"""Build the pilot selection report from curated evidence; no network access."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/amergis-phase6'
OUT = ROOT / 'outputs'

def read(name):
    return json.loads((WORK / (name + '.json')).read_text())

def esc(x):
    return html.escape(str(x))

def render(x):
    if isinstance(x, list):
        return '<ul>' + ''.join('<li>' + render(v) + '</li>' for v in x) + '</ul>'
    if isinstance(x, dict):
        return '<dl>' + ''.join('<dt>' + esc(k.replace('_', ' ')) + '</dt><dd>' + render(v) + '</dd>' for k, v in x.items()) + '</dl>'
    return esc(x) if x is not None else 'Not established'

def fields(x, omit=()):
    return render({k:v for k,v in x.items() if k not in omit})

def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th>' + esc(x) + '</th>' for x in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + x + '</td>' for x in row) + '</tr>' for row in rows) + '</tbody></table></div>'

selection = read('selection')
regional = {name: read(name) for name in ['challengers', 'texas', 'carolina-georgia', 'midatlantic']}
credentials = read('state-credential-fit')
risk = read('buyer-risk')
review = read('review') if (WORK / 'review.json').exists() else {'status': 'Pending independent review'}
sources = selection['sources'] + credentials['sources'] + risk['sources']
districts = []
codes = {'New York': 'NY', 'Texas': 'TX', 'North Carolina': 'NC', 'Georgia': 'GA', 'Virginia': 'VA', 'Maryland': 'MD'}
for group, data in regional.items():
    sources += data['sources']
    for row in data['districts']:
        row = dict(row)
        row['state_code'] = codes.get(row['state'], row['state'])
        row['research_group'] = group
        districts.append(row)
source_map = {s['id']:s for s in sources}
assert len(source_map) == len(sources), 'Duplicate source IDs'
district_map = {d['id']:d for d in districts}

statuses = {
    'CHD01': 'Open bid', 'CHD02': 'Open bid', 'CHD03': 'Alternative model',
    'TXD01': 'Open bid · conflict', 'TXD02': 'Unverified entry', 'TXD03': 'Unverified entry', 'TXD04': 'Closed / awarded',
    'SGD01': 'Closed / awarded', 'SGD02': 'Closed / awarded', 'SGD03': 'Closed / awarded',
    'SGD04': 'Closed / awarded', 'SGD05': 'Closed / awarded', 'SGD06': 'Closed / awarded',
    'MAD01': 'Standing entry · gated', 'MAD02': 'Closed / awarded', 'MAD03': 'Unverified entry', 'MAD04': 'Closed / awarded'
}
for d in districts:
    d['entry_class'] = statuses[d['id']]
for p in selection['priorities']:
    if 'district_id' not in p:
        matches = [d for d in districts if p['district_name_match'] in d['name']]
        assert len(matches) == 1
        p['district_id'] = matches[0]['id']
    p['name'] = district_map[p['district_id']]['name']

calendar = [
    {'buyer': 'Birdville ISD', 'district_id': 'TXD01', 'date': '2026-10-21', 'time': '14:00 America/Chicago / 15:00 Eastern', 'event': 'Official retrieved bid deadline; conflicting later-deadline lead unresolved', 'action': 'Check latest addenda and entity eligibility first. Not a launch deadline to chase from zero.', 'source_ids': ['TXS01','TXS02']},
    {'buyer': 'East Ramapo', 'district_id': 'CHD01', 'date': '2026-10-27', 'time': '12:00 America/New_York', 'event': 'SLP questions due', 'action': 'Prepare eligibility, term, funding and small-assignment questions; no questions sent.', 'source_ids': ['CHS04']},
    {'buyer': 'Rockland BOCES', 'district_id': 'CHD02', 'date': '2026-10-29', 'time': '11:00 America/New_York', 'event': 'SLP / OT / PT proposals due', 'action': 'SLP reviewed in detail; sealed paper delivery. Check all current addenda and readiness.', 'source_ids': ['CHS01','CHS02']},
    {'buyer': 'East Ramapo', 'district_id': 'CHD01', 'date': '2026-10-30', 'time': '12:00 America/New_York', 'event': 'SLP electronic proposals due', 'action': 'Named clinician resumes/references; in-person delivery only. Recheck addenda.', 'source_ids': ['CHS04','CHS05']}
]

pack = {'title': selection['title'], 'as_of': selection['as_of'], 'status': selection['status'], 'selection': selection,
        'counts': {'states_compared': 6, 'buyer_records': len(districts), 'source_records': len(sources), 'unique_source_urls': len({s['url'] for s in sources})},
        'calendar': calendar, 'districts': districts, 'credentials': credentials, 'buyer_risk': risk,
        'regional_research': regional, 'sources': sources, 'independent_review': review}
OUT.mkdir(exist_ok=True)
(OUT / 'school-therapy-pilot-selection.json').write_text(json.dumps(pack, indent=2, ensure_ascii=False) + '\n')

def refs(ids):
    return '<div class="refs">' + ' · '.join('<a href="#source-' + esc(i) + '">' + esc(i) + '</a>' for i in ids) + '</div>'

def details(title, body, css='', attrs=''):
    return '<details class="' + esc(css) + '" ' + attrs + '><summary>' + title + '</summary><div class="inside">' + body + '</div></details>'

decision = selection['decision']
brief = '<p class="lead">' + esc(decision['rationale']) + '</p><div class="callout"><b>Target selection, not bid readiness.</b><p>' + esc(decision['qualification']) + '</p><p>' + esc(decision['time_sensitivity']) + '</p></div>'
brief += '<div class="grid">' + ''.join('<article class="card"><span class="eyebrow">' + esc(t) + '</span><p>' + esc(v) + '</p></article>' for t, v in [
    ('Proposed first assignment', selection['method']['proposed_pilot']), ('Ongoing district route', decision['standing_alternative']), ('Different service model', decision['alternate_model'])]) + '</div>'
brief += refs(decision['source_ids'])
priority = ''.join('<article class="priority"><span class="rank">0' + str(p['rank']) + '</span><div><span class="eyebrow">' + esc(p['label']) + '</span><h3><a href="#buyer-' + p['district_id'] + '">' + esc(p['name']) + '</a></h3><p>' + esc(p['why']) + '</p><p><b>Gate:</b> ' + esc(p['gate']) + '</p><p class="muted">' + esc(p['confidence']) + '</p></div></article>' for p in selection['priorities'])

calendar_html = '<p>Snapshot: October 20, 2026. Eastern times below are EDT on these dates. No bid or question has been submitted. Always check the current buyer packet and subsequent amendments.</p>'
calendar_html += table(['Date', 'Buyer / event', 'Time', 'Decision before action'], [[esc(c['date']), '<b>'+esc(c['buyer'])+'</b><br>'+esc(c['event'])+refs(c['source_ids']), esc(c['time']), esc(c['action'])] for c in calendar])
calendar_html += '<p class="muted">Frederick’s additional-provider route and NYCPS’s independent-provider application have no fixed next deadline identified in the reviewed material. Qualification and assignment approval still apply. Griffin-Spalding’s October 30 MSP deadline is separately recorded as an adjacent broad-scope opportunity.</p>'

state_html = table(['State / priority', 'Purchasing access', 'Credential / operating tradeoff'], [[ '<b>'+esc(s['name'])+'</b><br>'+esc(s['position']), esc(s['access']), esc(s['credential_fit'])+'<p>'+esc(s['tradeoff'])+'</p>'+refs(s['source_ids'])] for s in selection['state_comparison']])
context = selection['workforce_context']
state_html += '<h3>Recruitment context, not available supply</h3><p>' + esc(context['measure']) + '.</p>'
state_html += table(['State', 'Certified SLP-only total', 'PDF page'], [[esc(r['state']), format(r['count'], ','), str(r['pdf_page'])] for r in context['rows']])
state_html += '<p class="muted">' + esc(context['limit']) + '</p>' + refs([context['source_id']])

state_options = ''.join('<option value="'+s['state']+'">'+esc(s['name'])+'</option>' for s in selection['state_comparison'])
entry_options = ''.join('<option>'+esc(x)+'</option>' for x in sorted(set(statuses.values())))
buyers = '<div class="filters"><label>Search buyers or requirements<input id="buyer-query" type="search" placeholder="e.g. SLP, references, in-person"></label><label>State<select id="buyer-state"><option value="">All states</option>'+state_options+'</select></label><label>Entry route<select id="buyer-entry"><option value="">All routes</option>'+entry_options+'</select></label><button id="reset">Reset</button></div><p id="result-count" role="status"></p>'
for d in districts:
    title = '<span class="id">'+esc(d['id'])+'</span> '+esc(d['name'])+' <span class="tag">'+esc(d['entry_class'])+'</span>'
    body = fields(d, ('id','name','state','state_code','source_ids','research_group','entry_class')) + refs(d['source_ids'])
    buyers += details(title, body, 'buyer', 'id="buyer-'+d['id']+'" data-state="'+d['state_code']+'" data-entry="'+esc(d['entry_class'])+'"')
buyers += '<h3>Adjacent leads and exclusions</h3>' + render(regional['challengers']['watchlist_and_exclusions']) + render(regional['carolina-georgia'].get('adjacent_live_leads', []))

credential_html = '<p>'+esc(credentials['scope'])+'</p>'
credential_html += '<div class="callout"><b>Compact membership is not a practice privilege.</b><p>Do not assume compact mobility for the six compared states. Verify actual operational status and each clinician’s authority before placement.</p></div>'
for s in credentials['state_profiles']:
    credential_html += details(esc(s['name']), fields(s, ('id','name','state_code','source_ids')) + refs(s['source_ids']), 'credential')
credential_html += details('Shared compact evidence and limits', render(credentials.get('compact_snapshot', credentials.get('compact_status', {}))))

risk_html = '<p>'+esc(risk['conclusion'])+'</p>'
for b in risk['buyers']:
    content = '<p><b>'+esc(b['assessment'])+'</b></p>'
    for f in b['facts']:
        content += '<p>'+esc(f['text'])+'</p><small>'+esc(f['locator'])+'</small>'+refs(f['source_ids'])
    content += '<h4>Limits</h4>'+render(b['limits'])+'<p><b>Pilot implication:</b> '+esc(b['pilot_implication'])+'</p>'
    risk_html += details(esc(b['name']), content)
risk_html += render(risk['comparison_limits'])

validation_html = '<p>These are the next evidence gates. Outreach, registration, reference checks and submission have not been performed.</p>'
validation_html += ''.join('<article class="card"><span class="eyebrow">Gate '+str(g['step'])+'</span><h3>'+esc(g['decision'])+'</h3>'+fields(g, ('step','decision'))+'</article>' for g in selection['validation_plan'])
validation_html += '<h3>What would change the recommendation?</h3>' + table(['Condition', 'Effect'], [[esc(s['condition']), esc(s['effect'])] for s in selection['sensitivity']])
validation_html += '<h3>Requirements to carry into the product</h3>' + table(['Finding', 'Requirement'], [[esc(p['finding']), esc(p['requirement'])] for p in selection['product_implications']])
validation_html += '<div class="callout">'+esc(selection['method']['ai_scope'])+'</div>'

sources_html = '<p>Primary evidence is linked below. Source facts, unresolved conflicts and analyst recommendations remain distinct. Source record counts include separate records that may share a URL.</p>'
for s in sources:
    sources_html += details('<span class="id">'+esc(s['id'])+'</span> '+esc(s['title']), '<p><a href="'+esc(s['url'])+'" target="_blank" rel="noopener">Open source ↗</a></p>'+fields(s, ('id','title','url')), 'source', 'id="source-'+s['id']+'"')
method_html = fields(selection['method']) + '<p>'+esc(selection['not_performed'])+'</p>'
method_html += '<h3>Independent review</h3>'+render(review)+'<p class="muted">Report checks cover source references, dates, rendering structure and filters in a local DOM. They do not validate a live service, therapist availability, credit, legal eligibility or a rendered browser layout.</p>'

sections = [('recommendation','Recommendation',brief), ('priorities','Buyer priorities',priority), ('calendar','Procurement dates',calendar_html), ('states','State comparison',state_html), ('buyers','Explore buyers',buyers), ('credentials','Credential and entity gates',credential_html), ('risk','Buyer funding and payment',risk_html), ('validation','Validation plan',validation_html), ('sources','Evidence register',sources_html), ('method','Method and review',method_html)]
nav = ''.join('<a href="#'+i+'">'+esc(t)+'</a>' for i,t,_ in sections)
body = ''.join('<section id="'+i+'"><div class="section-head"><span>'+str(n+1).zfill(2)+'</span><h2>'+esc(t)+'</h2></div>'+c+'</section>' for n,(i,t,c) in enumerate(sections))
css = '''
:root{--ink:#162b35;--muted:#586d78;--paper:#f2f5f5;--line:#d6e0e3;--accent:#006b67;--soft:#e6f2ef;--amber:#84561d}*{box-sizing:border-box}body{margin:0;background:var(--paper);font:16px/1.6 system-ui,-apple-system,sans-serif;color:var(--ink)}a{color:var(--accent);text-underline-offset:3px}header{padding:62px max(24px,calc((100vw - 1180px)/2));background:#123d49;color:white}header h1{font-size:clamp(32px,4.4vw,58px);line-height:1.12;max-width:1000px;margin:16px 0 24px;letter-spacing:-1.8px}header p{max-width:820px;color:#d6e7e9}header a{color:#c8f0e5}.eyebrow{text-transform:uppercase;letter-spacing:1.6px;font-size:11px;font-weight:750}.stats{display:flex;gap:32px;margin:28px 0 12px;flex-wrap:wrap}.stats b{font-size:27px;display:block}.stats span{font-size:12px;color:#b7d3d8}.layout{display:grid;grid-template-columns:210px minmax(0,1fr);max-width:1280px;margin:auto;gap:34px;padding:30px 26px}nav{position:sticky;top:22px;align-self:start}nav a{display:block;padding:8px 10px;text-decoration:none;font-size:13px;border-left:2px solid var(--line)}nav a:hover{background:var(--soft);border-color:var(--accent)}main{min-width:0}section{scroll-margin-top:24px;margin-bottom:48px}.section-head{display:flex;align-items:center;gap:14px;margin-bottom:16px}.section-head>span{color:var(--accent);font-size:12px;font-weight:750}h2{font-size:27px;line-height:1.2;letter-spacing:-.5px}h3{font-size:19px;margin:10px 0}h4{margin-bottom:6px}p{margin:10px 0}.lead{font-size:20px;line-height:1.6}.callout{background:var(--soft);border-left:4px solid var(--accent);padding:20px 24px;margin:22px 0;border-radius:0 10px 10px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}.card{background:white;border:1px solid var(--line);border-radius:12px;padding:20px;margin:14px 0}.priority{display:grid;grid-template-columns:56px 1fr;gap:16px;background:white;border:1px solid var(--line);border-radius:12px;padding:24px;margin:14px 0}.rank{font-size:30px;color:var(--accent);font-weight:300}.muted,small{color:var(--muted);font-size:13px}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:white;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:600px}th{text-align:left;background:#e9eff0;color:#3b515c;font-size:11px;letter-spacing:1px;text-transform:uppercase}td,th{padding:14px 16px;vertical-align:top;border-bottom:1px solid var(--line)}td{font-size:14px}tr:last-child td{border:0}.refs{font-size:12px;line-height:1.5;margin:8px 0 16px}.filters{display:flex;gap:12px;align-items:end;flex-wrap:wrap}.filters label{font-size:12px;font-weight:650;flex:1;min-width:160px}input,select,button{font:inherit;font-size:14px;padding:11px;border:1px solid #a9bec5;border-radius:7px;background:white;color:var(--ink)}input,select{display:block;width:100%;margin-top:5px}button{cursor:pointer}details{background:white;border:1px solid var(--line);border-radius:9px;margin:10px 0}summary{cursor:pointer;padding:17px 20px;font-weight:650;font-size:14px}summary:hover{background:#edf5f3}.inside{padding:4px 22px 22px}.id{font-size:10px;color:var(--muted);margin-right:8px}.tag{display:inline-block;font-weight:500;font-size:10px;border:1px solid var(--line);border-radius:20px;padding:2px 8px;margin-left:6px;background:#f2f5f5}dl{margin:10px 0}dt{text-transform:capitalize;color:var(--muted);font-size:11px;font-weight:750;margin-top:16px;letter-spacing:.4px}dd{margin:3px 0 0;font-size:14px}ul{padding-left:21px}li{margin:7px 0}a,dd,td{overflow-wrap:anywhere}[hidden]{display:none!important}footer{padding:32px;text-align:center;color:var(--muted);font-size:12px}@media(max-width:850px){.layout{display:block;padding:20px}nav{position:static;display:flex;overflow-x:auto;margin-bottom:26px;gap:8px}nav a{white-space:nowrap;border-left:0;border-bottom:2px solid var(--line)}header{padding:34px 24px}.priority{grid-template-columns:40px 1fr;padding:18px}}@media print{nav,.filters{display:none}.layout{display:block}header{background:white;color:var(--ink);padding:10px}header p,header a,.stats span{color:var(--ink)}details{break-inside:avoid}.table-wrap{overflow:visible}table{min-width:0}section{margin-bottom:28px}}
'''
script = '''
const query=document.getElementById('buyer-query'),state=document.getElementById('buyer-state'),entry=document.getElementById('buyer-entry');
const rows=[...document.querySelectorAll('.buyer')];
function filter(){const q=(query.value||'').trim().toLowerCase(),s=state.value||'',e=entry.value||'';let n=0;for(const row of rows){row.hidden=!!((s&&row.dataset.state!==s)||(e&&row.dataset.entry!==e)||(q&&!row.textContent.toLowerCase().includes(q)));if(!row.hidden)n++;}document.getElementById('result-count').textContent=n+' of '+rows.length+' buyer records shown';}
for(const el of [query,state,entry])el.addEventListener(el===query?'input':'change',filter);
document.getElementById('reset').addEventListener('click',()=>{query.value='';state.value='';entry.value='';filter();});
document.addEventListener('click',event=>{const a=event.target.closest('a[href^="#"]');if(!a)return;const target=document.getElementById(a.getAttribute('href').slice(1));if(target&&target.tagName==='DETAILS'){target.open=true;target.hidden=false;}});
filter();
'''
page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(selection['title'])+'</title><style>'+css+'</style></head><body><header><span class="eyebrow">Amergis independent operating model · Phase 06 · 20 October 2026</span><h1>'+esc(decision['headline'])+'</h1><p>First target: East Ramapo. Second buyer: Rockland BOCES. A practical market choice based on purchasing access, narrow assignments and explicit operating gates.</p><div class="stats"><div><b>6</b><span>states compared in depth</span></div><div><b>'+str(len(districts))+'</b><span>buyer records</span></div><div><b>'+str(len(sources))+'</b><span>source records</span></div></div><p><a href="school-therapy-pilot-selection.json">Structured research JSON</a> · <a href="school-therapy-requirements.html">School therapy requirements</a></p></header><div class="layout"><nav aria-label="Report sections">'+nav+'</nav><main>'+body+'</main></div><footer>Public evidence snapshot • Proposed independent business • No buyer commitment, live operations or achieved AI autonomy</footer><script>'+script+'</script></body></html>'
(OUT / 'school-therapy-pilot-selection.html').write_text(page)
print(json.dumps({'built': ['school-therapy-pilot-selection.html','school-therapy-pilot-selection.json'], **pack['counts']}))
