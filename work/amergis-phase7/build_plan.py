"""Build a portable East Ramapo planning report from curated local JSON only."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/amergis-phase7'
OUT = ROOT / 'outputs'
NAMES = {'launch_core': 'launch-core', 'bid': 'bid-requirements', 'workforce': 'workforce', 'insurance': 'insurance', 'products': 'products', 'economics': 'economics'}
modules = {k: json.loads((WORK / (v + '.json')).read_text()) for k, v in NAMES.items()}
core, bid, workforce, insurance, products, economics = (modules[k] for k in NAMES)
review = json.loads((WORK / 'review.json').read_text()) if (WORK / 'review.json').exists() else {'status': 'Pending independent review'}
sources = [dict(s, module=k) for k, d in modules.items() for s in d.get('sources', [])]
source_map = {s['id']: s for s in sources}
assert len(source_map) == len(sources), 'Source IDs must be unique'
requirements = [(group, r) for group, rows in [('Bid', bid['requirements']), ('Workforce', workforce['requirements']), ('Insurance', insurance['requirements']), ('Privacy', core['privacy_requirements'])] for r in rows]
counts = {'requirement_records': len(requirements), 'bid_requirements': len(bid['requirements']), 'workforce_requirements': len(workforce['requirements']), 'insurance_requirements': len(insurance['requirements']), 'privacy_requirements': len(core['privacy_requirements']), 'forms': len(bid['form_checklist']), 'notarized_forms': sum(bool(r['notary']) for r in bid['form_checklist']), 'credential_checks': len(workforce['credential_matrix']), 'capabilities': len(products['capabilities']), 'agent_roles': len(products['agent_matrix']), 'source_records': len(sources), 'external_source_records': sum('url' in s for s in sources), 'prior_artifact_source_records': sum('artifact' in s for s in sources), 'unique_source_urls': len({s['url'] for s in sources if 'url' in s})}
pack = {'title': core['title'], 'as_of': core['as_of'], 'timezone': core['timezone'], 'status': core['status'], 'modules': modules, 'sources': sources, 'counts': counts, 'independent_review': review, 'report_notes': {'classification': 'Research, proposed operating design and illustrative economics; not a submitted bid or established service.', 'source_hierarchy': 'External primary evidence supports requirements. Earlier local artifacts are proposed designs with explicit provenance. Model inputs are analyst estimates or quote-required allowances.', 'verification_scope': 'Local source/DOM/filter and arithmetic checks, not rendered-browser review or live operational testing.'}}
OUT.mkdir(exist_ok=True)
(OUT / 'east-ramapo-pilot-plan.json').write_text(json.dumps(pack, ensure_ascii=False, indent=2) + '\n')


def esc(value):
    return html.escape(str(value))


def label(value):
    return str(value).replace('_', ' ')


def refs(ids):
    for i in ids:
        assert i in source_map, 'Unresolved source: ' + i
    return '<span class="refs">' + ' · '.join('<a href="#source-' + esc(i) + '">' + esc(i) + '</a>' for i in ids) + '</span>'


def render(value, key=''):
    if key == 'source_ids':
        return refs(value)
    if isinstance(value, dict):
        return '<dl>' + ''.join('<dt>' + esc(label(k)) + '</dt><dd>' + render(v, k) + '</dd>' for k, v in value.items()) + '</dl>'
    if isinstance(value, list):
        return '<ul>' + ''.join('<li>' + render(v) + '</li>' for v in value) + '</ul>'
    if value is None:
        return '<span class="muted">Not established / unpriced</span>'
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    return esc(value)


def fields(value, omit=()):
    return render({k: v for k, v in value.items() if k not in omit})


def details(title, body, css='', attrs=''):
    return '<details class="' + esc(css) + '" ' + attrs + '><summary>' + title + '</summary><div class="inside">' + body + '</div></details>'


def table(head, rows, css=''):
    return '<div class="table-wrap ' + esc(css) + '"><table><thead><tr>' + ''.join('<th>' + esc(h) + '</th>' for h in head) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + cell + '</td>' for cell in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def dollars(x):
    return '${:,.2f}'.format(x)


def card(title, text):
    return '<article class="card"><span class="eyebrow">' + esc(title) + '</span><p>' + text + '</p></article>'


def options(vals):
    return ''.join('<option value="' + esc(v) + '">' + esc(label(v)) + '</option>' for v in vals)


def filterbar(prefix, choices, select_label):
    return '<div class="filters"><label>Search<input id="' + prefix + '-query" type="search" placeholder="Search evidence, actions or responsibilities"></label><label>' + esc(select_label) + '<select id="' + prefix + '-' + ('group' if prefix == 'requirement' else 'priority') + '"><option value="">All</option>' + options(choices) + '</select></label><button id="' + prefix + '-reset" type="button">Reset</button></div><p id="' + prefix + '-count" class="muted" role="status"></p>'


# A decision-ready digest precedes the detailed evidence.
intro = '<p class="lead">Build a small, human-delivered school SLP service with a controlled administrative stack. Start with one experienced in-person SLP and a separately qualified backup; increase capacity only after funded assignments and actual economics are established.</p>'
intro += '<div class="callout warning"><b>Current bid readiness: not ready.</b><p>The operator is starting a new company, with no confirmed therapists or insurance. This pack specifies what to establish; it does not represent completed hiring, coverage, eligibility or a submitted proposal.</p></div>'
intro += '<div class="grid">' + card('Before the bid', 'Real clinician participation and evidence; bidder identity; actual insurance evidence; viable fees; complete signatures and notarizations.') + card('Before first service', 'Executed agreement, funded assignment, district clearance, live payroll and coverage, approved records access and tested administrative handoffs.') + card('After observed delivery', 'Review the first 30 service days and first collected invoice. Validate coverage, quality, cost and cash before adding clinicians or custom software.') + '</div>'
intro += fields(core['charter'])
for key in ['company_baseline', 'launch_recommendation', 'new_company_implication', 'current_decision']:
    if key in core:
        intro += '<h3>' + esc(label(key)) + '</h3>' + render(core[key])
if 'capital_release_sequence' in core:
    intro += '<h3>Release capital in stages</h3>' + table(['Stage', 'Spending rule'], [[esc(r['stage']), esc(r['rule'])] for r in core['capital_release_sequence']])
intro += '<h3>Evidence gates</h3>' + table(['Gate', 'Stage', 'Readiness', 'Proof needed'], [[esc(r['gate']), esc(r['stage']), '<span class="tag warning">' + esc(r['status']) + '</span>', esc(r['proof'])] for r in core['readiness']])
intro += '<h3>Company inputs still needed</h3>' + render(core['open_company_inputs'])

calendar = '<p>Public procurement dates below are Eastern Daylight Time on the October 20, 2026 snapshot. Internal targets are proposed management dates. Recheck the current district packet and BidNet addenda before action.</p>'
p = bid['procurement']
calendar += '<div class="grid">' + card('Questions due', '<b>October 27, 2026 · noon EDT</b><br>Written questions through the purchasing contact. Drafts remain unsent.' + refs(p['source_ids'])) + card('Proposal due', '<b>October 30, 2026 · noon EDT</b><br>Electronic submission via Empire State Purchasing Group / BidNet Direct. No portal account or submission established.' + refs(p['source_ids'])) + '</div>'
calendar += table(['When / type', 'Deliverable and owner', 'Dependency / exit'], [[esc(r['when']) + '<br><span class="tag">' + esc(r['type']) + '</span>', '<b>' + esc(r['owner']) + '</b><p>' + esc(r['deliverable']) + '</p>', '<p>' + esc(r['dependency']) + '</p><p>' + esc(r['exit']) + '</p>'] for r in core['critical_path']])
calendar += details('Complete procurement terms and unresolved wording', render(p))

bid_html = '<p>' + esc(bid['readiness_note']) + '</p><div class="callout"><b>Nine listed form/document items; three require notarization.</b><p>The insurance certification needs both representative and bidder signatures, with a COI at bid. A quotation is not the requested certificate. Named clinician résumés and references belong in the proposal.</p>' + refs(['EBS02', 'EBS03']) + '</div>'
bid_html += table(['Form / PDF page', 'Signer(s)', 'Notary', 'Evidence / completion rule'], [[esc(r['document']) + '<br><small>p. ' + esc(r['page']) + '</small>', '<br>'.join(esc(s) for s in r['signers']), '<b>' + ('Yes' if r['notary'] else 'No') + '</b>', esc(r['requirement']) + refs(r['source_ids'])] for r in bid['form_checklist']])
bid_html += '<h3>Proposal assembly</h3>' + table(['Order', 'Section', 'Content'], [[str(r['order']), esc(r['section']), esc(r['content']) + refs(r['source_ids'])] for r in bid['proposal_sequence']])
bid_html += details('Eligibility and responsibility evidence', render(bid['eligibility']))
bid_html += details('Proposed fee schedule: units and amounts still to confirm', '<p>' + esc(bid['price_schedule_note']) + '</p>' + render(bid['price_line_items']))
bid_html += details('Bid preparation checklist and research limits', render(bid['procedural_checklist']) + render(bid['research_limits']))

workforce_html = '<p class="lead">' + esc(workforce['scope']) + '</p><p class="muted">' + esc(workforce['status']) + '</p>'
workforce_html += '<div class="grid">' + ''.join(card(r['role'], '<b>' + esc(r.get('proposed_count', 'Named owner')) + '</b><p>' + esc(r['job']) + '</p>' + details('Role and selection evidence', fields(r, ('role', 'job')))) for r in workforce['role_cards']) + '</div>'
workforce_html += '<h3>Credential and clearance matrix</h3>' + table(['Evidence', 'Verification', 'Cadence / basis'], [[ '<b>' + esc(r['item']) + '</b><p>' + esc(r['evidence']) + '</p>', esc(r['verification']), esc(r['cadence']) + '<p class="muted">' + esc(r['basis']) + '</p>' + refs(r['source_ids'])] for r in workforce['credential_matrix']])
workforce_html += details('Recruiting plan and practical screening rubric', render(workforce['recruiting_plan']))
workforce_html += details('Onboarding, backup coverage and employer decisions', '<h4>Onboarding</h4>' + render(workforce['onboarding_sequence']) + '<h4>Backup protocol</h4>' + render(workforce['backup_protocol']) + '<h4>Employer decisions</h4>' + render(workforce['employer_decisions_before_offer']))
workforce_html += details('Planning assumptions, unresolved evidence and operating checks', render(workforce['planning_assumptions']) + render(workforce['open_evidence']) + render(workforce['operating_checks']) + '<p>' + esc(workforce['operating_checks_note']) + '</p>')

insurance_html = '<p class="lead">' + esc(insurance['decision']) + '</p><p>No insurer has priced or bound this new company’s coverage. Exact legal names, payroll, activities and claims history must be supplied truthfully.</p>'
insurance_html += table(['Coverage / clause', 'Requirement', 'Evidence status and action'], [[ '<b>' + esc(r['topic']) + '</b><br><span class="tag">' + esc(r['status']) + '</span>', esc(r['requirement']) + '<p class="muted">' + esc(r['locator']) + '</p>' + refs(r['source_ids']), esc(r['pilot_action'])] for r in insurance['requirements']])
insurance_html += '<h3>New York proof of coverage</h3>' + render(insurance['wcb_evidence_schedule'])
insurance_html += details('Coverage gaps and operating controls', render(insurance['coverage_gap_matrix']) + render(insurance['operating_controls']))
insurance_html += details('Premium, cash and evidence limits', render(insurance['insurance_budget']) + render(insurance['evidence_limits']))

# Cost calculator retains full model disclosure and all editable assumptions.
base = economics['scenarios'][0]
cost_html = '<p class="lead">' + esc(economics['summary']) + '</p><div class="callout warning"><b>Illustrative model — not a bid, quote or earnings forecast.</b><p>All local pay, fee units, premium, software and setup inputs need validation. The district’s 30-day invoice rule is a submission deadline, not a promise to pay in 30 days. Revenue hour-equivalents are an analytical denominator, not verified contract billing units.</p></div>'
cost_html += '<h3>Base scenario at one to three clinicians</h3>' + table(['Active clinicians', 'Monthly revenue', 'Monthly operating profit¹', 'Operating margin', 'One-time setup', 'Total funding target²'], [[str(r['clinicians']), dollars(r['revenue']), dollars(r['operating_profit_before_tax_startup_and_financing']), '{:.2%}'.format(r['operating_margin_fraction']), dollars(r['setup_cost']), dollars(r['startup_funding_target'])] for r in base['results']])
cost_html += '<p class="muted">¹ Normalized service month, after the modeled human operator cost; before tax, startup recovery and financing. ² Setup + prepaid insurance + modeled no-collection operating reserve + contingency, not an additional expense or a guaranteed cash requirement. Do not annualize a school service month by multiplying by 12.</p>'
cost_html += '<div class="callout warning"><b>Additional required coverage reserve remains unpriced.</b><p>Every funding target below excludes the required two-year post-work professional E&amp;O continuation / closure reserve. The annual insurance input covers the first year only; the 10% contingency does not fund that separate obligation. Add the broker-quoted and buyer-accepted solution before approving funding or a bid price.</p>' + render(economics.get('unpriced_required_cash', [])) + '</div>'
cost_html += '<div class="calculator"><h3>Explore the assumptions</h3><p>Changes stay in this browser page and are not saved or transmitted. Fractions are decimal inputs: 0.20 means 20%.</p><div class="filters"><label>Scenario<select id="calc-scenario">' + ''.join('<option value="' + esc(s['id']) + '">' + esc(s['label']) + '</option>' for s in economics['scenarios']) + '</select></label><button id="calc-load" type="button">Load scenario</button><label>Active primary clinicians<input id="calc-clinicians" type="number" min="1" max="3" step="1" value="1"></label></div>'
main_keys = ['paid_hours', 'billable_hour_equivalents', 'pay_rate', 'bill_rate_equivalent', 'employer_burden_fraction', 'backup_allowance_fraction']
def input_field(d):
    k = d['key']
    return '<label class="input-field">' + esc(label(k)) + '<input type="number" id="calc-' + esc(k) + '" data-input="' + esc(k) + '" value="' + str(base['inputs'][k]) + '" min="0" step="any"><small>' + esc(d['unit']) + ' · ' + esc(label(d['provenance_kind'])) + '</small><details><summary>Input basis</summary><p>' + esc(d['note']) + '</p></details></label>'
cost_html += '<div class="input-grid">' + ''.join(input_field(d) for d in economics['input_definitions'] if d['key'] in main_keys) + '</div>'
cost_html += details('Edit overhead, setup, insurance and cash timing assumptions', '<div class="input-grid">' + ''.join(input_field(d) for d in economics['input_definitions'] if d['key'] not in main_keys) + '</div>')
cost_html += '<p id="calc-error" class="error" role="alert" hidden></p><div id="calc-results" aria-live="polite"><div class="result-grid">'
output_cards = [('revenue', 'Monthly revenue'), ('operating_profit_before_tax_startup_and_financing', 'Monthly operating profit¹'), ('operating_margin_fraction', 'Operating margin'), ('break_even_rate_equivalent', 'Break-even rate equivalent'), ('rate_equivalent_for_target_margin', 'Rate equivalent for target margin'), ('startup_funding_target', 'Total funding target²')]
for key, title in output_cards:
    cost_html += '<article class="result-card"><span>' + esc(title) + '</span><b data-result="' + key + '"></b></article>'
cost_html += '</div><p class="muted"><b>Funding exclusions:</b> The displayed target excludes unpriced two-year post-work professional E&amp;O continuation / closure coverage. Add that separate required reserve when quoted.</p><p id="calc-warning" class="warning-text"></p><h4>Cost and cash bridge</h4>'
cost_html += table(['Component', 'Value', 'Treatment'], [[esc(title), '<b data-result="' + key + '"></b>', esc(note)] for key, title, note in [('total_operating_cost', 'Monthly total operating cost', 'Direct delivery and shared overhead; excludes startup recovery, tax and financing.'), ('direct_delivery_cost', 'Monthly direct delivery cost', 'Loaded clinician payroll, backup allowance and per-clinician travel/tools/maintenance.'), ('shared_overhead', 'Monthly shared overhead', 'Insurance allocation, full human operator cost and shared tools.'), ('setup_cost', 'One-time setup', 'Entity/legal, configured tools, bid preparation, recruitment and hardware.'), ('insurance_upfront_cash', 'Prepaid insurance cash', 'Actual cash timing must come from the insurer; monthly allocation stays in profit.'), ('monthly_cash_outflow', 'Monthly operating cash outflow', 'Excludes already prepaid insurance; retains the selected human admin cash payment.'), ('days_to_first_cash_assumption', 'Days to first collection assumption', 'Invoice close + submission lag + approval delay + collection delay.'), ('funding_days', 'Days of funded operation', 'First-collection assumption plus extra cash cushion.'), ('working_capital_cash_reserve', 'Working-capital cash reserve', 'Outflows during modeled funding days; no receivable offsets.'), ('cash_contingency', 'Additional cash contingency', 'Applied to setup, prepaid premium and working-capital reserve.')]])
cost_html += '</div></div>'
cost_html += '<h3>Configuration cost basis</h3>' + render(economics.get('setup_labor_basis', {}))
cost_html += details('All scenario results and sensitivity', render(economics['scenarios']) + render(economics['sensitivity']))
cost_html += details('Verified pay context, model limits and pricing-release gates', render(economics['verified_pay_context']) + render(economics['local_pay_evidence_gap']) + render(economics['scope']) + render(economics['interpretation']) + render(economics['pricing_release_gates']))
cost_html += details('Formulas and validation rules', render(economics['formulas']) + render(economics['input_validation']))

product_html = '<p class="lead">' + esc(products['recommendation']) + '</p><p class="muted">' + esc(products['evidence_boundary']) + '</p>'
product_html += '<div class="grid">' + card('Configure', 'One secure operations workspace with controlled views, evidence, assignments and approvals. Reuse established services for payroll, accounting and signatures.') + card('Use the district’s systems', 'District-approved clinical, attendance and invoice routes stay authoritative. No district software product or API access is established.') + card('Build later, when justified', 'Only bounded reminders, exception detection and reconciliation after manual controls work. No custom ATS or native app on the bid critical path.') + '</div>'
product_html += '<p>' + esc(products['budget_and_effort_note']) + '</p>'
product_html += filterbar('product', sorted({r['priority'] for r in products['capabilities']}), 'Delivery stage')
for r in products['capabilities']:
    product_html += details('<span class="id">' + esc(r['id']) + '</span>' + esc(r['name']) + ' <span class="tag">' + esc(label(r['decision'])) + ' · ' + esc(label(r['priority'])) + '</span>', '<p>' + esc(r['purpose']) + '</p>' + fields(r, ('id', 'name', 'decision', 'priority', 'purpose')), 'product', 'id="product-' + r['id'] + '" data-priority="' + esc(r['priority']) + '"')
product_html += details('Operating stack and record ownership', render(products['operating_stack']) + render(products['scope']))
product_html += '<h3>Delivery backlog</h3>' + render(products['delivery_backlog'])
product_html += details('Integration evidence, proposed acceptance checks and open decisions', render(products['integration_register']) + render(products['launch_acceptance_checks']) + render(products['open_decisions']))

agents_html = '<p>Agents can prepare evidence, detect administrative exceptions and draft actions within approved access. People remain responsible for employment decisions, credentials, coverage, clinical care, IEP decisions, commercial commitments and money release.</p>'
for r in products['agent_matrix']:
    agents_html += details('<span class="id">' + esc(r['id']) + '</span>' + esc(r['name']), fields(r, ('id', 'name')), 'agent')
agents_html += '<h3>Workforce authority boundary</h3>' + table(['Function', 'Agent may assist', 'Human accountable'], [[esc(r['function']), esc(r['agent_can']), esc(r['human_must'])] for r in workforce['human_agent_boundary']])

operate_html = '<p>Preserve separate records for the authorized service, scheduled work, delivered or missed service, actual worked time and approved billable quantity. No agent should create clinical evidence or bill a missing service.</p>'
operate_html += table(['Cadence', 'Control', 'AI role'], [[esc(r['frequency']), esc(r['control']), esc(r['ai_role'])] for r in core['operating_cadence']])
operate_html += '<h3>Privacy and approved data flow</h3>' + render(core['privacy_requirements'])
operate_html += '<h3>Proposed pilot success measures</h3>' + table(['Measure', 'Target', 'Evidence'], [[esc(r['metric']), esc(r['target']), esc(r['measurement'])] for r in core['proposed_success_measures']])

requirement_html = '<p>This matrix combines procurement, workforce, insurance and privacy records. A requirement supported by a source is not a fulfilled company obligation. Some records overlap across disciplines of review; the count is not a count of unique legal duties.</p>' + filterbar('requirement', ['Bid', 'Workforce', 'Insurance', 'Privacy'], 'Workstream')
for group, r in requirements:
    title = r.get('title', r.get('topic', r.get('category', r.get('requirement', r['id']))))
    requirement_html += details('<span class="id">' + esc(r['id']) + '</span>' + esc(title) + ' <span class="tag">' + group + '</span>', fields(r, ('id',)), 'requirement', 'id="requirement-' + r['id'] + '" data-group="' + group + '"')

drafts_html = '<div class="callout"><b>Ready to review, not sent.</b><p>The following are internal drafts. Company particulars and recipient authority need completion. This report has not contacted the district, candidates, references or brokers, and has not bound coverage.</p></div>'
drafts_html += '<h3>Broker RFQ brief</h3>' + render(insurance['broker_rfq_brief'])
drafts_html += '<h3>Purchasing clarification questions</h3><p>Consolidate overlapping questions into one approved message before the October 27 deadline.</p>' + render(bid['questions_draft'])
drafts_html += details('Additional insurance clarification questions', render(insurance['buyer_clarification_questions']))

prior_artifact_map = {'work/amergis-phase4/portfolio.json': 'amergis-product-roadmap.json', 'work/amergis-phase5/domain-spec.json': 'school-therapy-requirements.json', 'work/amergis-phase5/obligations.json': 'school-therapy-requirements.json', 'work/amergis-phase5/integrations.json': 'school-therapy-requirements.json'}
sources_html = '<p><b>' + str(counts['source_records']) + ' source records</b>: ' + str(counts['external_source_records']) + ' external records spanning ' + str(counts['unique_source_urls']) + ' unique URLs, and ' + str(counts['prior_artifact_source_records']) + ' earlier local design references. Shared URLs appear in multiple workstreams. Earlier designs establish provenance, not observed district platforms or completed software.</p>'
for s in sources:
    if 'url' in s:
        link = '<a href="' + esc(s['url']) + '" target="_blank" rel="noopener">Open external source ↗</a>'
    else:
        assert s['artifact'] in prior_artifact_map, s
        link = '<a href="' + prior_artifact_map[s['artifact']] + '">Open earlier packaged design JSON</a><p class="muted">Exact curated input provenance: ' + esc(s['artifact']) + '</p>'
    sources_html += details('<span class="id">' + s['id'] + '</span>' + esc(s['title']), '<p>' + link + '</p>' + fields(s, ('id', 'title', 'url')), 'source', 'id="source-' + s['id'] + '"')
method_html = '<p>' + esc(core['actions_performed']) + '</p><p>All readiness status is evidence-based and remains subject to actual company documents, named clinicians, insurer evidence, district acceptance and final human release. Research does not establish operational compliance.</p><h3>Independent review</h3>' + render(review) + '<p class="muted">Report checks use a local in-memory DOM and arithmetic fixtures. They do not establish rendered-browser layout, a working business service, actual staffing availability, legal eligibility, insured coverage or live integration behavior.</p>'

sections = [('pilot', 'Pilot decision and readiness', intro), ('calendar', 'Critical path and procurement dates', calendar), ('bid', 'Bid package', bid_html), ('therapists', 'Therapists and credentials', workforce_html), ('insurance', 'Insurance and coverage gaps', insurance_html), ('costs', 'Costs and cash calculator', cost_html), ('products', 'Digital products to establish', product_html), ('agents', 'AI agents and human authority', agents_html), ('operations', 'Daily operation and data', operate_html), ('requirements', 'Explore all requirements', requirement_html), ('drafts', 'Unsent RFQ and questions', drafts_html), ('sources', 'Evidence register', sources_html), ('review', 'Method and independent review', method_html)]
nav = ''.join('<a href="#' + i + '">' + esc(t) + '</a>' for i, t, _ in sections)
body = ''.join('<section id="' + i + '"><div class="section-head"><span>' + str(n + 1).zfill(2) + '</span><h2>' + esc(t) + '</h2></div>' + content + '</section>' for n, (i, t, content) in enumerate(sections))

CSS = '''
:root{--ink:#142d38;--muted:#566b77;--bg:#f2f5f5;--line:#d6e0e3;--accent:#006a64;--soft:#e6f3ee;--warn:#80500e;--warnbg:#fff2d9}*{box-sizing:border-box}body{margin:0;background:var(--bg);font:16px/1.6 system-ui,-apple-system,sans-serif;color:var(--ink)}a{color:var(--accent);text-underline-offset:3px}a,dd,td{overflow-wrap:anywhere}header{background:#103b47;color:white;padding:54px max(24px,calc((100vw - 1200px)/2))}header h1{font-size:clamp(34px,4.4vw,60px);line-height:1.1;letter-spacing:-1.9px;max-width:960px;margin:18px 0 24px}header p{max-width:900px;color:#d9e9e9}header a{color:#bff0dd}.eyebrow{text-transform:uppercase;letter-spacing:1.5px;font-size:11px;font-weight:750}.stats{display:flex;gap:30px;flex-wrap:wrap;margin:26px 0}.stats b{display:block;font-size:27px}.stats span{font-size:12px;color:#bad6db}.layout{display:grid;grid-template-columns:225px minmax(0,1fr);gap:30px;max-width:1380px;margin:auto;padding:30px 26px}nav{position:sticky;top:16px;align-self:start;max-height:calc(100vh - 32px);overflow:auto}nav a{display:block;font-size:12px;text-decoration:none;padding:9px;border-left:2px solid var(--line)}nav a:hover{background:var(--soft);border-color:var(--accent)}main{min-width:0}section{margin-bottom:50px;scroll-margin-top:20px}.section-head{display:flex;gap:14px;align-items:center}.section-head>span{font-size:12px;color:var(--accent);font-weight:750}h2{font-size:27px;line-height:1.25;letter-spacing:-.6px}h3{font-size:20px;margin:26px 0 12px}h4{margin:18px 0 8px}.lead{font-size:20px;line-height:1.65}p{margin:11px 0}.callout{border-left:4px solid var(--accent);background:var(--soft);padding:20px 24px;margin:22px 0;border-radius:0 10px 10px 0}.warning{background:var(--warnbg);color:var(--warn);border-color:#c38c31}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}.card{padding:20px;border:1px solid var(--line);border-radius:12px;background:white;margin:12px 0}.card>p{font-size:14px}.table-wrap{overflow-x:auto;background:white;border:1px solid var(--line);border-radius:10px;margin:18px 0}table{width:100%;border-collapse:collapse;min-width:630px}td,th{text-align:left;padding:14px 16px;vertical-align:top;border-bottom:1px solid var(--line)}td{font-size:14px}th{background:#e8eff0;font-size:11px;text-transform:uppercase;letter-spacing:.7px}tr:last-child td{border:0}details{background:white;border:1px solid var(--line);border-radius:9px;margin:11px 0}summary{padding:16px 20px;font-size:14px;font-weight:650;cursor:pointer}summary:hover{background:#edf5f3}.inside{padding:2px 22px 22px}.id{font-size:10px;color:var(--muted);margin-right:8px}.tag{display:inline-block;border:1px solid var(--line);border-radius:18px;padding:2px 9px;font-size:10px;font-weight:550;margin:4px 0;background:#f2f5f5}.refs{display:block;font-size:11px;margin:8px 0}.muted,small{font-size:12px;color:var(--muted)}dl{margin:10px 0}dt{font-size:11px;text-transform:uppercase;letter-spacing:.5px;font-weight:750;color:var(--muted);margin-top:16px}dd{font-size:14px;margin:4px 0 0}ul{padding-left:21px}li{margin:8px 0}.filters{display:flex;align-items:end;gap:12px;flex-wrap:wrap}.filters label{flex:1;min-width:150px;font-size:12px;font-weight:650}.filters label:first-child{flex:2}input,select,button{font:inherit;color:var(--ink);font-size:14px;border:1px solid #a7bec5;border-radius:6px;padding:11px;background:white}input,select{display:block;width:100%;margin-top:6px}button{cursor:pointer}.calculator{border:1px solid #b8d8d0;background:#eaf4f1;padding:24px;border-radius:12px;margin:28px 0}.calculator h3{margin-top:0}.input-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:18px;margin:20px 0}.input-field{font-size:12px;font-weight:650}.input-field small{display:block;font-weight:450;line-height:1.4;margin-top:5px}.input-field details{margin:6px 0}.input-field summary{font-size:11px;padding:7px 9px;font-weight:500}.input-field details p{font-size:12px;font-weight:400;padding:5px 10px}.result-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:20px 0}.result-card{padding:18px;background:#123e46;color:white;border-radius:9px}.result-card span{font-size:11px;display:block;color:#c0d9dd}.result-card b{font-size:26px;display:block;margin-top:7px}.warning-text{font-weight:650;color:var(--warn)}.error{padding:14px;background:#ffe3df;color:#8b2420;border:1px solid #dfaaa4;border-radius:7px}[hidden]{display:none!important}footer{text-align:center;padding:30px;font-size:12px;color:var(--muted)}@media(max-width:850px){.layout{display:block;padding:20px}nav{position:static;display:flex;gap:7px;overflow-x:auto;max-height:none;margin-bottom:25px}nav a{white-space:nowrap;border-left:0;border-bottom:2px solid var(--line)}header{padding:34px 23px}.calculator{padding:18px}}@media print{nav,.filters,.calculator .input-grid{display:none}.layout{display:block}header{background:white;color:var(--ink);padding:10px}header p,header a,.stats span{color:var(--ink)}section{margin-bottom:28px}details{break-inside:avoid}.table-wrap{overflow:visible}table{min-width:0}}
'''
SCRIPT = r'''
(function(){
function connectFilter(prefix,cls,attr,suffix){const q=document.getElementById(prefix+'-query'),s=document.getElementById(prefix+'-'+suffix),rows=[...document.querySelectorAll('.'+cls)];function filter(){let n=0;for(const r of rows){r.hidden=!!((s.value&&r.dataset[attr]!==s.value)||((q.value||'').trim()&&!r.textContent.toLowerCase().includes(q.value.trim().toLowerCase())));if(!r.hidden)n++;}document.getElementById(prefix+'-count').textContent=n+' of '+rows.length+' records shown';}q.addEventListener('input',filter);s.addEventListener('change',filter);document.getElementById(prefix+'-reset').addEventListener('click',()=>{q.value='';s.value='';filter();});filter();}
connectFilter('requirement','requirement','group','group');connectFilter('product','product','priority','priority');
document.addEventListener('click',event=>{const a=event.target.closest('a[href^="#"]');if(!a)return;const target=document.getElementById(a.getAttribute('href').slice(1));if(target&&target.tagName==='DETAILS'){target.hidden=false;target.open=true;}});
const data=JSON.parse(document.getElementById('economics-data').textContent);window.pilotEconomics=data;
function round(v,places=2){return Number(v.toFixed(places));}
function validate(i,n){if(!Number.isInteger(n)||n<1||n>3)throw Error('Active clinicians must be a whole number from 1 to 3.');for(const d of data.input_definitions){if(typeof i[d.key]!=='number'||!Number.isFinite(i[d.key])||i[d.key]<0)throw Error(d.key.replaceAll('_',' ')+' must be a finite, non-negative number.');}for(const k of ['paid_hours','pay_rate','bill_rate_equivalent','billable_hour_equivalents'])if(i[k]<=0)throw Error(k.replaceAll('_',' ')+' must be greater than zero.');for(const k of Object.keys(data.input_validation.fractions)){if(i[k]>1||(k==='target_operating_margin'&&i[k]>=1))throw Error(k.replaceAll('_',' ')+' must be within its valid fraction range.');}if(i.billable_hour_equivalents>i.paid_hours)throw Error('Revenue hour-equivalents cannot exceed paid hours in this bounded model.');if(i.invoice_cycle_days+i.invoice_submission_lag_days>30)throw Error('Invoice cycle plus submission lag must be no more than 30 days.');}
function raw(i,n){let r={clinicians:n};r.paid_hours_total=n*i.paid_hours;r.billable_hour_equivalents_total=n*i.billable_hour_equivalents;r.billable_to_paid_ratio=i.billable_hour_equivalents/i.paid_hours;r.revenue=r.billable_hour_equivalents_total*i.bill_rate_equivalent;r.gross_pay=r.paid_hours_total*i.pay_rate;r.employer_burden=r.gross_pay*i.employer_burden_fraction;r.loaded_pay=r.gross_pay+r.employer_burden;r.backup_allowance=r.loaded_pay*i.backup_allowance_fraction;r.travel=n*i.travel_per_clinician;r.software_seats=n*i.software_seat_per_clinician;r.credential_maintenance=n*i.credential_maintenance_per_clinician;r.direct_delivery_cost=r.loaded_pay+r.backup_allowance+r.travel+r.software_seats+r.credential_maintenance;r.contribution_before_shared_overhead=r.revenue-r.direct_delivery_cost;r.annual_insurance=i.annual_insurance_first+(n-1)*i.annual_insurance_additional;r.insurance_monthly_allocation=r.annual_insurance/12;r.human_admin_hours=i.admin_hours_first+(n-1)*i.admin_hours_additional;r.human_admin_cost=r.human_admin_hours*i.admin_loaded_rate;r.shared_overhead=r.insurance_monthly_allocation+r.human_admin_cost+i.shared_software_monthly;r.total_operating_cost=r.direct_delivery_cost+r.shared_overhead;r.operating_profit_before_tax_startup_and_financing=r.revenue-r.total_operating_cost;r.operating_margin_fraction=r.operating_profit_before_tax_startup_and_financing/r.revenue;r.break_even_rate_equivalent=r.total_operating_cost/r.billable_hour_equivalents_total;r.rate_equivalent_for_target_margin=r.total_operating_cost/(r.billable_hour_equivalents_total*(1-i.target_operating_margin));r.break_even_billable_to_paid_ratio=r.total_operating_cost/(r.paid_hours_total*i.bill_rate_equivalent);r.max_pay_rate_for_target_margin=(r.revenue*(1-i.target_operating_margin)-(r.travel+r.software_seats+r.credential_maintenance+r.shared_overhead))/(r.paid_hours_total*(1+i.employer_burden_fraction)*(1+i.backup_allowance_fraction));r.setup_cost=i.entity_legal_setup+i.technology_configuration_setup+i.bid_preparation_hours*i.admin_loaded_rate+i.backup_recruit_clearance_setup+n*(i.recruit_clearance_setup_per_clinician+i.hardware_setup_per_clinician);r.insurance_upfront_cash=r.annual_insurance*i.insurance_upfront_fraction;r.insurance_monthly_cash_remaining=r.annual_insurance*(1-i.insurance_upfront_fraction)/12;r.monthly_cash_outflow=r.direct_delivery_cost+i.shared_software_monthly+r.human_admin_cost*i.admin_cash_fraction+r.insurance_monthly_cash_remaining;r.days_to_first_cash_assumption=i.invoice_cycle_days+i.invoice_submission_lag_days+i.approval_delay_days+i.payment_after_approval_days;r.funding_days=r.days_to_first_cash_assumption+i.extra_cash_cushion_days;r.working_capital_cash_reserve=r.monthly_cash_outflow*r.funding_days/30;let subtotal=r.setup_cost+r.insurance_upfront_cash+r.working_capital_cash_reserve;r.cash_contingency=subtotal*i.cash_contingency_fraction;r.startup_funding_target=subtotal+r.cash_contingency;r.operating_profit_per_clinician=r.operating_profit_before_tax_startup_and_financing/n;return r;}
window.calculatePilot=function(i,n){validate(i,n);let r=raw(i,n);for(const k of Object.keys(r))r[k]=round(r[k],['billable_to_paid_ratio','operating_margin_fraction','break_even_billable_to_paid_ratio'].includes(k)?4:2);const prev=n>1?raw(i,n-1):null;r.incremental_funding_vs_previous_scale=round(r.startup_funding_target-(prev?round(prev.startup_funding_target):0));r.incremental_monthly_profit_vs_previous_scale=round(r.operating_profit_before_tax_startup_and_financing-(prev?round(prev.operating_profit_before_tax_startup_and_financing):0));for(const v of Object.values(r))if(!Number.isFinite(v))throw Error('Inputs are too large for a finite result.');return r;};
const usd=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:2,maximumFractionDigits:2});
function update(){const error=document.getElementById('calc-error'),results=document.getElementById('calc-results');try{let i={};for(const d of data.input_definitions){const val=document.getElementById('calc-'+d.key).value;if(val.trim()==='')throw Error(d.key.replaceAll('_',' ')+' is required.');i[d.key]=Number(val);}const nRaw=document.getElementById('calc-clinicians').value;if(!nRaw.trim())throw Error('Active clinicians is required.');const r=window.calculatePilot(i,Number(nRaw));for(const el of document.querySelectorAll('[data-result]')){const k=el.dataset.result;el.textContent=k==='operating_margin_fraction'?(r[k]*100).toFixed(2)+'%':k.includes('days')?r[k].toFixed(0)+' days':usd.format(r[k]);}error.hidden=true;error.textContent='';results.hidden=false;document.getElementById('calc-warning').textContent=r.break_even_billable_to_paid_ratio>1?'At this assumed rate and cost, break-even requires more than 100% of paid time to convert to revenue. Reprice or change the authorized scope; do not alter clinical services to hit utilization.':r.operating_margin_fraction<i.target_operating_margin?'This scenario is below the selected operating-margin target, before startup recovery and financing.':'This scenario meets the selected operating-margin target on assumptions only. Validate actual scope, pay, costs and collections.';}catch(e){error.hidden=false;error.textContent=e.message;results.hidden=true;}}
function loadScenario(){const selected=data.scenarios.find(s=>s.id===document.getElementById('calc-scenario').value)||data.scenarios[0];for(const d of data.input_definitions)document.getElementById('calc-'+d.key).value=String(selected.inputs[d.key]);update();}
for(const el of document.querySelectorAll('[data-input],#calc-clinicians'))el.addEventListener('input',update);document.getElementById('calc-load').addEventListener('click',loadScenario);update();
})();
'''
embedded = json.dumps(economics, ensure_ascii=False).replace('<', '\\u003c')
header = '<header><span class="eyebrow">Independent school staffing company · Phase 07 · 20 October 2026</span><h1>East Ramapo:<br>from a new company to a controlled pilot.</h1><p>One experienced school SLP, a qualified backup and a lean operating stack. Establish real people, coverage and commercial evidence before an October 30 bid or any student service.</p><div class="stats"><div><b>1 + backup</b><span>proposed initial staffing</span></div><div><b>' + str(counts['forms']) + ' / ' + str(counts['notarized_forms']) + '</b><span>form items / notarized forms</span></div><div><b>' + str(counts['capabilities']) + '</b><span>digital capabilities</span></div><div><b>Not ready</b><span>current bid readiness</span></div></div><p><a href="#costs">Explore cost assumptions ↓</a> · <a href="east-ramapo-pilot-plan.json">Structured planning JSON</a> · <a href="school-therapy-pilot-selection.html">Market selection evidence</a></p></header>'
page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + esc(core['title']) + '</title><style>' + CSS + '</style></head><body>' + header + '<div class="layout"><nav aria-label="Plan sections">' + nav + '</nav><main>' + body + '</main></div><footer>Public evidence and proposed design · No therapist, coverage, buyer commitment or achieved AI autonomy established</footer><script type="application/json" id="economics-data">' + embedded + '</script><script>' + SCRIPT + '</script></body></html>'
(OUT / 'east-ramapo-pilot-plan.html').write_text(page)
print(json.dumps({'built': ['east-ramapo-pilot-plan.html', 'east-ramapo-pilot-plan.json'], **counts}))
