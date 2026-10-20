"""Build a portable research/specification report from curated JSON; no network."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/amergis-phase5"
OUT = ROOT / "outputs"

def read(name):
    return json.loads((WORK / name).read_text())

def esc(value):
    return html.escape(str(value))

def label(value):
    return str(value).replace('_', ' ').replace('-', ' ')

def ul(values):
    return '<ul>' + ''.join('<li>' + render(x) + '</li>' for x in values) + '</ul>'

def render(value):
    if value is None:
        return '<span class="muted">Not established</span>'
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, list):
        return ul(value)
    if isinstance(value, dict):
        return '<dl>' + ''.join('<dt>' + esc(label(k)) + '</dt><dd>' + render(v) + '</dd>' for k,v in value.items()) + '</dl>'
    return esc(value)

def fields(row, omit=()):
    return '<dl>' + ''.join('<dt>' + esc(label(k)) + '</dt><dd>' + render(v) + '</dd>' for k,v in row.items() if k not in omit) + '</dl>'

def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th>'+esc(h)+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>'+v+'</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table></div>'

def detail(title, content, kind='', attrs=''):
    return '<details class="'+esc(kind)+'" '+attrs+'><summary>'+title+'</summary><div class="inside">'+content+'</div></details>'

plan = read('discovery-plan.json')
evidence = read('local-care-evidence.json')
obligations = read('obligations.json')
integrations = read('integrations.json')
domain = read('domain-spec.json')
scenarios = read('scenarios.json')
trace = read('traceability.json')
review = read('review.json') if (WORK / 'review.json').exists() else {'status':'Review pending'}

sources = evidence['sources'] + obligations['sources'] + integrations['sources']
source_map = {s['id']:s for s in sources}
assert len(source_map) == len(sources), 'Duplicate source IDs'

def refs(ids):
    return '<div class="refs">' + ' · '.join('<a href="'+esc(source_map[s]['url'])+'" target="_blank" rel="noopener">'+esc(s)+' · '+esc(source_map[s]['title'])+'</a>' for s in ids) + '</div>' if ids else '<p class="small muted">Independent design requirement; validate through the selected district and implementation.</p>'

groups = [('District evidence',evidence['requirement_candidates']), ('Operational obligations',obligations['requirements']), ('Integration and operating controls',integrations['requirements'])]
requirements = []
for category, rows in groups:
    for r in rows:
        requirements.append({
            'id':r['id'], 'title':r.get('title',r.get('name')), 'category':category,
            'priority':r.get('priority','Conditional' if r['id']=='LCR14' else 'Must'),
            'actor':r.get('actor',r.get('human_owner','Named owner in requirement')),
            'trigger':r.get('trigger','Applicable workflow or requirement change'),
            'behavior':r.get('required_behavior',r.get('behavior')),
            'exception':r.get('exception',r.get('open_questions',[])),
            'acceptance':r['acceptance'], 'applicability':r.get('applicability','Source-specific evidence informs a proposed design; actual pilot terms remain to be selected.'),
            'evidence_status':r.get('evidence_status',r.get('confidence')),
            'source_ids':r['source_ids'],
            'trace':trace['requirements'].get(r['id'],{})
        })

for r in requirements:
    assert r['behavior'] and r['acceptance'] and r['evidence_status']
    assert all(s in source_map for s in r['source_ids'])

counts = {'requirements':len(requirements),'source_records':len(sources),'unique_source_urls':len({s['url'].rstrip('/') for s in sources}), 'objects':len(domain['objects']), 'state_models':len(domain['state_models']), 'commands':len(domain['commands']), 'roles':len(domain['roles']), 'scenarios':len(scenarios['scenarios']), 'arithmetic_fixtures':len(scenarios['arithmetic_fixtures'])}
pack = {'title':plan['title'],'as_of':plan['as_of'],'status':plan['status'],'scope':plan['scope'],'counts':counts,'requirements':requirements,'discovery_plan':plan,'district_evidence':evidence,'obligations':obligations,'integrations':integrations,'domain_specification':domain,'scenario_pack':scenarios,'traceability':trace,'sources':sources,'independent_review':review}
OUT.mkdir(exist_ok=True)
(OUT/'school-therapy-requirements.json').write_text(json.dumps(pack,indent=2,ensure_ascii=False)+'\n')

brief = '<div class="scope-grid">' + ''.join('<article class="card"><div class="eyebrow">'+esc(t)+'</div><p>'+esc(v)+'</p></article>' for t,v in [('Selected market',plan['scope']['user_selected']),('Worked example',plan['scope']['worked_example']),('Open jurisdiction',plan['scope']['jurisdiction']),('Delivery and data',plan['scope']['delivery_model'])]) + '</div>'
brief += '<div class="callout"><b>Administration can be delegated. Clinical and educational authority stays explicit.</b><p>'+esc(plan['scope']['clinical_boundary'])+'</p><p>'+esc(plan['scope']['student_data_boundary'])+'</p></div>'
brief += '<h3>What changed from the broad staffing roadmap</h3>' + table(['Capability','School-therapy requirement'],[[esc(x['product']),esc(x['change'])] for x in plan['product_changes_from_phase4']])
brief += '<h3>New evidence that changes the design</h3>' + render(evidence['key_design_findings'])

journey = ''.join('<article class="journey-card"><div class="eyebrow">'+esc(j['id'])+'</div><h3>'+esc(j['stage'])+'</h3>'+fields(j,('id','stage'))+'</article>' for j in plan['journey'])

req_cards = []
for r in requirements:
    body = fields(r,('id','title','category','priority','source_ids','trace')) + '<div class="gate"><b>Trace and future validation</b>'+render(r['trace'])+'</div>'+refs(r['source_ids'])
    req_cards.append(detail('<span class="id">'+esc(r['id'])+'</span> '+esc(r['title'])+' <span class="tag">'+esc(r['category'])+'</span>',body,'requirement','data-category="'+esc(r['category'])+'" data-priority="'+esc(r['priority'])+'"'))

source_cards = ''.join(detail('<span class="id">'+esc(s['id'])+'</span> '+esc(s['title']),'<p><a href="'+esc(s['url'])+'" target="_blank" rel="noopener">Open primary source</a></p>'+fields(s,('id','title','url')),'source', 'id="source-'+esc(s['id'])+'"') for s in sources)
source_cards += '<h3>Unresolved source conflicts and limitations</h3>'+render(evidence['source_exceptions'])+'<div class="callout">Source availability and source applicability are separate. Historical contract examples and unawarded solicitations do not bind a new operator. Failed direct retrievals and indexed-text evidence are disclosed in each source record.</div>'

objects=[]
for obj in domain['objects']:
    decoded_fields = [dict(zip(domain['record_formats']['field_columns'],f)) if isinstance(f,list) else f for f in obj['fields']]
    rows = [[esc(f['name']),esc(f['type']),render(f['name'] in obj.get('required_at_create',[])),esc(f.get('definition','')),esc(f.get('validation','')),esc(f.get('privacy',''))] for f in decoded_fields]
    content = fields(obj,('id','name','fields')) + table(['Field','Type','Required at creation','Meaning','Validation','Data class'],rows)
    objects.append(detail('<span class="id">'+esc(obj['id'])+'</span> '+esc(obj['name']),content,'domain-object'))
state_models=[]
for sm in domain['state_models']:
    rows=[]
    for t in sm['transitions']:
        rows.append([esc(', '.join(t['from']))+' → '+esc(t['to']),esc(t['command_id']),esc(', '.join(t['actor_roles'])),esc(t['prerequisites']),esc(t['evidence_required']),esc(t['on_exception'])])
    content=fields(sm,('id','name','transitions'))+table(['Transition','Command','Roles','Prerequisite','Evidence','Exception'],rows)
    state_models.append(detail('<span class="id">'+esc(sm['id'])+'</span> '+esc(sm['name']),content,'state-model'))
domain_html = '<div class="callout"><b>Proposed bounded state models</b><p>'+esc(domain['status'])+'</p>'+render(domain['scope'])+'</div><h3>Objects and fields</h3>'+''.join(objects)+'<h3>Workflow state models</h3>'+''.join(state_models)
domain_html += detail('Shared types, fields, storage and lifecycle rules',fields(domain,('id','title','as_of','status','basis','scope','objects','state_models','commands','roles','permission_matrix')))

roles = ''.join(detail('<span class="id">'+esc(r['id'])+'</span> '+esc(r['name']),fields(r,('id','name')),'role') for r in domain['roles'])
roles += '<h3>Permission matrix</h3>'+table(['Role','Objects','Actions','Conditions'],[[esc(x['role_id']),render(x['object_ids']),render(x['actions']),esc(x['conditions'])] for x in domain['permission_matrix']])
roles += '<h3>Command contracts</h3><p>These contracts describe future application behavior. They are not discovered Amergis endpoints or deployed APIs.</p>'
decoded_commands = [dict(zip(domain['record_formats']['command_columns'],c)) if isinstance(c,list) else c for c in domain['commands']]
transition_by_command = {t['command_id']:t for sm in domain['state_models'] for t in sm['transitions']}
for command in decoded_commands:
    command['transition_contract'] = transition_by_command.get(command['id'],{})
roles += ''.join(detail('<span class="id">'+esc(c['id'])+'</span> '+esc(c['name']),fields(c,('id','name')),'command') for c in decoded_commands)

scenario_html='<div class="callout"><b>Specification checks are not product tests</b>'+render(scenarios['validation_statement'])+'</div>'
scenario_html+=''.join(detail('<span class="id">'+esc(s['id'])+'</span> '+esc(s['title']),fields(s,('id','title')),'scenario') for s in scenarios['scenarios'])
scenario_html+='<h3>Artificial financial fixtures</h3>'+render(scenarios['arithmetic_policy'])
scenario_html+=''.join(detail('<span class="id">'+esc(f['id'])+'</span> '+esc(f['description']),fields(f,('id','description')),'financial-fixture') for f in scenarios['arithmetic_fixtures'])
scenario_html+='<h3>Future pilot measures</h3>'+''.join(detail('<span class="id">'+esc(m['id'])+'</span> '+esc(m['name']),fields(m,('id','name')),'metric') for m in scenarios['metrics'])
scenario_html+='<h3>Coverage and gaps</h3>'+render({k:v for k,v in trace.items() if k!='requirements'})

vendors='<p>'+esc(integrations['status'])+'</p>'+''.join(detail('<span class="id">'+esc(p['id'])+'</span> '+esc(p['capability']),fields(p,('id','capability','source_ids'))+refs(p['source_ids']),'integration') for p in integrations['profiles'])
vendors+='<h3>Evidence needed before an adapter is considered tested</h3>'+render(integrations['conformance_evidence_required'])+'<p>'+esc(integrations['rule'])+'</p>'

discovery='<h3>Decisions needed for the pilot</h3>'+table(['Decision','Status / owner','Evidence needed','Blocks'],[[esc(d['id'])+' · '+esc(d['topic']),esc(d['status'])+'<br>'+esc(d['owner']),esc(d['evidence_needed']),esc(d['blocks'])] for d in plan['decisions']])
discovery+='<h3>Prepared discovery sessions</h3><p>No interviews, outreach, demos, registrations or procurement were performed.</p>'+''.join(detail('<span class="id">'+esc(s['id'])+'</span> '+esc(s['audience']),fields(s,('id','audience')),'interview') for s in plan['discovery_sessions'])
discovery+='<h3>Discipline and responsibility differences</h3>'+render(obligations['discipline_discovery_checklist'])
discovery+='<h3>Unit economics and cash requirements</h3>'+render(plan['economics'])
discovery+='<h3>Next implementation sequence</h3>'+render(plan['next_steps'])
discovery+='<h3>Additional district questions and production unknowns</h3>'+render(evidence['remaining_discovery_questions'])+render(obligations['production_blocking_unknowns'])
discovery+='<h3>Independent review</h3>'+render(review)

sections=[('brief','Scope & findings',brief),('journey','Staffing journey','<div class="journey-grid">'+journey+'</div>'),('requirements','Requirements','<div class="controls"><label for="req-query">Search</label><input id="req-query" type="search" placeholder="e.g. missed session, invoice, consent"><label for="req-category">Evidence group</label><select id="req-category"><option value="">All groups</option>'+''.join('<option>'+esc(g[0])+'</option>' for g in groups)+'</select><span id="req-count" class="small"></span></div>'+''.join(req_cards)),('domain','Data & states',domain_html),('authority','Roles & commands',roles),('scenarios','Acceptance scenarios',scenario_html),('integrations','Vendor conformance',vendors),('evidence','Source evidence',source_cards),('discovery','Decisions & research',discovery)]
css='''
:root{--navy:#173c51;--teal:#146f69;--ink:#233b4a;--muted:#5d7180;--bg:#f2f5f6;--line:#d7e1e5;--light:#e5f2ee}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,sans-serif}a{color:#076d83;text-underline-offset:3px}header{background:var(--navy);color:#fff;padding:34px max(24px,calc((100vw - 1280px)/2));border-bottom:5px solid #55b3a1}header p{max-width:980px;color:#d8e9ed}h1,h2,h3,p{margin:0 0 12px}h1{font-size:36px;line-height:1.15;letter-spacing:-.7px}h2{font-size:26px}h3{font-size:19px;margin-top:24px}.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:1.4px;font-weight:700;margin-bottom:9px}.links{display:flex;flex-wrap:wrap;gap:20px;font-size:13px;margin-top:20px}header a{color:#c3eee3}main{max-width:1328px;margin:auto;padding:0 24px 48px}.stats{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:22px 0}.stat{background:#fff;padding:15px;border:1px solid var(--line);border-radius:6px}.stat strong{display:block;font-size:28px;color:var(--teal);line-height:1.2}.stat span{font-size:11px;color:var(--muted)}nav{position:sticky;top:0;z-index:2;background:var(--bg);display:flex;gap:6px;overflow:auto;border-block:1px solid var(--line);padding:10px 0}nav a{padding:7px 10px;text-decoration:none;white-space:nowrap;font-size:12px;border-radius:4px}nav a:hover{background:var(--light)}section{padding-top:30px;scroll-margin-top:52px}.scope-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card,.journey-card{background:#fff;border:1px solid var(--line);border-radius:7px;padding:19px}.card p{font-size:13px;margin:0}.journey-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.journey-card{border-top:3px solid var(--teal)}.journey-card h3{margin-top:0}.callout,.gate{background:#e8f3ef;border-left:4px solid var(--teal);padding:18px;margin:20px 0}.callout p:last-child{margin-bottom:0}.gate{font-size:13px}.muted,.small{color:var(--muted)}.small{font-size:12px}.table-wrap{overflow:auto;border:1px solid var(--line);background:#fff;border-radius:6px}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}th{background:#e6eef2;font-size:11px;text-transform:uppercase;letter-spacing:.4px}td ul{margin:0}details{background:#fff;border:1px solid var(--line);border-radius:6px;margin:10px 0}summary{padding:16px;cursor:pointer;font-weight:600}.inside{padding:0 18px 18px}.id{display:inline-block;font-size:11px;color:var(--teal);margin-right:6px;font-weight:700}.tag{font-size:10px;background:#e7f1ee;color:#286557;border-radius:4px;padding:3px 6px;margin-left:8px;white-space:nowrap}.refs{font-size:12px;padding-top:14px;border-top:1px solid var(--line)}dl{margin:0}dt{font-size:11px;text-transform:uppercase;letter-spacing:.6px;font-weight:650;color:var(--muted);margin:14px 0 4px}dd{margin:0}ul{padding-left:20px;margin:4px 0 12px}li{margin:5px 0}li dl{margin:12px 0}li>ul{margin:4px 0}input,select{font:inherit;padding:10px 12px;border:1px solid #b9c9d0;border-radius:4px;background:white}input{min-width:260px;flex:1}.controls{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin:18px 0}label{font-size:12px;font-weight:600}.requirement[hidden]{display:none}footer{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:20px;margin-top:30px}@media(max-width:900px){.scope-grid,.stats{grid-template-columns:repeat(2,1fr)}.journey-grid{grid-template-columns:1fr}h1{font-size:29px}main{padding-inline:16px}header{padding:26px 18px}}@media print{nav,.controls{display:none}.stats,.scope-grid,.journey-grid{display:block}.card,.stat,.journey-card{margin-bottom:10px;break-inside:avoid}body{background:white}}
'''
stats=[(counts['requirements'],'requirements with acceptance criteria'),(counts['source_records'],'source records'),(counts['objects'],'domain objects'),(counts['state_models'],'bounded state models'),(counts['scenarios'],'future acceptance scenarios'),(len(plan['decisions']),'open pilot decisions')]
content='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>School therapy staffing · Requirements pack</title><style>'+css+'</style></head><body><header><div class="eyebrow">Amergis research · Phase 5 · '+esc(plan['as_of'])+'</div><h1>School therapy staffing<br>Requirements grounded in evidence</h1><p>District demand → therapist readiness → approved assignment → school service evidence → time, pay and district invoice. SLP worked example with OT/PT variants.</p><div class="links"><a href="school-therapy-requirements.json" download>Download structured requirements</a><a href="amergis-product-roadmap.html">Product roadmap</a><a href="amergis-api-reconstruction.html">Portal and API research</a></div></header><main><div class="stats">'+''.join('<div class="stat"><strong>'+str(n)+'</strong><span>'+esc(t)+'</span></div>' for n,t in stats)+'</div><nav aria-label="Requirements pack navigation">'+''.join('<a href="#'+sid+'">'+esc(title)+'</a>' for sid,title,_ in sections)+'</nav>'+''.join('<section id="'+sid+'"><h2>'+esc(title)+'</h2>'+body+'</section>' for sid,title,body in sections)+'<footer>'+esc(plan['status'])+'. Independent review: '+esc(review.get('status','pending'))+'. Fixture/graph/source validation does not demonstrate live workflow behavior, legal completeness or automation performance.</footer></main><script>(()=>{const q=document.getElementById("req-query"),s=document.getElementById("req-category"),cards=[...document.querySelectorAll(".requirement")];function filter(){let n=0;for(const c of cards){c.hidden=!(c.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!s.value||c.dataset.category===s.value));if(!c.hidden)n++;}document.getElementById("req-count").textContent=n+" of "+cards.length+" requirements";}q.addEventListener("input",filter);s.addEventListener("change",filter);filter();})();</script></body></html>'
(OUT/'school-therapy-requirements.html').write_text(content)
print(json.dumps({'output':'outputs/school-therapy-requirements.html','counts':counts,'review':review.get('status')}))
