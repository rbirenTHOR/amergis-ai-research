import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/amergis-phase4'
OUT = ROOT / 'outputs'

def read(name):
    return json.loads((WORK/name).read_text())

def esc(x):
    return html.escape(str(x))

def items(values):
    if isinstance(values, str):
        return '<p>'+esc(values)+'</p>'
    return '<ul>'+''.join('<li>'+esc(x)+'</li>' for x in values)+'</ul>'

def value(x):
    if isinstance(x, bool):
        return '<p>'+('Yes' if x else 'No')+'</p>'
    if isinstance(x, list):
        return items([json.dumps(y, ensure_ascii=False) if isinstance(y, dict) else y for y in x])
    if isinstance(x, dict):
        return '<dl>'+''.join('<dt>'+esc(k.replace('_',' '))+'</dt><dd>'+value(v)+'</dd>' for k,v in x.items())+'</dl>'
    return '<p>'+esc(x)+'</p>'

core = read('plan-core.json')
portfolio = read('portfolio.json')
reconstruction = read('reconstruction.json')
review = read('review.json')
api = json.loads((OUT/'amergis-api-reconstruction.json').read_text())
products = portfolio['products']
areas = reconstruction['areas']
source_map = {s['id']:s for s in api['sources']}

def refs(ids):
    rows=[]
    for sid in ids:
        s=source_map.get(sid)
        if s:
            rows.append('<a href="'+esc(s['url'])+'" target="_blank" rel="noopener">'+esc(s['title'])+'</a>')
    return '<div class="refs">'+' · '.join(rows)+'</div>'

def fields(row, excluded):
    return ''.join('<div class="label">'+esc(k.replace('_',' '))+'</div>'+value(v) for k,v in row.items() if k not in excluded)

D=dict(core, portfolio=portfolio, reconstruction=reconstruction, independent_review=review, sources=api['sources'])
(OUT/'amergis-product-roadmap.json').write_text(json.dumps(D,indent=2,ensure_ascii=False)+'\n')
architecture=''.join('<div class="arch"><div class="eyebrow">'+esc(x['layer'])+'</div>'+items(x['components'])+'<p class="muted small">'+esc(x['rule'])+'</p></div>' for x in core['architecture'])
product_cards=''.join('<article class="card product" data-decision="'+esc(p['decision'])+'"><div class="eyebrow">'+esc(p['id'])+' · '+esc(p['layer'])+'</div><h3>'+esc(p['name'])+'</h3><span class="tag">'+esc(p['decision'])+'</span>'+fields(p,{'id','name','layer','decision','source_ids','references'})+refs(p.get('source_ids',[]))+'</article>' for p in products)
area_cards=''.join('<details class="reconstruction-area"><summary>'+esc(a['area'])+' <span class="tag">'+esc(a['feasibility'])+'</span></summary><div class="inside">'+fields(a,{'id','area','feasibility','source_ids','references'})+refs(a.get('source_ids',[]))+'</div></details>' for a in areas)
state_examples=[]
for sm in reconstruction['state_machines']:
    rows=''.join('<tr><td>'+esc(t['from'])+' → '+esc(t['to'])+'</td><td>'+esc(t['actor'])+'</td><td>'+esc(t['guard'])+'</td></tr>' for t in sm['transitions'])
    state_examples.append('<details class="state-machine"><summary>'+esc(sm['name'])+'</summary><div class="inside"><p class="muted">'+esc(sm['scope'])+' '+esc(sm['status'])+'</p><div class="table-wrap"><table><thead><tr><th>Selected transition</th><th>Actor</th><th>Prerequisite</th></tr></thead><tbody>'+rows+'</tbody></table></div><div class="label">Exception behavior</div>'+items(sm['exceptions'])+'<div class="label">Acceptance cases to implement</div>'+items(sm['acceptance'])+'</div></details>')
state_cards=''.join(state_examples)
records=''.join('<tr><td>'+esc(x['records'])+'</td><td>'+esc(x['owner'])+'</td><td>'+esc(x['boundary'])+'</td></tr>' for x in core['system_of_record_decisions'])
releases=''.join('<article class="card"><div class="eyebrow">'+esc(x['id'])+'</div><h3>'+esc(x['name'])+'</h3><div class="label">Build</div><p>'+esc(x['build'])+'</p><div class="label">Establish</div><p>'+esc(x['establish'])+'</p><div class="gate"><b>Exit evidence</b><p>'+esc(x['exit'])+'</p></div></article>' for x in core['release_slices'])
sprint=''.join('<tr><td>'+str(x['priority'])+'</td><td><b>'+esc(x['task'])+'</b><p>'+esc(x['deliverable'])+'</p></td><td>'+esc(x['completion'])+'</td></tr>' for x in core['next_discovery_sprint'])
ats=core['ats_selection_gate']
content=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amergis research · Digital product roadmap</title><style>
:root{{--ink:#183044;--navy:#14384f;--teal:#126d69;--bg:#eff3f5;--line:#d7e1e7;--muted:#586c7a}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,sans-serif}}a{{color:#086887;text-underline-offset:3px}}header{{padding:38px max(24px,calc((100vw - 1240px)/2));background:var(--navy);color:white;border-bottom:5px solid #4ca99b}}header p{{max-width:940px;color:#dfedf3}}header a{{color:#ccefe7}}h1{{font-size:35px;line-height:1.2;letter-spacing:-.6px}}h1,h2,h3,p{{margin:0 0 12px}}h2{{font-size:25px}}h3{{font-size:18px}}main{{max-width:1288px;margin:auto;padding:0 24px 50px}}.eyebrow{{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;font-weight:700}}.links{{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;margin-top:20px}}nav{{position:sticky;top:0;background:var(--bg);z-index:3;display:flex;gap:22px;overflow:auto;padding:16px 0;border-bottom:1px solid var(--line)}}nav a{{white-space:nowrap;text-decoration:none;font-size:13px}}section{{padding-top:28px;scroll-margin-top:52px}}.card{{padding:21px;background:white;border:1px solid var(--line);border-radius:7px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:17px}}.architecture{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0}}.arch{{background:white;padding:18px;border-top:4px solid var(--teal)}}.arch ul{{padding-left:17px;font-size:13px}}.small{{font-size:12px}}.muted{{color:var(--muted)}}.label,dt{{font-size:11px;text-transform:uppercase;letter-spacing:.8px;font-weight:650;color:var(--muted);margin:16px 0 5px}}.tag{{display:inline-block;padding:3px 8px;background:#e2f1ec;color:#176453;border-radius:4px;font-size:11px;font-weight:650}}.note,.gate{{background:#edf5f4;padding:15px 18px;border-left:4px solid var(--teal);margin:18px 0}}.note p:last-child,.gate p:last-child{{margin:0}}ul{{padding-left:20px;margin:5px 0 13px}}li{{margin:5px 0}}.controls{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:18px 0}}input,select{{font:inherit;padding:10px 12px;border:1px solid #b9cbd5;border-radius:5px;background:white}}input{{min-width:280px;flex:1}}.product[hidden]{{display:none}}.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:6px;background:white}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:13px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}th{{font-size:11px;text-transform:uppercase;background:#e4edf2}}td p{{margin:6px 0 0}}details{{background:white;border:1px solid var(--line);border-radius:6px;margin:10px 0}}summary{{cursor:pointer;padding:16px 18px;font-weight:650}}summary .tag{{margin-left:12px}}.inside{{padding:0 18px 18px}}.refs{{font-size:12px;border-top:1px solid var(--line);padding-top:12px;margin-top:16px}}dd{{margin-left:0}}footer{{font-size:12px;color:var(--muted);border-top:1px solid var(--line);margin-top:28px;padding-top:16px}}@media(max-width:850px){{.architecture,.grid{{grid-template-columns:1fr}}header{{padding:28px 20px}}main{{padding:0 16px 35px}}h1{{font-size:28px}}}}@media print{{nav,.controls{{display:none}}.grid,.architecture{{display:block}}.card,.arch{{break-inside:avoid;margin-bottom:12px}}details{{display:block}}body{{background:white}}}}
</style></head><body><header><div class="eyebrow">Product strategy · Phase 4 · {esc(core['as_of'])}</div><h1>What to build, what to establish</h1><p>{esc(core['recommendation'])}</p><div class="links"><a href="amergis-product-roadmap.json" download>Structured roadmap</a><a href="amergis-api-reconstruction.html">API evidence</a><a href="amergis-operating-blueprint.html">Operating blueprint</a></div></header><main><nav aria-label="Roadmap navigation"><a href="#architecture">Architecture</a><a href="#products">Product portfolio</a><a href="#reconstruction">Reconstruction feasibility</a><a href="#sequence">Build sequence</a><a href="#discovery">Next discovery</a></nav>
<section id="architecture"><h2>One platform, three experiences</h2><p>{esc(core['planning_assumption'])}</p><div class="architecture">{architecture}</div><div class="note"><b>Operating scope</b><p>{esc(core['operating_limit'])}</p></div><h3>Choose authoritative records before connecting systems</h3><div class="table-wrap"><table><thead><tr><th>Record class</th><th>Proposed owner</th><th>Boundary</th></tr></thead><tbody>{records}</tbody></table></div></section>
<section id="products"><h2>Product portfolio</h2><p class="muted">These are recommended components of an independent operator. They are not recovered Amergis applications or a claim that all components require separate deployments.</p><div class="controls"><label for="product-query">Find a capability</label><input type="search" id="product-query" placeholder="e.g. credentials, payroll, client"><label for="decision-filter">Decision</label><select id="decision-filter"><option value="">All decisions</option>{''.join('<option>'+esc(x)+'</option>' for x in sorted(set(p['decision'] for p in products)))}</select><span id="product-count" class="small muted"></span></div><div id="product-grid" class="grid">{product_cards}</div><div class="card" style="margin-top:18px"><h3>ATS / CRM selection gate</h3><p>{esc(ats['default'])}</p>{items(ats['required_evidence'])}<p>{esc(ats['fallback'])}</p><p class="small muted">{esc(ats['vendor_status'])}</p></div></section>
<section id="reconstruction"><h2>What can be reconstructed</h2><p>Public extraction, independent behavioral design and vendor-specific compatibility require different evidence. A public endpoint list does not reveal production databases or all business rules.</p>{area_cards}<div class="note"><b>Not recoverable from the public evidence collected</b>{items(core['not_recoverable_from_public_evidence'])}</div></section>
<section id="state-examples"><h2>Illustrative workflow transitions</h2><p>These examples show how public observations become independent specifications. They are selected transitions, not complete or executable state graphs.</p>{state_cards}</section>
<section id="sequence"><h2>Release sequence with explicit exit conditions</h2><p class="muted">Sequence is a recommendation; dates, staffing and costs have not been estimated. Each release requires evidence before expanding agent authority.</p><div class="grid">{releases}</div></section>
<section id="discovery"><h2>The next discovery and build sprint</h2><div class="table-wrap"><table><thead><tr><th>Priority</th><th>Work and deliverable</th><th>Completion evidence</th></tr></thead><tbody>{sprint}</tbody></table></div><div class="note"><b>The next decision</b><p>Select the first service line, specialty, jurisdiction and client profile, then run the ATS/integration selection gate. Additional public website extraction will not resolve private configuration or supply a consented worker pool.</p></div></section><footer>{esc(core['scope_of_this_phase'])} Source research is dated October 20, 2026; historical vendor statements retain their original dates. Independent review status: {esc(review.get('status','pending'))}.</footer></main><script>
(()=>{{const q=document.getElementById('product-query'),s=document.getElementById('decision-filter'),cards=[...document.querySelectorAll('.product')];function filter(){{let n=0;for(const c of cards){{c.hidden=!(c.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!s.value||c.dataset.decision===s.value));if(!c.hidden)n++;}}document.getElementById('product-count').textContent=n+' of '+cards.length+' components';}}q.addEventListener('input',filter);s.addEventListener('change',filter);filter();}})();
</script></body></html>'''
(OUT/'amergis-product-roadmap.html').write_text(content)
assert products and areas
assert len({p['id'] for p in products})==len(products)
assert all(s in source_map for p in products+areas for s in p.get('source_ids',[]))
print(json.dumps({'products':len(products),'reconstruction_areas':len(areas),'review':review.get('status'),'output':'outputs/amergis-product-roadmap.html'}))
