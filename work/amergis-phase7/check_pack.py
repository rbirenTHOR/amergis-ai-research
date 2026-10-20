"""Validate the planning package, not a live staffing operation or completed bid."""
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/amergis-phase7'
pack = json.loads((ROOT / 'outputs/east-ramapo-pilot-plan.json').read_text())
names = {'launch_core':'launch-core','bid':'bid-requirements','workforce':'workforce','insurance':'insurance','products':'products','economics':'economics'}
checks = []
for key,name in names.items():
    expected = json.loads((WORK / (name+'.json')).read_text())
    assert pack['modules'][key] == expected, key+' is stale'
checks.append('All six operating-plan modules match the curated inputs')

sources = {s['id']:s for s in pack['sources']}
assert len(sources) == len(pack['sources']), 'Duplicate source IDs'
refs_seen = set()
def walk(x):
    if isinstance(x, dict):
        for key,value in x.items():
            if key == 'source_ids':
                assert isinstance(value,list)
                for sid in value:
                    assert sid in sources, sid
                    refs_seen.add(sid)
            walk(value)
    elif isinstance(x,list):
        for value in x: walk(value)
walk(pack['modules'])
checks.append('Every module source reference resolves; repeated source URLs are not counted as unique evidence')

core,bid,insurance,products,economics = [pack['modules'][k] for k in ['launch_core','bid','insurance','products','economics']]
assert core['company_baseline']['confirmed_therapists'] == 0
assert core['company_baseline']['insurance'] == 'None confirmed'
assert 'not bid-ready' in core['status']
assert all(g['status'] not in ['Ready','Complete','Verified'] for g in core['readiness'])
assert datetime.fromisoformat(bid['procurement']['question_deadline']) < datetime.fromisoformat(bid['procurement']['submission_deadline'])
assert datetime.fromisoformat(bid['procurement']['submission_deadline']).isoformat() == '2026-10-30T12:00:00-04:00'
assert sum(bool(f['notary']) for f in bid['form_checklist']) == 3
assert len(bid['form_checklist']) == 9
assert all(p['quoted_amount'] is None and not p['district_confirmed_payable'] for p in bid['price_line_items'])
checks.append('User-confirmed startup gaps, current deadlines, notarizations and unquoted pricing remain explicit')

assert insurance['insurance_budget']['annual_premium_usd'] is None
assert insurance['insurance_budget']['deposit_usd'] is None
assert insurance['insurance_budget']['post_work_coverage_cost_usd'] is None
assert economics['status'] == 'planning_model_not_bid_quote'
assert 'submission deadline' in economics['scope']['invoice_note']
assert 'not payment Net 30' in economics['scope']['invoice_note']
checks.append('Unpriced insurance and illustrative economics cannot become actual quotes or payment terms')

cap_ids = {c['id'] for c in products['capabilities']}
for row in products['launch_acceptance_checks']:
    assert all(cid in cap_ids for cid in row['capability_ids'])
assert len(products['capabilities']) == 8
assert len(products['agent_matrix']) == 8
assert len(products['launch_acceptance_checks']) == 10
checks.append('Digital capability, agent and proposed acceptance coverage is structurally complete')

result = {'status':'pass','as_of':'2026-10-20','checks':checks,'limits':['Planning-package consistency only; no bid, vendor integration or live product acceptance test executed.','No clinician recruited, insurance bound, company formed or district assignment authorized by these checks.']}
(WORK / 'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
