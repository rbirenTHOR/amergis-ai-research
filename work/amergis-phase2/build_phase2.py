import collections
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from operating_model import AUTONOMY, STAGES, DATA_DOMAINS, RUNTIME, ROLLOUT, SCENARIOS

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
OUT = WORKSPACE / "outputs"

def read(path):
    return json.loads((ROOT / path).read_text())

roles = read("roles/roles.json")
tasks = read("roles/tasks.json")
agents = read("roles/agents.json")
role_summary = read("roles/summary.json")
software = read("roles/software_evidence.json")
quality = read("roles/data_quality_findings.json")
contracts = read("contracts/contracts.json")
rules = read("contracts/rules.json")
customer_rates = read("contracts/customer-rates.json")
contract_evidence = read("contracts/platform-process-evidence.json")
contract_notes = read("contracts/review-notes.json")
education = read("education/normalized-education-jobs.json")
reconciliation = read("education/reconciliation.json")
locations = read("platforms/locations.json")
platforms = read("platforms/platforms.json")
platform_workflows = read("platforms/workflow_evidence.json")
platform_coverage = read("platforms/coverage.json")
sunburst = read("platforms/sunburst_teletherapy.json")
controls = read("controls/controls.json")
phase1 = json.loads((OUT / "amergis-source-map.json").read_text())
healthcare = json.loads((WORKSPACE / "work/amergis-audit/normalized-jobs.json").read_text())
healthcare_meta = json.loads((WORKSPACE / "work/amergis-audit/public-jobs-feed.metadata.json").read_text())
healthcare_hash = json.loads((WORKSPACE / "work/amergis-audit/source-hashes.json").read_text())["files"]["public-jobs-feed.json"]

label_by_code = {x["code"]:x["label"] for x in AUTONOMY}
for t in tasks:
    t["autonomy_label"] = label_by_code[t["autonomy_class"]]
for a in agents:
    selected = [t for t in tasks if t["task_id"] in a["task_ids"]]
    a["task_count"] = len(selected)
    a["autonomy_counts"] = dict(collections.Counter(t["autonomy_class"] for t in selected))

counts = {
    "healthcare_listing_records":len(healthcare),
    "education_listing_records":len(education),
    "combined_listing_records":len(healthcare)+len(education),
    "listed_offices":len(locations["records"]),
    "office_states":locations["state_count"],
    "internal_job_advertisements":role_summary["public_postings"],
    "role_families":len(roles),
    "characterized_role_families":sum(bool(r["task_ids"]) for r in roles),
    "unresolved_role_families":sum(not bool(r["task_ids"]) for r in roles),
    "tasks":len(tasks),
    "task_autonomy":dict(collections.Counter(t["autonomy_class"] for t in tasks)),
    "agent_capability_groups":len(agents),
    "contract_packets":len(contracts),
    "contract_rules":len(rules),
    "customer_rate_rows":len(customer_rates),
    "sourcewell_ceiling_rates":148,
    "proposed_msp_tiers":3,
    "official_control_sources":len(controls["sources"]),
    "core_workflow_stages":len(STAGES),
}

coverage = [
    {"area":"Healthcare public feed","status":"Extracted snapshot","count":len(healthcare),"unit":"listing records","limits":"Includes 79 internal Field/Corporate advertisements; not unique vacancies, placements or employee headcount."},
    {"area":"Education public feed","status":"Extracted snapshot","count":len(education),"unit":"listing records","limits":"30 unclassified; repeated title/location groups retained; 42 state/DC codes. No matching IDs to healthcare snapshot."},
    {"area":"Office directory","status":"All rendered cards extracted","count":len(locations["records"]),"unit":"office URLs","limits":"32 states; only two full addresses and one service mix sampled. Homepage says over 70 offices; absolute footprint unresolved."},
    {"area":"Internal roles","status":"Snapshot classified","count":len(roles),"unit":"role families","limits":"19 characterized and one unresolved Staffing Analyst family. No inference of actual team sizes or full organization chart."},
    {"area":"Contracts","status":"Targeted sample extracted","count":len(contracts),"unit":"packets","limits":"Five customer packets plus cooperative master; not a census. Three documented initial terms have expired; renewals unverified."},
    {"area":"Rate data","status":"Published schedules extracted","count":148+len(customer_rates),"unit":"rate rows across different scopes","limits":"148 Sourcewell ceilings and 42 customer schedule rows. Do not combine as interchangeable prices or infer margins."},
    {"area":"Platform and workflow documentation","status":"Public documentation mapped","count":16,"unit":"documented/proposed workflow records","limits":"Historical guides, supplier claims and observed fields separated; authenticated tenant behavior not inspected."},
    {"area":"Private operational records","status":"Unavailable from public material","count":None,"unit":"","limits":"Candidate pool, client CRM, private credentials, transactions, internal SOPs and database schema remain unavailable."},
]

source_register = {}
def add_source(url, title="", kind="", date="", notes=""):
    if not url or not isinstance(url,str) or not url.startswith(("https://","http://")):
        return
    parts = urlsplit(url)
    canonical = urlunsplit((parts.scheme,parts.netloc,parts.path,parts.query,""))
    sid = "SRC-" + hashlib.sha256(canonical.encode()).hexdigest()[:12]
    if canonical not in source_register:
        source_register[canonical] = dict(source_id=sid,url=canonical,title=title or canonical,source_type=kind,evidence_date=date,notes=notes)
    return sid

for s in phase1["sources"]:
    add_source(s["url"],s["title"],s["evidence_type"],s["evidence_date"],s["limits"])
for s in platforms["sources"] + sunburst["sources"]:
    add_source(s["url"],s["title"],s.get("source_type",""),s.get("published_date") or "",s.get("limitations",""))
for s in controls["sources"]:
    add_source(s["url"],s["title"],s.get("type",""),s.get("source_date",""),"Selected official control source; scope specified per constraint.")
for c in contracts:
    add_source(c["source_url"],c["title"],"Public contract packet",c["source_date"],c["notes"])
for r in roles:
    for s in r["sources"]:
        add_source(s["url"],s.get("title",r["role_family"]),"Job responsibility observed in public search-index snapshot","2026-10-20","Detail URL from job card; individual detail page not necessarily fetched.")
for key in ("education_page_url","education_feed_url","education_search_url"):
    add_source(reconciliation[key],key.replace("_"," ").title(),"Observed public page/feed","2026-10-20")

summary_findings = [
    {"title":"Two public catalogs, separate identities","body":"The education feed adds 2,764 records to the earlier 2,755 healthcare records. No exact feed/position/slug/URL IDs overlap. Similar titles within each feed are retained as distinct observations.","source_urls":[reconciliation["education_feed_url"],healthcare_meta["url"]]},
    {"title":"Dated technology disclosure resolves part of the stack","body":"A June 2024 supplier proposal names eRecruit, MaxView, Certiphi and Nursys eNotify. The disclosure is reproduced in an executed 2026 packet, but is not proof of current deployment everywhere.","source_urls":[contract_evidence[0]["source_url"]]},
    {"title":"The contract is an operating input","body":"Time sources, approval routes, holidays and invoice clocks differ by customer. The future system needs versioned customer rules rather than one universal workflow.","source_urls":[c["source_url"] for c in contracts if c["contract_id"] in ("C02","C04","C06")]},
    {"title":"Unknown values need an owner","body":"A conversion-fee cell in the Santa Barbara agreement contains an hour range instead of a fee. An agent must suspend that calculation and route it for clarification.","source_urls":[r["source_url"] for r in rules if "140" in json.dumps(r) and r["contract_id"]=="C06"][:1]},
    {"title":"AI authority applies to tasks","body":"The 63 tasks use three proposed authority levels. These counts do not measure labor hours, savings or eliminated roles. One advertised role lacks enough duties to map.","source_urls":[]},
]

blueprint = {
    "title":"Amergis public data and AI operating blueprint",
    "as_of":"2026-10-20",
    "status":"Research blueprint and proposed independent design; not recovered Amergis SOP or a deployed operating system.",
    "scope":"AI-operated staffing administration with human professionals delivering regulated healthcare and education services.",
    "counts":counts,
    "findings":summary_findings,
    "autonomy":AUTONOMY,
    "workflow_stages":STAGES,
    "agent_groups":agents,
    "tasks":tasks,
    "roles":roles,
    "contracts":contracts,
    "contract_rules":rules,
    "customer_rates":customer_rates,
    "software_evidence":software,
    "contract_process_evidence":contract_evidence,
    "platforms":platforms,
    "platform_workflow_evidence":platform_workflows,
    "locations":locations,
    "controls":{"status":controls["status"],"constraints":controls["constraints"],"sources":controls["sources"],"shared_engineering_controls":controls["shared_engineering_controls"],"taxonomy_note":"This deliverable uses the unified A/B/C task rubric. Research-control A+B map to A with prerequisites; C maps to B; D maps to C."},
    "data_domains":[dict(domain=a,fields=b,design_rule=c,status="Inferred independent schema") for a,b,c in DATA_DOMAINS],
    "runtime":RUNTIME,
    "rollout":ROLLOUT,
    "acceptance_scenarios":[dict(test_id=a,scenario=b,expected=c,workflow_ids=d.split(","),status="Specified; not executed against a live system") for a,b,c,d in SCENARIOS],
    "coverage":coverage,
    "data_quality_findings":quality,
    "contract_review_notes":contract_notes,
    "platform_coverage":platform_coverage,
    "job_reconciliation":reconciliation,
    "sources":list(source_register.values()),
    "remaining_gaps":[
        "No full candidate or customer pool, private transactions or production schema can be reconstructed from these public sources.",
        "Office detail pages, the over-70-versus-61 count discrepancy and an exhaustive contract census remain incomplete.",
        "Amergis Connect launch/migration and actual current tenant capabilities remain unresolved.",
        "Posting title/body mismatches and one role with no duties prevent a complete organization chart.",
        "Hours per task, exception frequency, headcount, operating costs and verified outcomes are absent, so automation ROI is not estimated.",
        "The future operator needs its own clients, consented worker supply, professional authority, vendor connections and approved operating policies."
    ],
}

review_path = ROOT / "review.json"
if review_path.exists():
    blueprint["independent_review"] = json.loads(review_path.read_text())

OUT.mkdir(exist_ok=True)
(OUT/"amergis-blueprint.json").write_text(json.dumps(blueprint,indent=2))
db_path = OUT/"amergis-phase2-intelligence.sqlite"
if db_path.exists():
    db_path.unlink()
source_db = sqlite3.connect(OUT/"amergis-public-intelligence.sqlite")
db = sqlite3.connect(db_path)
source_db.backup(db)
source_db.close()

def create_table(name, rows):
    if not rows:
        return
    db.execute(f'DROP TABLE IF EXISTS "{name}"')
    columns=list(dict.fromkeys(k for row in rows for k in row))
    def field_type(key):
        values=[r.get(key) for r in rows if r.get(key) is not None]
        if values and all(isinstance(v,int) for v in values):
            return "INTEGER"
        if values and all(isinstance(v,(int,float)) for v in values):
            return "REAL"
        return "TEXT"
    db.execute(f'CREATE TABLE "{name}" ('+",".join(f'"{k}" {field_type(k)}' for k in columns)+")")
    def value(x):
        return json.dumps(x,ensure_ascii=False) if isinstance(x,(dict,list)) else x
    db.executemany(f'INSERT INTO "{name}" VALUES ('+",".join("?" for _ in columns)+")",[[value(r.get(k)) for k in columns] for r in rows])

all_jobs=[]
for catalog,records in [("healthcare",healthcare),("education",education)]:
    for r in records:
        row=dict(r)
        row["source_catalog"]=catalog
        row["record_key"]=catalog+":"+r["source_feed_id"]
        if catalog=="healthcare":
            row["source_url"]=healthcare_meta["url"]
            row["retrieved_at"]=healthcare_meta["retrieved_at"]
            row["source_sha256"]=healthcare_hash
            row["advertised_pay_unit"]=r["advertised_pay_raw"].rsplit("/",1)[-1].strip().lower()
            row["canonical_url"]=r["url"]
            row["city"]=r["location"].rsplit(",",1)[0].strip()
            m=re.search(r"(\d+)\s*weeks?",r["duration_raw"])
            row["duration_weeks"]=int(m.group(1)) if m else None
        all_jobs.append(row)
create_table("public_jobs",all_jobs)
db.execute("CREATE UNIQUE INDEX public_job_record_key ON public_jobs(record_key)")
db.execute("CREATE INDEX public_job_catalog ON public_jobs(source_catalog)")
for name,rows in [
    ("source_register",blueprint["sources"]),
    ("public_offices",locations["records"]),
    ("role_families",roles),("agent_tasks",tasks),("agent_groups",agents),
    ("customer_contracts",contracts),("contract_rules",rules),("customer_rate_schedules",customer_rates),
    ("software_evidence",software),("contract_process_evidence",contract_evidence),
    ("workflow_stages",STAGES),("data_domains",blueprint["data_domains"]),
    ("autonomy_controls",controls["constraints"]),("control_sources",controls["sources"]),
    ("coverage",coverage),("acceptance_scenarios",blueprint["acceptance_scenarios"]),
    ("role_data_quality",quality),
]:
    create_table(name,rows)
db.execute("INSERT INTO metadata(key,value) VALUES (?,?)",("phase2_status",blueprint["status"]))
db.execute("INSERT INTO metadata(key,value) VALUES (?,?)",("phase2_counts",json.dumps(counts)))
db.commit()
assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
assert db.execute("select count(*) from public_jobs").fetchone()[0]==5519
assert len({t["task_id"] for t in tasks})==len(tasks)==63
assert sum(r["public_posting_count"] for r in roles)==79
assert set(t["role_family_id"] for t in tasks) <= set(r["role_family_id"] for r in roles)
assert set(r["contract_id"] for r in rules) <= set(c["contract_id"] for c in contracts)
assert sum(counts["task_autonomy"].values())==63
db.close()

template=(ROOT/"blueprint_template.html").read_text()
embedded=json.dumps(blueprint,ensure_ascii=False).replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
document=template.replace("__BLUEPRINT_DATA__",embedded)
(OUT/"amergis-operating-blueprint.html").write_text(document)
print(json.dumps({"counts":counts,"unique_source_urls":len(source_register),"database":str(db_path),"html_bytes":len(document.encode())},indent=2))
