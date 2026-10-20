import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/amergis-phase3"
OUT = ROOT / "outputs"

def read(rel):
    return json.loads((WORK / rel).read_text())

ats = read("ats/api-findings.json")
partners = read("partners/api-findings.json")
vms = read("vms/api-findings.json")
wp = read("portal/public-cms-summary.json")

sources = []
for group in [ats["sources"], partners["sources"], vms["sources"]]:
    for s in group:
        sources.append({"id": s.get("source_id", s.get("id")), "title": s["title"],
                        "url": s["url"], "basis": s.get("relevance", s.get("evidence_note", s.get("evidence_status", "")))})
root_sources = [
    ("PUB01", "Amergis WordPress REST index", "https://www.amergis.com/wp-json/",
     "Direct anonymous GET returned HTTP 200, 312 route patterns and 16 namespaces. A declared route is not proof anonymous operations are allowed."),
    ("PUB02", "Amergis public office collection", "https://www.amergis.com/wp-json/wp/v2/locations?per_page=100&_fields=id,date,modified,slug,link,title,content,acf,services,meta",
     "Direct anonymous GET returned 61 records; response headers total=61 and totalPages=1."),
    ("PUB03", "Amergis jobs page metadata", "https://www.amergis.com/wp-json/wp/v2/pages/6265?_fields=id,date,modified,slug,link,title,status,type,template,acf",
     "Direct anonymous GET returned published Jobs page 6265; this is CMS metadata, not ATS data."),
    ("PUB04", "MaxView portal", "https://mymaxview.com/",
     "Public browser reached username/password screen. HTML explicitly links a Clerk login bundle. No credentials submitted."),
    ("PUB05", "MaxView public login bundle", "https://mymaxview.com/dist/clerklogin.67914ce2d11b3a10230a.js?v=PsD5QBZb98XYl85QoGcpiEEbFE6zB7LF3vXZr6InM7A",
     "Directly linked browser code contains Clerk components, sign-in bridge and account-migration logic. No business endpoint contract established."),
    ("PUB06", "MaxView cookie notice", "https://mymaxview.com/cookie",
     "Official association with Amergis and ASP.NET session/antiforgery cookies. Does not establish a data model."),
    ("PUB07", "Healthcare job-card feed", "https://www.amergis.com/wp-content/uploads/wmx-jobs/jobs.json",
     "Previously retrieved site-declared static JSON; 2,755 observations in phase 1 snapshot."),
    ("PUB08", "Education job-card feed", "https://www.amergiseducation.com/wp-content/uploads/wmx-jobs/jobs.json",
     "Previously retrieved site-declared static JSON; 2,764 observations in phase 2 snapshot."),
    ("PUB09", "MaxView Jobs app listing", "https://apps.apple.com/us/app/maxview-jobs-by-amergis/id1626499875",
     "Public candidate-app capability description and publisher attribution; private mobile API unobserved."),
    ("PUB10", "MaxView product page", "https://www.amergis.com/workforce-solutions/maxview/",
     "Phase 2 public feature evidence; marketing is not an authenticated walkthrough."),
    ("PUB11", "Amergis homepage", "https://www.amergis.com/",
     "Phase 2 observation: Amergis Connect coming-soon naming appears alongside MaxView Jobs; migration relationship unresolved."),
    ("PUB12", "Amergis public service taxonomy", "https://www.amergis.com/wp-json/wp/v2/services?per_page=100&_fields=id,name,slug,count,link",
     "Direct anonymous GET returned HTTP 200 and five service taxonomy entries. Published categorization does not prove service availability."),
]
sources += [dict(id=i, title=t, url=u, basis=b) for i,t,u,b in root_sources]
SM = {s["id"]: s for s in sources}

def platform(pid, name, state, relationship, findings, objects, route, missing, agents, src):
    return dict(id=pid, name=name, access_class=state, amergis_relationship=relationship,
                observed=findings, domain_objects=objects, reconstruction_route=route,
                missing=missing, agent_groups=agents, source_ids=src)

platforms = [
    platform("P01", "Public websites and job feeds", "Public data verified",
        "Direct Amergis and Amergis Education public surfaces.",
        ["WordPress REST index verified: 312 declared route patterns across 16 namespaces. Administrative and write routes were not exercised.",
         "Published Jobs page metadata and all 61 records in the current public locations collection retrieved.",
         "Two site-declared static job-card/search feeds already extracted: 5,519 combined listing observations. These are snapshots, not unique vacancy or workforce counts."],
        ["CMS page", "Location", "Service taxonomy", "Public job listing"],
        "Build a read-only public-content importer and source/change ledger. Feed IDs, DOM position IDs and URL slug IDs must remain distinct.",
        ["Internal ATS-to-site publication mapping", "Refresh and deletion contract", "Reuse terms for any republished content", "Complete sitewide content extraction was not attempted in this phase"],
        ["AG06", "AG08"], ["PUB01","PUB02","PUB03","PUB07","PUB08","PUB12"]),
    platform("P02", "MaxView client portal", "Login reached; business API unknown",
        "Official Amergis client portal.",
        ["Browser verified the login form. Authenticated pages were not reached.",
         "Linked login bundle shows a Clerk identity integration, sign-in bridge and account-migration code paths.",
         "Cookie notice describes ASP.NET session and antiforgery cookies. Neither identity framework establishes business APIs or database schema."],
        ["Position", "Submittal", "Placement", "Shift", "Timecard", "Invoice/report (feature evidence)"],
        "Use public product behavior to design a client experience. Verify exact permissions and transitions later in a permitted synthetic-data demonstration.",
        ["Client/supplier/admin roles", "Supported integration API or export", "Data model and custom fields", "Approval transitions and current modules", "eRecruit field mapping"],
        ["AG01", "AG04", "AG09"], ["PUB04","PUB05","PUB06","PUB10"]),
    platform("P03", "MaxView Jobs / Amergis Connect", "App features; API unknown",
        "Amergis candidate app; Connect naming/migration unresolved.",
        ["App listing describes candidate-facing scheduling, onboarding and work/pay visibility.",
         "No supported mobile API specification, authenticated app workflow or Connect migration contract was recovered.",
         "Bullhorn attribution is a vendor clue; it does not identify Bullhorn ATS/CRM REST as the backend."],
        ["Candidate profile", "Application", "Onboarding item", "Availability", "Shift", "Time/pay view"],
        "Build an independent worker interface over the new operator's own workflow API.",
        ["Worker account and permitted demo", "Actual mobile backend", "Push/event delivery", "Eligibility and scheduling conflict logic"],
        ["AG01", "AG11"], ["PUB09","PUB11"]),
    platform("P04", "Erecruit WebAPI v2", "Vendor API documented",
        "Amergis named Erecruit in a June 2024 supplier proposal; current version/API enablement unverified.",
        ["Distinct API with OAuth client credentials, registered applications and administrator-selected endpoint permissions.",
         "Published examples cover candidate/resume intake, credential progress, requirements, onboarding and shifts.",
         "Full version-specific Swagger is tenant-hosted. Legacy XML RESTServices v1 is separate and retained in the research annex."],
        ["Candidate", "Contact", "Requirement", "CredentialingRequest", "Onboarding", "Shift", "Vendor"],
        "Highest-priority adapter candidate if the operator selects Erecruit. Obtain current Swagger and synthetic fixtures before writing a production connector.",
        ["Current build/modules", "Vendor/agency-approved test tenant", "Version-matched Swagger", "Endpoint permissions and entity scope", "Custom fields, statuses, rules and AI-use permission"],
        ["AG01", "AG11", "AG09"], ["PART02","er-overview","er-permissions","er-docs","er-usecase","er-admin32"]),
    platform("P05", "Bullhorn ATS/CRM REST", "Vendor API documented",
        "Alternative/reference product; Amergis use of this ATS API is not established.",
        ["Public entity and metadata references provide rich ATS concepts.",
         "OAuth authorization-code flow and BhRestToken differ from Erecruit.",
         "Event subscriptions are polled queues; consuming events purges returned items even though the call uses GET."],
        ["Candidate", "ClientCorporation", "JobOrder", "JobSubmission", "Placement", "RateCard", "CustomObject"],
        "Useful schema comparison or chosen-platform adapter. Do not substitute its endpoints for Erecruit or consume another integration's event queue.",
        ["Product relevance", "Contracted API/sandbox access", "Customer-specific data instructions", "Explicit permission for third-party AI/LLM use", "Tenant metadata and entitlements"],
        ["AG01","AG09","AG11"], ["bh-rest","bh-entities","bh-oauth","bh-events","bh-access","bh-policy"]),
    platform("P06", "ADP", "Vendor API documented",
        "Amergis Help Center routes employee paystubs/W-2s and address changes to ADP; product edition unknown.",
        ["Public product-specific worker, payroll input, time/labor and change-event documentation exists.",
         "Access uses provisioned credentials, OAuth and mutual SSL; client API Central or accepted partner arrangements apply.",
         "Current notification documentation supports queue polling and webhooks. Support varies by product/event."],
        ["Worker", "Work assignment", "Time entry", "Payroll input batch", "Change notification"],
        "Agent prepares and reconciles approved payroll inputs; an authorized payroll owner controls release. Choose edition before mapping fields.",
        ["Edition and API entitlement", "Client consent/scopes", "Certificates and credentials", "Test client", "Current earnings/deduction codes and payroll rules"],
        ["AG07","AG04"], ["PART01","PART03","PART05","PART06","PART07","PART08"]),
    platform("P07", "The Work Number / Equifax", "API product; schema gated",
        "Amergis confirms outbound employment/income verification service. Applicant-screening API usage is not established.",
        ["Equifax publishes a staffing-specific Talent Report product and OAuth/environment onboarding docs.",
         "Staffing endpoint reference requires sign-in; no product payload recovered.",
         "Registered developer sandbox uses mock data, subject to product eligibility."],
        ["Employment verification request", "Employment report", "Employer", "Title", "Employment dates"],
        "Keep employer data contribution and applicant verification as two separate adapters with separate purpose and authority.",
        ["Product contract and permitted purpose", "Developer schema/mock access", "Production credentialing", "Employer contribution specification if needed"],
        ["AG11","AG01"], ["PART01","PART10","PART11","PART12","PART13"]),
    platform("P08", "Certiphi / ATS Toolbox", "Integration advertised; schema unavailable",
        "Named in Amergis's June 2024 proposal; current configuration unknown.",
        ["Official ATS Toolbox explicitly lists erecruit compatibility.",
         "Front-end screening order and back-end report delivery are documented product capabilities.",
         "No public executable endpoint contract or sandbox found in the inspected sources."],
        ["Screening order", "Candidate ordering data", "Screening report"],
        "Define an order/status/result boundary; obtain vendor schema and test packages before implementing.",
        ["Integration agreement", "Protocol/auth/schema", "Screening package and status catalog", "Test environment", "Result delivery/retry behavior"],
        ["AG11"], ["PART02","PART14","PART15"]),
    platform("P09", "Nursys e-Notify", "API capability; schema gated",
        "Named for license monitoring in June 2024 Amergis proposal; API use unverified.",
        ["Current official documentation specifies JSON and institution Nurse List operations.",
         "Only enrolled licenses are available; no QuickConfirm API or SFTP.",
         "API URL/specification require institution-admin access. NCSBN states there is no separate sandbox or sample nurses."],
        ["Institution Nurse List", "Enrolled license", "Nurse report", "License-change notification"],
        "Agent reconciles enrollment and flags license changes. Credential clearance remains governed by the operator's policy and accountable owner.",
        ["Eligible institution account", "Administrator-requested credentials", "Current spec and URL", "Approved enrollment population and testing plan"],
        ["AG11","AG02"], ["PART02","PART16","PART17","PART18","PART19"]),
    platform("P10", "MatterWorx", "Open API advertised; spec unavailable",
        "Sunburst education offering names it; universal deployment not established.",
        ["Official pages advertise an open API and SSO.",
         "Linked login returned a Next.js shell over ordinary HTTP; research browser could not load it. No sign-in attempted.",
         "Support form names Worker, Hiring Manager, Recruitment Manager and Program Admin, with timesheet-import, invoice, vendor and settings issues.",
         "Support categories are not demonstrated permissions or actual database/API object names."],
        ["Job posting", "Application", "Assignment", "Timesheet", "Invoice", "Supplier", "Client", "Program setting"],
        "Public features support an independent MSP workflow design. Any authenticated evaluation must have a permitted scope given published competitive-use restrictions.",
        ["Permitted evaluation/integration scope", "Current API spec and provisioning", "Synthetic tenant", "Role matrix", "Events/imports/exports and reconciliation rules"],
        ["AG09","AG04"], ["VMS-S01","VMS-S02","VMS-S03","VMS-S05","VMS-S09","VMS-S11"]),
    platform("P11", "Sunburst MSP", "Program-specific platform unknown",
        "Amergis-affiliated MSP service; VMS choice varies by client.",
        ["General VMS page describes choosing partner platforms for client fit.",
         "Education offering explicitly names MatterWorx.",
         "No Sunburst-specific public API contract or supplier-portal enrollment was established."],
        ["MSP program", "Supplier", "Requisition distribution", "Submission", "Consolidated invoice"],
        "Model client program configuration separately from the VMS adapter; do not hard-code one vendor for every program.",
        ["Sample program's actual VMS", "Supplier onboarding", "Distribution/approval rules", "Fees and invoice format", "Supported integration channel"],
        ["AG09","AG04"], ["VMS-S10","VMS-S11"]),
    platform("P12", "Amergis Teletherapy Platform", "Capabilities only; interface unknown",
        "Amergis Education describes ATP as proprietary; backend vendor undisclosed.",
        ["Published features include rooms, waiting rooms, activity/minute reporting and assessment resources.",
         "No public API specification, portal/room endpoint, export schema or named video backend found.",
         "No-session-data-storage wording and activity-report retention boundary need explanation."],
        ["Room", "Session", "Therapy minute", "Completion", "Activity report"],
        "Design clinical administration and scheduling separately from clinical service delivery. Do not infer a video vendor or copy licensed assessment content.",
        ["Permitted clinician/admin demo", "Underlying platform", "API/export", "Retention/data flow", "Resource licenses and clinical handoffs"],
        ["AG02","AG06"], ["VMS-S12","VMS-S13"]),
]

lanes = [
    dict(id="L01", workflow="W01–W04 · Demand, requisitions and sourcing", interfaces=["P01","P04","P05"],
         agent="AG08 + AG01", now="Ingest published demand and normalize jobs, specialties, locations and source IDs. Draft requisitions and outreach.",
         later="Create/update the operator's requisitions and candidate records through the selected ATS under approved permissions.",
         proof="Synthetic duplicate candidate; missing requirement; corrected job; unpublished listing; source-ID collision."),
    dict(id="L02", workflow="W05 · Matching and submission", interfaces=["P04","P05","P10","P11"],
         agent="AG01 + AG09", now="Design eligibility checks and evidence-linked match explanations from the public role/requirement model.",
         later="Submit approved candidates to the correct client/vendor program; reconcile status changes.",
         proof="No double submission, cross-client disclosure or unsupported employment decision; approval binds to submitted version."),
    dict(id="L03", workflow="W06 · Credentials and onboarding", interfaces=["P04","P08","P09","P07"],
         agent="AG11", now="Define requirement bundles, document states, expiry rules and an exception work queue.",
         later="Track permitted screening orders, credential progress and enrolled-license changes.",
         proof="Expired license blocks readiness; screening mismatch goes to reviewer; vendor outage cannot imply clearance."),
    dict(id="L04", workflow="W07 · Scheduling and coverage", interfaces=["P02","P03","P04","P10"],
         agent="AG01 + AG09", now="Model availability, shift offers, confirmation and replacement escalation.",
         later="Book only within verified eligibility, client approval and worker acceptance rules.",
         proof="Concurrent shift offers, timezone changes, canceled placements, stale eligibility and double booking."),
    dict(id="L05", workflow="W08–W09 · Time and payroll", interfaces=["P02","P04","P06","P10"],
         agent="AG07 + AG04", now="Prepare canonical time-entry and pay-batch contracts with independent approval states.",
         later="Import approved time, reconcile payroll input and route variances to payroll owner.",
         proof="Late/edited timesheet, overtime, rejection, duplicate retry and reconciliation. Customer invoice dispute must not automatically withhold payroll."),
    dict(id="L06", workflow="W10–W11 · Billing and MSP", interfaces=["P04","P10","P11"],
         agent="AG04 + AG09", now="Apply scoped public contract rules and design client-specific invoice formats.",
         later="Generate draft invoices, reconcile acknowledged exports and route disputes with audit evidence.",
         proof="Effective-date rate changes, credit/rebill, missing approval, supplier split, failed delivery and duplicate export."),
    dict(id="L07", workflow="W12 · Service and clinical administration", interfaces=["P12","P09"],
         agent="AG02 + AG05", now="Design reminders, documentation completeness and incident routing.",
         later="Reconcile authorized session activity and credential alerts; escalate clinical and workforce case decisions.",
         proof="Data minimization, inconsistent activity counts, incident escalation and explicit clinical-owner handoff."),
]
requirements = [
    ("Identity", "Immutable IDs and cross-system aliases", "Public feed IDs do not reveal employee/client keys; tenant-scoped mapping is required."),
    ("Schema", "Field dictionary, types, required values and enums", "Vendor entity lists and REST indexes do not disclose Amergis custom fields or hidden fields."),
    ("Permissions", "Role × action × scope matrix", "Test candidate, recruiter, client, supplier, payroll and admin roles separately; support labels are insufficient."),
    ("Transitions", "Allowed states, prerequisites and side effects", "Record happy path plus withdraw, reject, reopen, cancel, correct and retroactive changes."),
    ("Rules", "Client/contract/role/jurisdiction configuration", "Rate, overtime, credential and approval rules must be versioned rather than inferred from one demonstration."),
    ("Events", "Delivery, retries, ordering, acknowledgement and replay", "A GET can consume a queue. Use a dedicated integration subscription and durable checkpoints."),
    ("Data movement", "Synthetic exports and representative payload fixtures", "Confirm attachment rules, imports, deletion, pagination, historical backfill and tenant boundaries."),
    ("Reconciliation", "Counts, totals, exception ownership and audit evidence", "Prove a complete synthetic candidate-to-invoice journey across system boundaries."),
]
backlog = [
    {"priority":"1 · Ready to implement", "deliverable":"Independent canonical model and fixture pack",
     "detail":"Use the existing 12-stage blueprint to specify Candidate, Client, Requisition, Requirement, Submission, Assignment, Shift, TimeEntry, PayrollBatch and Invoice. Labels are our design, not recovered Amergis tables."},
    {"priority":"2 · Ready to implement", "deliverable":"Public data adapter",
     "detail":"Read-only importer for published jobs and business-office metadata, with provenance, timestamps, aliases and change detection. Do not copy source prose into generated marketing."},
    {"priority":"3 · Access-dependent", "deliverable":"One selected ATS sandbox",
     "detail":"Obtain a permitted synthetic environment and current API contract. Choose Erecruit or another product; do not implement Bullhorn REST merely because the app credits Bullhorn."},
    {"priority":"4 · Access-dependent", "deliverable":"Credentialing and payroll integrations",
     "detail":"Provision selected Nursys/Certiphi/ADP products; map enrolled records, status codes and approved payroll batches. Use simulations until vendor testing conditions are resolved."},
    {"priority":"5 · Access-dependent", "deliverable":"Client/VMS and clinical interface validation",
     "detail":"Capture role-specific synthetic journeys and documented export/API behavior for an expressly permitted scope. Resolve MatterWorx terms and teletherapy retention before integration."},
    {"priority":"6 · Evidence-dependent", "deliverable":"Operational pilot",
     "detail":"Execute the prior blueprint's acceptance cases plus connector retries/reconciliation; set measurable error thresholds before granting each agent write authority."},
]
constraints = [
    {"title":"Bullhorn API use", "text":"Published API policy requires explicit permission for third-party AI/LLM API integration and customer-specific written instructions for provider access to customer data. Competing uses and transfers also have conditions. Applicable agreements may differ; this is not proof these exact terms govern Amergis's Erecruit contract.", "source_ids":["bh-policy","bh-access"]},
    {"title":"MatterWorx evaluation scope", "text":"Published terms restrict access for competitive reconstruction, reverse engineering and third-party credential sharing. A normal customer/demo login alone does not establish permission for this proposed use. Public feature analysis supports independent design.", "source_ids":["VMS-S09"]},
    {"title":"Actual access achieved", "text":"Only public website data, login surfaces and vendor documentation were accessed. No account was created, no credentials submitted, no vendor operational API invoked and no private candidate, employee, client or clinical records obtained.", "source_ids":["PUB01","PUB02","PUB04","VMS-S03"]},
]
public_routes = []
for path in ["/wp/v2/pages","/wp/v2/posts","/wp/v2/locations","/wp/v2/services","/wp/v2/categories","/wp/v2/tags","/wp/v2/search","/wp/v2/media","/wp/v2/landing-page"]:
    val=wp["routes"].get(path, {})
    public_routes.append({"path":path,"declared_methods":val.get("methods",[]),
                         "status":"Anonymous read verified" if path in ["/wp/v2/locations","/wp/v2/services"] else "Declared only (Jobs page detail verified separately)" if path=="/wp/v2/pages" else "Declared only; not requested"})
location_file=OUT/"amergis-public-locations.json"
locations = json.loads(location_file.read_text()) if location_file.exists() else None
review_file = WORK/"review/review.json"
review = json.loads(review_file.read_text()) if review_file.exists() else {"status":"Pending final independent review"}
data = {
    "title":"Amergis portal and API reconstruction map",
    "as_of":"2026-10-20",
    "status":"Public-interface discovery complete for the inspected surfaces; authenticated reconstruction not achieved",
    "conclusion":"Public interfaces and vendor docs support a detailed independent operating model. Exact Amergis compatibility and full internal reconstruction require tenant-specific schemas, configurations, permissions and test evidence that were not available.",
    "counts":{"surface_groups":len(platforms),"official_source_records":len(sources),"wordpress_declared_route_patterns":wp["route_count"],
              "wordpress_namespaces":len(wp["namespaces"]),"public_location_records":61,"authenticated_sessions":0},
    "platforms":platforms,"sources":sources,"agent_interface_lanes":lanes,
    "reconstruction_requirements":[dict(area=a,evidence=e,why=w) for a,e,w in requirements],
    "build_backlog":backlog,"access_conditions":constraints,"cms_route_examples":public_routes,
    "vendor_research":{"ats":ats,"partners":partners,"vms":vms},"public_locations":locations,"independent_review":review,
    "limits":["Bounded discovery, not proof that no other public API exists.",
              "No private system-of-record data or database DDL recovered.",
              "Endpoint templates in the research annex are vendor documentation examples, not verified Amergis URLs or executed calls.",
              "No production connectors, live AI operators or end-to-end staffing workflow were implemented in this phase.",
              "A functional recreation does not require copying vendor software; exact replica claims are not supported by these observations."],
}
OUT.mkdir(exist_ok=True)
(OUT/"amergis-api-reconstruction.json").write_text(json.dumps(data,indent=2,ensure_ascii=False))
template=(WORK/"report_template.html").read_text()
payload=json.dumps(data,ensure_ascii=False).replace("<","\\u003c")
(OUT/"amergis-api-reconstruction.html").write_text(template.replace("__REPORT_DATA__",payload))

db_path=OUT/"amergis-api-reconstruction.sqlite"
db_path.unlink(missing_ok=True)
con=sqlite3.connect(db_path)
con.execute("CREATE TABLE platforms (id TEXT PRIMARY KEY,name TEXT,access_class TEXT,relationship TEXT,details_json TEXT)")
con.execute("CREATE TABLE sources (id TEXT PRIMARY KEY,title TEXT,url TEXT,basis TEXT)")
con.execute("CREATE TABLE platform_sources (platform_id TEXT,source_id TEXT)")
con.execute("CREATE TABLE workflow_adapters (id TEXT PRIMARY KEY,workflow TEXT,agent TEXT,details_json TEXT)")
con.execute("CREATE TABLE public_locations (wp_id INTEGER PRIMARY KEY,office_name TEXT,page_url TEXT,details_json TEXT)")
con.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY,value TEXT)")
for p in platforms:
    con.execute("INSERT INTO platforms VALUES (?,?,?,?,?)",(p["id"],p["name"],p["access_class"],p["amergis_relationship"],json.dumps(p)))
    con.executemany("INSERT INTO platform_sources VALUES (?,?)",[(p["id"],s) for s in p["source_ids"]])
con.executemany("INSERT INTO sources VALUES (?,?,?,?)",[(s["id"],s["title"],s["url"],s["basis"]) for s in sources])
con.executemany("INSERT INTO workflow_adapters VALUES (?,?,?,?)",[(x["id"],x["workflow"],x["agent"],json.dumps(x)) for x in lanes])
if locations:
    con.executemany("INSERT INTO public_locations VALUES (?,?,?,?)",[(x["wp_id"],x["office_name"],x["page_url"],json.dumps(x)) for x in locations["records"]])
con.executemany("INSERT INTO metadata VALUES (?,?)",[("as_of",data["as_of"]),("status",data["status"])])
con.commit();con.close()

assert len(SM)==len(sources)
assert all(s in SM for p in platforms for s in p["source_ids"])
assert all(s in SM for p in constraints for s in p["source_ids"])
assert all(p in {x["id"] for x in platforms} for lane in lanes for p in lane["interfaces"])
assert wp["route_count"]==312 and len(wp["namespaces"])==16
print(json.dumps({"outputs":["amergis-api-reconstruction.html","amergis-api-reconstruction.json","amergis-api-reconstruction.sqlite"],"counts":data["counts"],"locations_included":bool(locations),"review_status":review.get("status")},indent=2))
