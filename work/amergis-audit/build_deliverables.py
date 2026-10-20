import hashlib
import html
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[1] / "outputs"
OUT.mkdir(exist_ok=True)
DATE = "2026-10-20"

sources = [
    ("S01", "Healthcare job board", "https://www.amergis.com/jobs/", "Observed HTML", "2026-10-20", "Displayed 2,751 results. Includes internal jobs; not a count of placements."),
    ("S02", "Public job-card feed", "https://www.amergis.com/wp-content/uploads/wmx-jobs/jobs.json?v=1792515708", "Retrieved JSON", "2026-10-20", "2,755 records. Referenced directly by the public jobs page."),
    ("S03", "Public job search index", "https://www.amergis.com/wp-content/uploads/wmx-jobs/jobs-search.json?v=1792515709", "Retrieved JSON", "2026-10-20", "2,755 keys, all matched to the job-card feed. Lowercased searchable descriptions; not an internal API."),
    ("S04", "Education job board", "https://www.amergiseducation.com/jobs/", "Observed HTML", "2026-10-20", "Displayed 2,764 results. Full education catalog not extracted or deduplicated against healthcare."),
    ("S05", "Locations", "https://www.amergis.com/about/locations/", "Observed HTML", "2026-10-20", "Office records, cities, states and published business phone numbers. Page has Load More; not assumed complete."),
    ("S06", "MaxView", "https://www.amergis.com/workforce-solutions/maxview/", "Product claim", "", "Public feature descriptions; authenticated business records not accessed."),
    ("S07", "MaxView feature guide", "https://www.amergis.com/resources/company-news/features-of-the-maxview-workforce-management-dashboard/", "Historical product guide", "2024-05-14", "Positions, submittals, assignments, shifts, timecards and reporting. Some features were roadmap items."),
    ("S08", "Per-diem workflow guide", "https://www.amergis.com/resources/company-news/looking-for-per-diem-shifts-how-maxview-jobs-can-help/", "Historical product guide", "2024-09-18", "Compliant existing applicants can be scheduled automatically; others go to a recruiter."),
    ("S09", "MaxView login", "https://mymaxview.com/", "Public login surface", "2026-10-20", "Account boundary; no login attempted."),
    ("S10", "MaxView Jobs Apple listing", "https://apps.apple.com/us/app/maxview-jobs-by-amergis/id1626499875", "Publisher listing", "2026-10-20", "Amergis seller and Bullhorn copyright are supplier clues, not proof of the full ATS or backend."),
    ("S11", "MaxView Jobs Google listing", "https://play.google.com/store/apps/details?id=com.maximstaffing.app&hl=en_US", "Publisher listing", "2026-10-20", "Public features and version information; legacy Maxim package name."),
    ("S12", "Amergis homepage", "https://www.amergis.com/", "Observed marketing page", "2026-10-20", "Amergis Connect heading and Coming soon label coexist with MaxView Jobs copy; transition unresolved."),
    ("S13", "Help Center", "https://www.amergis.com/help-center/", "Official support documentation", "2026-10-20", "ADP for pay documents/address; The Work Number for verification; recruiters/local offices handle employee support."),
    ("S14", "Sunburst VMS", "https://www.sunburstworkforce.com/vendor-management-system/", "Product claim", "", "Describes recommending VMS partners. Does not establish one proprietary Sunburst VMS."),
    ("S15", "Sunburst suppliers", "https://www.sunburstworkforce.com/suppliers/", "Public qualification criteria", "", "Supplier quality, compliance and responsiveness criteria; no complete supplier dataset obtained."),
    ("S16", "Sourcewell contract 061324-AMH", "https://www.sourcewell-mn.gov/cooperative-purchasing/061324-AMH", "Public procurement record", "2026-10-20", "Contract matures October 24, 2028. Pricing subject to change."),
    ("S17", "Sourcewell pricing workbook", "https://files.sourcewell.org/public/Shared%20Documents/Solicitations/10924/00006717/Additional%20Documents/Sourcewell%20Price%20List%20May%202026.xlsx", "Inspected workbook", "2026-05", "148 hourly not-to-exceed prices and three proposed MSP tiers. Not wages or realized margins."),
    ("S18", "Knox County contract packet", "https://public.destinyhosted.com/knoxdocs/2025/AGN/20250604_4922/17376_Contract_No._25-287%28b%29_Amergis_Healthcare_Staffing%2C_Inc..pdf", "Historical customer contract/proposal", "2025-03-13", "Client-specific workflow evidence; agreement July 2025–June 2026. PDF pages 46 and 65–70 particularly useful."),
    ("S19", "Clinical education role", "https://www.amergis.com/job/993081-rn-clinical-education-and-quality-improvement-lead-pueblo-co/", "Official role description", "2026-08-07", "Clinical interviews, facility training, trackers and follow-up; RN license required by posting."),
    ("S20", "Senior Proposal Developer", "https://www.amergis.com/job/953595-senior-proposal-developer-columbia-md/", "Official role description", "2026-04-10", "Bid analysis, SME interviews, reviews, staffing and implementation plans, BAFOs and templates."),
    ("S21", "Clinical Investigator", "https://www.amergis.com/job/955292-clinical-investigator-rn-educational-services-columbia-md/", "Official role description", "2026-04-16", "Incident intake, investigations, root-cause analysis, corrective action and risk reports."),
    ("S22", "National Recruitment Manager historical posting", "https://careers.amergis.com/job/859369-amergis-national-recruitment-manager-tampa-florida/", "Indexed historical role description", "2025-03-11", "Sourcing, qualification, negotiation, assignment and retention. Legacy URL may now redirect."),
    ("S23", "Time and Expense historical posting", "https://careers.amergis.com/job/877789-time-and-expense-field-support-specialist-i-los-angeles-california/", "Indexed historical role description", "2025-06-17", "Timecards, payroll/billing system entry, HQ handoff and revenue-cycle reconciliation. Vendor unnamed."),
    ("S24", "Privacy policy", "https://www.amergis.com/privacy-policy/", "Declared data categories", "2024-04-08", "Discloses applicant, education, credential, reference and payroll data categories; no actual records."),
    ("S25", "Client contact form", "https://www.amergis.com/contact/", "Observed form schema", "2026-10-20", "Company, location, staffing needs and consent fields. No submission made."),
    ("S26", "Teletherapy platform", "https://www.amergiseducation.com/teletherapy-platform/", "Product claim", "", "Virtual sessions, assessment integrations and session-activity reporting. Not independently tested."),
    ("S27", "Robots directives", "https://www.amergis.com/robots.txt", "Retrieved text", "2026-10-20", "Contains disallowed paths, a 10-second crawl delay and sitemap link. Duplicate agent groups; use conservative directives."),
    ("S28", "Sitemap index", "https://www.amergis.com/sitemap_index.xml", "Retrieved XML", "2026-10-20", "Eight sitemap categories. Locations child sitemap timed out; no full site count established."),
    ("S29", "MaxView demo form", "https://www.amergis.com/request-a-demo/", "Observed form schema", "", "Organization, industry, size and requested capabilities. No submission made."),
]
source_rows = [dict(zip(["id", "title", "url", "evidence_type", "evidence_date", "limits"], row)) for row in sources]

surfaces = [
    ("Public healthcare jobs", "Extracted", "S01,S02,S03", "IDs, title, geography, type, category, setting, advertised pay, duration, detail URL; searchable requirement text available", "Demand and recruiting-role catalog", "Feed and UI counts differ; preserve all ID namespaces."),
    ("Education jobs", "Sample inspected", "S04", "Titles, school disciplines, geography, pay units, contract length and requirements", "Education staffing demand", "Not yet fully extracted; do not sum with healthcare."),
    ("Office and geographic network", "Sample inspected", "S05,S28", "Office identity, address, business contact, local service mix", "Territory and delivery footprint", "Published offices are not internal headcount or all client locations."),
    ("MaxView client portal", "Public documentation inspected", "S06,S07,S09", "Feature descriptions, entities, status vocabulary, approval paths and reporting dimensions", "Client-side workflow specification", "No client records, current tenant screens or private APIs."),
    ("Candidate app", "Public documentation inspected", "S08,S10,S11", "Features, screenshots, release history, search fields and per-diem decision branch", "Candidate journey and eligibility rules", "No candidate profiles; Bullhorn attribution is a clue only."),
    ("Amergis Connect", "Announcement observed", "S12", "Public name and coming-soon status", "Track product transition", "Launch, migration and backend relationship unknown."),
    ("Payroll and verification", "Official routing documented", "S13", "ADP and The Work Number touchpoints; support ownership", "Integration and escalation requirements", "No employee or financial records accessed."),
    ("Sunburst MSP and VMS", "Public documentation inspected", "S14,S15,S16", "Supplier criteria, VMS partner role, procurement services", "Multi-vendor business model", "Vendor selection and deployment vary by client."),
    ("Public contracts and pricing", "Workbook extracted; packet reviewed", "S16,S17,S18", "Price ceilings, proposed MSP fees, contract scope, terms, invoice fields and customer-specific procedures", "Commercial rules and operating processes", "Ceilings are not actual rates, wages, margins or revenue."),
    ("Internal workforce roles", "Role samples and public catalog", "S19,S20,S21,S22,S23", "Responsibilities, handoffs, qualifications and explicit software mentions", "Task inventory for AI agents and human owners", "Job postings do not establish role staffing levels; legacy links may redirect."),
    ("Intake and data declarations", "Public forms/policy inspected", "S24,S25,S29", "Field names, purpose, consent and declared data classes", "Lead/candidate intake schema", "Policy categories are not database tables or accessible records."),
    ("Education teletherapy", "Public feature page inspected", "S26", "Session workflows, assessment brands, activity reporting", "Separate service line to scope", "Student/clinical records and underlying implementation unavailable."),
]
surface_rows = [dict(zip(["surface", "status", "source_ids", "extractable", "value", "limits"], r)) for r in surfaces]

concepts = [
    ("Organization / Worksite", "Clients, service locations and local operating requirements", "S05,S06,S18"),
    ("Contract / RateRule", "Effective dates, pay/bill rules, overtime, cancellation, conversion, timekeeping and approvals", "S16,S17,S18"),
    ("Requisition / Shift", "Discipline, location, schedule, requirements and demand status", "S01,S06,S08"),
    ("Professional / Credential", "Candidate qualifications, availability and verification/expiry status", "S08,S24"),
    ("Application / Submittal", "Candidate interest, screening and client decisions", "S06,S07"),
    ("OnboardingTask / Placement", "Requirements, sign-offs, assignment start and completion", "S07,S19"),
    ("Timecard / Approval", "Worked time, worksite clock source, acceptance and exceptions", "S07,S18,S23"),
    ("PayrollEntry / Invoice / Adjustment", "Separate payroll and customer-billing amounts and reconciliation", "S13,S18,S23"),
    ("Supplier / MSPProgram", "Participating vendors, fee rules and performance", "S14,S15,S17"),
    ("Incident / CorrectiveAction", "Clinical or service issue, investigation, owner and resolution", "S21"),
    ("RecruiterActivity / Proposal", "Sales pipeline, sourcing activity, bids, templates and approvals", "S20,S22"),
    ("Consent / Communication / AuditEvent", "Permissions, notices, communication and traceable decisions", "S24,S25"),
]
concept_rows = [dict(entity=a, purpose=b, source_ids=c, status="Inferred design; not recovered Amergis schema") for a,b,c in concepts]
backlog = [
    (1, "Reconcile job catalogs", "Extract education feed if publicly linked; deduplicate by preserved IDs and canonical URLs; separate internal and deployed roles.", "Daily snapshots only if later requested; current run is one-time."),
    (2, "Build contract rule matrix", "Compare multiple recent public agreements for approval routes, rates, overtime, cancellation, credential requirements and invoice terms.", "Record client, jurisdiction and effective dates for each rule."),
    (3, "Map workforce tasks", "Expand internal role catalog and map each task to inputs, outputs, decision rules, exception owner and KPI.", "Do not infer staffing levels from hiring advertisements."),
    (4, "Resolve current product state", "Cross-reference current guides, release notes and publicly available screenshots for MaxView and Connect.", "Authorized demos or supplied materials needed for nonpublic detail."),
    (5, "Define automation tests", "Test job normalization, eligibility checks, document completeness, scheduling constraints and invoice reconciliation on synthetic cases.", "Clinical and employment decisions retain accountable owners until separately justified."),
]
backlog_rows = [dict(priority=a, task=b, method=c, limitation=d) for a,b,c,d in backlog]

jobs = json.loads((ROOT / "normalized-jobs.json").read_text())
summary = json.loads((ROOT / "jobs-summary.json").read_text())
pricing = json.loads((ROOT / "sourcewell/sourcewell-inspection.json").read_text())
normalized_pricing = json.loads((ROOT / "sourcewell/normalized-pricing.json").read_text())
limitations = [
    "This is a public-source research database, not a copy of Amergis production systems.",
    "No access to candidate pool, customer CRM, credential documents, payroll, billing transactions, internal schemas or matching algorithms.",
    "Healthcare feed records, healthcare page totals and education page totals are separate observations; not unique vacancy, employee or placement counts.",
    "Public descriptions can be historical or aspirational. Documented client procedures can differ from advertised platform workflows.",
    "Public bill-rate ceilings and fee proposals do not establish realized prices, costs, profit margins or client revenue.",
    "Terms-of-use retrieval returned timeouts; no conclusion about bulk reuse permissions. Robots and rate directives require checking before a larger crawl.",
    "No logins, account creation, form submissions, security testing, private endpoint enumeration or scheduled monitoring were performed.",
]
report = {
    "title": "Amergis public-source intelligence: initial assessment",
    "as_of_date": DATE,
    "working_scope": "AI-operated staffing administration with human healthcare and education professionals delivering services; zero-human business feasibility not established.",
    "extraction_summary": summary,
    "public_pricing_summary": {k:v for k,v in pricing.items() if k not in ("sourcePath", "summary")},
    "sources": source_rows,
    "surface_inventory": surface_rows,
    "conceptual_entities": concept_rows,
    "next_extraction_priorities": backlog_rows,
    "limitations": limitations,
    "sample_jobs": jobs[:3],
}
(OUT / "amergis-source-map.json").write_text(json.dumps(report, indent=2))

db_path = OUT / "amergis-public-intelligence.sqlite"
if db_path.exists():
    db_path.unlink()
con = sqlite3.connect(db_path)
def table(name, rows):
    if not rows:
        return
    cols = list(rows[0])
    def sql_type(col):
        values = [r[col] for r in rows if r.get(col) is not None]
        if values and all(isinstance(v, int) for v in values):
            return "INTEGER"
        if values and all(isinstance(v, (int, float)) for v in values):
            return "REAL"
        return "TEXT"
    con.execute(f'CREATE TABLE "{name}" (' + ",".join(f'"{c}" {sql_type(c)}' for c in cols) + ")")
    con.executemany(f'INSERT INTO "{name}" VALUES (' + ",".join("?" for _ in cols) + ")", [[r.get(c) for c in cols] for r in rows])
table("sources", source_rows)
table("platform_surfaces", surface_rows)
table("conceptual_entities", concept_rows)
table("extraction_backlog", backlog_rows)
job_rows = [dict(r, source_id="S02", retrieved_at=summary["as_of"]) for r in jobs]
table("public_jobs", job_rows)
table("public_price_ceilings", [dict(r,source_id="S17",retrieved_on=DATE) for r in normalized_pricing["healthcare_pricing"]])
table("proposed_msp_fees", [dict(r,source_id="S17",retrieved_on=DATE) for r in normalized_pricing["msp_pricing"]])
con.execute("CREATE UNIQUE INDEX public_jobs_feed_id ON public_jobs(source_feed_id)")
con.execute("CREATE INDEX public_jobs_category ON public_jobs(job_category)")
con.execute("CREATE INDEX public_jobs_state ON public_jobs(state)")
metadata = {
    "purpose": "Independent public-source intelligence; not Amergis production database",
    "as_of": DATE,
    "job_feed_retrieved_at": summary["as_of"],
    "job_feed_sha256": json.loads((ROOT / "source-hashes.json").read_text())["files"]["public-jobs-feed.json"],
    "job_search_index_sha256": json.loads((ROOT / "source-hashes.json").read_text())["files"]["public-jobs-search.json"],
    "pricing_workbook_sha256": pricing["sha256"],
    "job_descriptions": "Public search index inspected but full copyrighted descriptions not redistributed in this database.",
    "limitations": json.dumps(limitations),
}
table("metadata", [dict(key=k,value=v) for k,v in metadata.items()])
con.commit()
assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
assert con.execute("SELECT count(*) FROM public_jobs").fetchone()[0] == 2755
assert con.execute("SELECT count(*) FROM public_price_ceilings").fetchone()[0] == 148
assert con.execute("SELECT count(*) FROM proposed_msp_fees").fetchone()[0] == 3
con.close()

esc = html.escape
src = {r["id"]:r for r in source_rows}
def refs(ids):
    return " · ".join(f'<a href="{esc(src[i]["url"], quote=True)}">{esc(src[i]["title"])}</a>' for i in ids.split(","))
inventory = "".join(f'<tr><td><b>{esc(r["surface"])}</b><br><span class="tag">{esc(r["status"])}</span></td><td>{esc(r["extractable"])}<p class="small">{refs(r["source_ids"])}</p></td><td>{esc(r["limits"])}</td></tr>' for r in surface_rows)
entities = "".join(f'<tr><td>{esc(r["entity"])}</td><td>{esc(r["purpose"])}</td></tr>' for r in concept_rows)
tasks = "".join(f'<li><b>{esc(r["task"])}.</b> {esc(r["method"])} <span class="muted">{esc(r["limitation"])}</span></li>' for r in backlog_rows)
limits = "".join(f'<li>{esc(r)}</li>' for r in limitations)
source_html = "".join(f'<li><a href="{esc(r["url"],quote=True)}">{esc(r["title"])}</a> <span class="muted">— {esc(r["evidence_type"])}; {esc(r["evidence_date"] or "publication date not established")}. {esc(r["limits"])}</span></li>' for r in source_rows)
document = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amergis public-source intelligence</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;color:#182a3a;background:#f4f7fa;margin:0}}main{{max-width:1120px;margin:auto;background:white;padding:45px}}h1{{font-size:36px;line-height:1.15}}h2{{margin-top:40px;font-size:23px}}.eyebrow,.muted{{color:#5d6b79}}.eyebrow{{letter-spacing:.12em;font-size:12px;text-transform:uppercase}}a{{color:#126a8b}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;vertical-align:top;border-bottom:1px solid #d8e1e8;padding:13px}}th{{background:#edf4f7}}.tag{{font-size:11px;color:#366a63}}.small{{font-size:12px}}.stats{{display:flex;gap:16px;flex-wrap:wrap}}.stats div{{background:#edf4f7;padding:18px 25px;flex:1}}.stats b{{display:block;font-size:28px}}.flow{{padding:20px;background:#edf4f7;border-left:4px solid #126a8b}}li{{margin:12px 0}}.notice{{border-left:4px solid #b68936;padding:10px 18px;background:#fff9ed}}@media(max-width:700px){{main{{padding:20px}}table{{font-size:12px}}th,td{{padding:8px}}}}@media print{{body{{background:white}}main{{padding:0}}h2{{break-after:avoid}}tr{{break-inside:avoid}}}}</style>
<main><div class="eyebrow">Initial research • October 20, 2026</div><h1>Amergis: what can be reconstructed from public evidence</h1>
<p>Public sources support a substantial reconstruction of products, job demand, commercial rules and operating workflows. They do not expose the private candidate/customer dataset or production database schema.</p>
<div class="stats"><div><b>2,755</b>job feed records extracted</div><div><b>148</b>hourly price ceilings inspected</div><div><b>3</b>proposed MSP fee tiers</div></div>
<p>Deliverables: <a href="amergis-public-intelligence.sqlite">Research SQLite database</a> · <a href="amergis-source-map.json">Structured source map</a></p>
<h2>What the initial extraction establishes</h2>
<p>The public jobs page directly references a job-card JSON file and a separate searchable text index. Both contained 2,755 records/keys, joined by the feed ID. The card feed exposes state, job type, category and setting plus rendered HTML containing title, pay, duration, location and URL. The database preserves the separate feed, position and URL identifiers. Full descriptions were inspected for availability but are not redistributed here.</p>
<p>The healthcare page displayed 2,751 results, while the education page displayed 2,764. Those observations are not reconciled, and the education catalog has not been fully extracted. The healthcare feed includes 1,567 Nursing, 540 Allied and 345 Aide records, plus other categories; 79 records are tagged Field or Corporate. These are listing categories, not workforce counts. <span class="small">{refs("S01,S02,S03,S04")}</span></p>
<p>The May 2026 pricing workbook provides 148 hourly not-to-exceed rates. Examples are $115/hour for Med/Surg RNs and $125/hour for school speech-language pathologists. Three proposed MSP tiers depend on projected client spending, with potential fees ranging from 3% to 5% across the bands. VMS fees and rebates are labeled as included, not additive. Exact $5M spend is not explicitly assigned a band. <span class="small">{refs("S16,S17")}</span></p>
<h2>Public platform and extraction map</h2><table><thead><tr><th>Surface and inspection status</th><th>Available evidence</th><th>Interpretation limits</th></tr></thead><tbody>{inventory}</tbody></table>
<h2>Operating workflow reconstructed from evidence</h2>
<div class="flow">Client demand → contract/requisition → sourcing and screening → candidate submission → client decision → credentialing/onboarding → placement and shifts → time capture → approval → payroll and invoicing → reconciliation, retention and exceptions</div>
<p>This is a synthesized functional model, not a claim about exact internal sequencing. The documented per-diem branch can schedule an existing compliant applicant automatically; candidates with outstanding requirements go to a recruiter. <span class="small">{refs("S07,S08,S22,S23")}</span></p>
<p>The Knox County packet is especially informative: it describes screening, training, file audits and invoice review, while its customer addendum prefers email and the customer's own timekeeping over a VMS. Consequently, the product design needs client-specific workflow configuration. This is a historical client example, not a universal Amergis procedure. <span class="small">{refs("S18")}</span></p>
<h2>Inferred database domains for an independent implementation</h2><p>These are design hypotheses grounded in public functions. They are not extracted Amergis tables.</p><table><thead><tr><th>Domain</th><th>Purpose</th></tr></thead><tbody>{entities}</tbody></table>
<h2>What “AI operated” needs to mean at this stage</h2>
<p>The working scope is AI-run staffing administration with human clinicians and educators delivering services. Candidate/job normalization, intake, scheduling assistance, document completeness and invoice reconciliation are promising test areas. The public evidence also includes clinical interviews, incident investigation, client approvals and exceptions, so fully autonomous operation remains a hypothesis to evaluate task by task. Accountable ownership of clinical, employment and financial decisions belongs in the design. <span class="small">{refs("S19,S21")}</span></p>
<h2>Next extraction priorities</h2><ol>{tasks}</ol>
<h2>Coverage and limitations</h2><ul>{limits}</ul>
<h2>Evidence register</h2><ol class="small">{source_html}</ol>
</main></html>"""
(OUT / "amergis-public-assessment.html").write_text(document)
print(json.dumps({"database":str(db_path),"jobs":len(jobs),"sources":len(source_rows),"surfaces":len(surface_rows),"report":str(OUT/"amergis-public-assessment.html")},indent=2))
