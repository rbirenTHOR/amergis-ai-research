"""Check research consistency; this does not verify eligibility or live opportunities."""
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/amergis-phase6'
pack = json.loads((ROOT / 'outputs/school-therapy-pilot-selection.json').read_text())
sources = {s['id']: s for s in pack['sources']}
districts = {d['id']: d for d in pack['districts']}
checks = []

assert len(sources) == len(pack['sources'])
assert len(districts) == len(pack['districts']) == pack['counts']['buyer_records']
assert pack['counts']['source_records'] == len(sources)
for s in sources.values():
    assert urlsplit(s['url']).scheme == 'https' and urlsplit(s['url']).netloc
checks.append('Unique IDs, source counts and HTTPS source structure')

def walk(obj):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k == 'source_ids':
                assert all(s in sources for s in v), v
            if k == 'source_id':
                assert v in sources, v
            if k == 'district_id':
                assert v in districts, v
            walk(v)
    elif isinstance(obj, list):
        for v in obj:
            walk(v)

walk(pack)
checks.append('All nested source and buyer references resolve')
as_of = date.fromisoformat(pack['as_of'])
for event in pack['calendar']:
    assert date.fromisoformat(event['date']) >= as_of
    assert event['source_ids']
    assert 'America/' in event['time']
checks.append('Action-calendar dates follow snapshot and state time zones')

assert districts['CHD03']['entry_class'] == 'Alternative model'
assert districts['MAD01']['entry_class'] == 'Standing entry · gated'
assert districts['TXD02']['entry_class'] == districts['TXD03']['entry_class'] == 'Unverified entry'
assert districts['TXD01']['entry_class'] == 'Open bid · conflict'
assert all(districts[i]['entry_class'] == 'Closed / awarded' for i in ['TXD04','SGD01','SGD02','SGD03','SGD04','SGD05','SGD06','MAD02','MAD04'])
checks.append('Closed, conflicted, unverified and non-staffing channels stay distinct')

assert len({s['state'] for s in pack['selection']['state_comparison']}) == 6
assert pack['selection']['priorities'][0]['district_id'] == 'CHD01'
assert pack['selection']['priorities'][2]['district_id'] == 'MAD01'
assert 'not bid-ready' not in pack['selection']['decision']['qualification']  # Readiness is unknown, not proved absent.
assert 'not a finding' in pack['selection']['decision']['qualification']
assert 'available candidates' in pack['selection']['workforce_context']['limit']
assert len(pack['selection']['workforce_context']['rows']) == 6
checks.append('Recommendation remains conditional and supply metric is scoped')
result = {'as_of': pack['as_of'], 'status':'pass', 'method':'Research-data consistency checks only; no current procurement, legal, clinical, credit or product validation.', 'checks': checks}
(WORK / 'validation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
