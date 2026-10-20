"""Validate research/specification references and graph consistency, not product behavior."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'work/amergis-phase5'
OUT=ROOT/'outputs'

def read(path):
    return json.loads(path.read_text())

def unique(rows,key='id'):
    values=[r[key] for r in rows]
    assert len(values)==len(set(values)),f'Duplicate {key}'
    return set(values)

pack=read(OUT/'school-therapy-requirements.json')
domain=read(WORK/'domain-spec.json')
scenarios=read(WORK/'scenarios.json')
trace=read(WORK/'traceability.json')
plan=read(WORK/'discovery-plan.json')
checks=[]

for fname,key in [('discovery-plan.json','discovery_plan'),('local-care-evidence.json','district_evidence'),('obligations.json','obligations'),('integrations.json','integrations'),('domain-spec.json','domain_specification'),('scenarios.json','scenario_pack'),('traceability.json','traceability'),('review.json','independent_review')]:
    assert read(WORK/fname)==pack[key],f'Stale packaged input: {fname}'
checks.append('Pack matches the current curated source files')

source_ids=unique(pack['sources'])
req_ids=unique(pack['requirements'])
for s in pack['sources']:
    assert s['url'].startswith('https://'),s['id']
for r in pack['requirements']:
    assert set(r['source_ids'])<=source_ids,r['id']
    assert r['behavior'] and r['acceptance'] and r['evidence_status'],r['id']
assert set(trace['requirements'])==req_ids
checks.append('Requirement/source IDs resolve and every requirement has acceptance criteria and evidence status')

object_ids=unique(domain['objects'])
role_ids=unique(domain['roles'])
state_model_ids=unique(domain['state_models'])
fmt=domain['record_formats']
commands=[dict(zip(fmt['command_columns'],c)) if isinstance(c,list) else c for c in domain['commands']]
command_ids=unique(commands)
retention_ids=unique(domain['retention_policy_pointers'])
for raw in domain['commands']:
    if isinstance(raw,list):assert len(raw)==len(fmt['command_columns'])
for o in domain['objects']:
    fs=[]
    for f in o['fields']:
        if isinstance(f,list):
            assert len(f)==len(fmt['field_columns']),o['id']
            fs.append(dict(zip(fmt['field_columns'],f)))
        else:fs.append(f)
    field_names=unique(fs,'name')
    assert set(o.get('required_at_create',[]))<=field_names,o['id']
    assert o['retention_policy_ref'] in retention_ids,o['id']
for p in domain['permission_matrix']:
    assert p['role_id'] in role_ids
    assert set(p['object_ids'])<=object_ids
checks.append('Compact field/command schemas, object retention and role references are structurally valid')

transition_commands=[]
edge_count=0
for sm in domain['state_models']:
    states=set(sm['states']); terminals=set(sm['terminal_states'])
    assert len(states)==len(sm['states'])
    assert sm['object_id'] in object_ids
    assert sm['initial_state'] in states and terminals<=states
    edges={s:set() for s in states}
    for t in sm['transitions']:
        assert t['command_id'] in command_ids
        transition_commands.append(t['command_id'])
        assert set(t['actor_roles'])<=role_ids and t['actor_roles']
        assert set(t['from'])<=states and t['to'] in states
        assert not(set(t['from'])&terminals),sm['id']
        for field in ['prerequisites','evidence_required','output','on_exception']:
            assert t[field],(sm['id'],field)
        for start in t['from']:
            edges[start].add(t['to']);edge_count+=1
    def reachable(start):
        seen={start}; stack=[start]
        while stack:
            for nxt in edges[stack.pop()]-seen:
                seen.add(nxt); stack.append(nxt)
        return seen
    assert reachable(sm['initial_state'])==states,('Unreachable state',sm['id'])
    assert all(reachable(s)&terminals for s in states),('No terminal path',sm['id'])
assert len(transition_commands)==len(set(transition_commands))
assert set(transition_commands)==command_ids
checks.append('Every listed state is reachable; each has a terminal path; transitions resolve to unique command/role contracts')

scenario_ids=unique(scenarios['scenarios'])
journey_ids=unique(plan['journey'])
model_by_id={m['id']:m for m in domain['state_models']}
for s in scenarios['scenarios']:
    assert s['status']=='specified_not_executed',s['id']
    for ex in s.get('expected_states',[]):
        assert ex['model_id'] in state_model_ids
        assert ex['state'] in model_by_id[ex['model_id']]['states']
for r,links in trace['requirements'].items():
    assert set(links['object_ids'])<=object_ids,r
    assert set(links['journey_ids'])<=journey_ids,r
    assert set(links['scenario_ids'])<=scenario_ids,r
gaps={g['requirement_id'] for g in trace['dedicated_scenario_gaps']}
assert gaps=={r for r,v in trace['requirements'].items() if not v['scenario_ids']}
checks.append('Scenario state references and trace links resolve; dedicated case-design gaps are explicitly retained')

assert pack['scope']['user_selected']=='Schools and therapists'
assert all(m['threshold'] is None for m in scenarios['metrics'])
assert len(pack['requirements'])==pack['counts']['requirements']
assert len(scenario_ids)==pack['counts']['scenarios']
assert len(source_ids)==pack['counts']['source_records']
checks.append('Selected school-therapy scope and unmeasured pilot thresholds are preserved')

result={
    'status':'PASS — research package consistency only',
    'checks':[{'check':c,'status':'pass'} for c in checks],
    'counts':dict(pack['counts'],expanded_transition_edges=edge_count,dedicated_scenario_gaps=len(gaps)),
    'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(WORK.glob('*.json')) if p.name not in {'validation.json','report-checks.json'}},
    'limits':['No application, live API, actual employment/clinical decision or financial release tested.','Graph reachability does not prove the written guard semantics or a complete clinical workflow.','No jurisdiction-specific legal clearance, rendered-browser validation or observed operating ROI.']
}
(WORK/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
