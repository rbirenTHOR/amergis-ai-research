const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { parseHTML } = require('linkedom');

const root = path.resolve(__dirname, '../..');
const file = path.join(root, 'outputs/east-ramapo-pilot-plan.html');
const html = fs.readFileSync(file, 'utf8');
const pack = JSON.parse(fs.readFileSync(path.join(root, 'outputs/east-ramapo-pilot-plan.json'), 'utf8'));
const economics = JSON.parse(fs.readFileSync(path.join(__dirname, 'economics.json'), 'utf8'));
const { window } = parseHTML(html);
const document = window.document;
const context = vm.createContext({ window, document, console, URL, Intl, Number, Math });
const checks = [];
for (const script of document.querySelectorAll('script')) {
  if (!script.type || ['text/javascript', 'application/javascript'].includes(script.type)) {
    assert(!script.src, 'Report scripts must work without external runtime assets');
    vm.runInContext(script.textContent, context, { timeout: 5000 });
  }
}
function check(name, fn) { fn(); checks.push({ name, status: 'pass' }); }
function visible(selector) { return [...document.querySelectorAll(selector)].filter(el => !el.hidden); }
function setValue(el, value) {
  assert(el, 'Expected form control');
  Object.defineProperty(el, 'value', { value: String(value), writable: true, configurable: true });
}
function trigger(el, kind) { el.dispatchEvent(new window.Event(kind, { bubbles: true })); }
function approximately(actual, expected, label) {
  assert.equal(typeof actual, 'number', label);
  assert(Number.isFinite(actual), label);
  const tolerance = /fraction|ratio/.test(label) ? 0.00011 : 0.011;
  assert(Math.abs(actual - expected) <= tolerance, `${label}: got ${actual}, expected ${expected}`);
}

check('Unique IDs and structural links resolve', () => {
  const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
  assert.equal(new Set(ids).size, ids.length, 'Duplicate DOM IDs');
  for (const a of document.querySelectorAll('a[href]')) {
    const href = a.getAttribute('href');
    if (href.startsWith('#')) assert(document.getElementById(decodeURIComponent(href.slice(1))), href);
    else if (/^https?:\/\//.test(href)) assert(new URL(href).hostname, href);
    else if (/^mailto:/.test(href)) assert(href.slice(7), href);
    else assert(fs.existsSync(path.resolve(path.dirname(file), href)), href);
  }
  assert(!html.includes('[object Object]'), 'Unrendered object');
});

check('All requirement, capability and evidence records render', () => {
  assert.equal(document.querySelectorAll('.requirement').length, pack.counts.requirement_records);
  assert.equal(document.querySelectorAll('.product').length, pack.counts.capabilities);
  assert.equal(document.querySelectorAll('.source').length, pack.counts.source_records);
  for (const [group, key] of [['Bid', 'bid_requirements'], ['Workforce', 'workforce_requirements'], ['Insurance', 'insurance_requirements'], ['Privacy', 'privacy_requirements']]) {
    assert.equal(document.querySelectorAll(`.requirement[data-group="${group}"]`).length, pack.counts[key]);
  }
  const sourceIds = new Set(pack.sources.map(source => source.id));
  assert.equal(sourceIds.size, pack.sources.length, 'Duplicate evidence IDs');
  for (const source of pack.sources) assert(document.getElementById(`source-${source.id}`), source.id);
  function visit(value) {
    if (Array.isArray(value)) return value.forEach(visit);
    if (!value || typeof value !== 'object') return;
    for (const [key, child] of Object.entries(value)) {
      if (key === 'source_ids') for (const id of child) assert(sourceIds.has(id), `Unresolved evidence ${id}`);
      else visit(child);
    }
  }
  visit(pack.modules);
});

check('Scope, human accountability and unverified readiness remain visible', () => {
  const copy = document.body.cloneNode(true);
  for (const el of copy.querySelectorAll('script,style')) el.remove();
  const prose = copy.textContent;
  for (const pattern of [/RFP-ER-5-27/, /not bid.ready/i, /in.person/i, /TSHH|TSSLD/, /COI/, /notari[sz]/i, /human/i, /IEP/, /no confirmed therapists/i, /no confirmed insurance/i, /not.*(?:bid quote|quoted|quote)|illustrative|hypothetical/i]) {
    assert(pattern.test(prose), `Missing material scope/readiness text ${pattern}`);
  }
});

function testFilters(prefix, selector, attribute, count) {
  const query = document.getElementById(`${prefix}-query`);
  const select = document.getElementById(`${prefix}-${attribute === 'group' ? 'group' : 'priority'}`);
  const reset = document.getElementById(`${prefix}-reset`);
  const cards = [...document.querySelectorAll(selector)];
  assert(cards.length && query && select && reset);
  const value = cards[0].getAttribute(`data-${attribute}`);
  setValue(select, value); trigger(select, 'change');
  assert.equal(visible(selector).length, cards.filter(card => card.getAttribute(`data-${attribute}`) === value).length);
  assert(visible(selector).length > 0 && visible(selector).length < count, 'Category filter must narrow results');
  setValue(query, 'no-match-check-42911'); trigger(query, 'input');
  assert.equal(visible(selector).length, 0);
  setValue(query, ''); trigger(query, 'input');
  assert(visible(selector).length > 0);
  trigger(reset, 'click'); assert.equal(visible(selector).length, count);
}
check('Requirement search, group filter and reset', () => testFilters('requirement', '.requirement', 'group', pack.counts.requirement_records));
check('Product search, priority filter and reset', () => testFilters('product', '.product', 'priority', pack.counts.capabilities));

check('Calculator agrees with every stored scenario and clinician count', () => {
  assert.equal(typeof window.calculatePilot, 'function');
  assert.equal(JSON.stringify(window.pilotEconomics), JSON.stringify(pack.modules.economics));
  for (const scenario of economics.scenarios) {
    for (const expected of scenario.results) {
      const input = JSON.parse(JSON.stringify(scenario.inputs));
      const before = JSON.stringify(input);
      const actual = window.calculatePilot(input, expected.clinicians);
      assert.equal(JSON.stringify(input), before, 'Calculator must not mutate input');
      for (const [key, value] of Object.entries(expected)) {
        if (typeof value === 'number') approximately(actual[key], value, `${scenario.id}/${expected.clinicians}/${key}`);
      }
    }
  }
});

check('Calculator rejects unsupported and nonfinite assumptions', () => {
  const base = economics.scenarios[0].inputs;
  for (const n of [0, 4, 1.5, NaN, Infinity]) assert.throws(() => window.calculatePilot({ ...base }, n), undefined, `Invalid clinician count ${n}`);
  for (const [key, value] of [
    ['paid_hours', 0], ['paid_hours', -1], ['pay_rate', 0], ['bill_rate_equivalent', 0],
    ['billable_hour_equivalents', 0], ['billable_hour_equivalents', base.paid_hours + 1],
    ['pay_rate', NaN], ['pay_rate', Infinity], ['travel_per_clinician', -1],
    ['insurance_upfront_fraction', 1.1], ['admin_cash_fraction', 1.1],
    ['target_operating_margin', 1], ['invoice_cycle_days', 31]
  ]) assert.throws(() => window.calculatePilot({ ...base, [key]: value }, 1), undefined, `Invalid ${key}=${value}`);
});

check('Calculator form handles invalid values and restores a scenario', () => {
  const scenario = economics.scenarios[0];
  const select = document.getElementById('calc-scenario');
  const load = document.getElementById('calc-load');
  const clinicians = document.getElementById('calc-clinicians');
  const error = document.getElementById('calc-error');
  assert(select && load && clinicians && error);
  setValue(select, scenario.id); setValue(clinicians, 1); trigger(load, 'click');
  const pay = document.getElementById('calc-pay_rate');
  setValue(pay, -1); trigger(pay, 'input');
  assert(error.textContent.trim().length > 0 && !error.hidden, 'Invalid UI value needs visible explanation');
  setValue(select, scenario.id); trigger(load, 'click');
  assert(error.hidden || !error.textContent.trim(), 'Loading a valid scenario clears error');
  const expected = scenario.results.find(result => result.clinicians === 1);
  for (const key of ['revenue', 'operating_profit_before_tax_startup_and_financing', 'startup_funding_target']) {
    const el = document.querySelector(`[data-result="${key}"]`);
    assert(el, `Missing rendered ${key}`);
    const value = Number(el.textContent.replace(/[^0-9.\-]/g, ''));
    approximately(value, expected[key], `Rendered ${key}`);
  }
});

process.stdout.write(JSON.stringify({
  status: 'pass',
  method: 'Local in-memory DOM/source and calculator checks; not rendered-browser, vendor integration, live operation or procurement verification.',
  checks
}, null, 2) + '\n');
