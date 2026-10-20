"""Independent operating design, grounded in but distinct from public evidence."""

AUTONOMY = [
    {"code": "A", "label": "Agent operates within rules", "definition": "Execute an explicitly delegated task after deterministic prerequisites pass. Retain source evidence, validation, audit history and an exception route."},
    {"code": "B", "label": "Agent prepares; person approves", "definition": "Prepare the recommendation or transaction. A named owner approves the exact version before a consequential action."},
    {"code": "C", "label": "Person leads; agent assists", "definition": "A qualified or authorized person performs judgment, professional activity or attestation. The agent assists with logistics and documentation."},
]

STAGES = [
    {
        "id":"W01","name":"Demand and account intake","owner":"Account management / sales",
        "observed_basis":"Public lead forms collect organization, location, job title and staffing needs. Sales roles qualify opportunities.",
        "agent_function":"Extract and deduplicate inquiries, identify missing fields, route by region and specialty, prepare account research.",
        "inputs":["Authorized inquiry","Organization and worksite facts","Approved service catalog"],
        "outputs":["Qualified lead record","Missing-information request","Opportunity owner"],
        "autonomy":"A","gate":"Approved intake channel and communication policy; business identity must be resolved.",
        "exception":"Unclear employer, unsupported service, sensitive content or conflicting locations → account owner.",
        "source_urls":["https://www.amergis.com/contact/"],
        "kpi":"Complete-intake rate; routing accuracy; elapsed time to owner assignment."
    },
    {
        "id":"W02","name":"Contract and commercial setup","owner":"Sales, finance and contracting",
        "observed_basis":"Public agreements establish customer-specific prices, timekeeping, approval and payment terms.",
        "agent_function":"Extract clauses into a versioned rule set, compare quote with approved bands, draft proposal and rate calculations.",
        "inputs":["Executed agreement and amendments","Customer requirement set","Approved cost assumptions"],
        "outputs":["Contract rule version","Quoted rate worksheet","Approval request"],
        "autonomy":"B","gate":"Contract authority and effective dates established; named owner approves nonstandard terms and signatures.",
        "exception":"Contradictory clauses, missing fees or uncertain units → contracting/finance. Do not select a convenient interpretation.",
        "source_urls":["https://www.sourcewell-mn.gov/cooperative-purchasing/061324-AMH"],
        "kpi":"Rule-extraction accuracy; unresolved term count; quote turnaround; exception rate."
    },
    {
        "id":"W03","name":"Requisition and requirements","owner":"Recruiting / client account team",
        "observed_basis":"Public job cards and MaxView documentation expose job, setting, shift, discipline and candidate requirements.",
        "agent_function":"Normalize orders, validate pay units and dates, resolve duplicate IDs and publish approved requisitions.",
        "inputs":["Approved client order","Current contract rule version","Worksite and discipline requirement matrix"],
        "outputs":["Versioned requisition","Eligibility rule set","Approved publication payload"],
        "autonomy":"A","gate":"Required fields complete and client order confirmed; no inferred wages, hours or clinical requirements.",
        "exception":"Conflicting IDs, unknown credentials, stale contract or missing pay units → recruiter/account owner.",
        "source_urls":["https://www.amergis.com/jobs/","https://www.amergiseducation.com/jobs/"],
        "kpi":"Requisition completeness; duplicate prevention; correction rate."
    },
    {
        "id":"W04","name":"Sourcing and engagement","owner":"Recruiting",
        "observed_basis":"Recruiter descriptions cover sourcing, database mining, contact, interviews and candidate relationship management.",
        "agent_function":"Search an authorized candidate pool, draft approved communications, collect availability and arrange interviews.",
        "inputs":["Consented candidate data","Approved outreach policy","Open requisition"],
        "outputs":["Contact history","Availability","Candidate interest","Interview appointment"],
        "autonomy":"B","gate":"A recruiter approves ranked prospects and proposed outreach at launch. Routine scheduling/reminders can later run under a separately approved policy.",
        "exception":"Opt-out, accommodation request, disputed identity or negative complaint → recruiter or HR.",
        "source_urls":["https://careers.amergis.com/job/859369-amergis-national-recruitment-manager-tampa-florida/"],
        "kpi":"Response and opt-out rates; qualified-interest rate; communication error rate."
    },
    {
        "id":"W05","name":"Matching and submission","owner":"Recruiter; clinical reviewer where applicable; client approver",
        "observed_basis":"MaxView supports submissions and client decisions. Clinical roles conduct pre-submission interviews.",
        "agent_function":"Assemble an evidence-based match, explain unmet requirements, prepare the submission and proposed terms.",
        "inputs":["Verified candidate facts","Requisition requirements","Candidate consent","Clinical assessment where required"],
        "outputs":["Match rationale","Submission package","Candidate/client decision records"],
        "autonomy":"B","gate":"Approved, job-related selection criteria; authorized submission; clinical/client approval remains distinct.",
        "exception":"Disputed exclusion, inferred sensitive traits, unsupported competency claim or accommodation → appropriate reviewer.",
        "source_urls":["https://www.amergis.com/workforce-solutions/maxview/","https://www.amergis.com/job/993081-rn-clinical-education-and-quality-improvement-lead-pueblo-co/"],
        "kpi":"Submission completeness; reviewer overturns; selection outcomes; time to client decision."
    },
    {
        "id":"W06","name":"Credentials and onboarding","owner":"Credentialing, HR and licensed clinical staff",
        "observed_basis":"Amergis documents credentialing/onboarding and names verification vendors in a public proposal.",
        "agent_function":"Track required documents, retrieve authorized verification evidence, monitor expiry, schedule checks and prepare forms.",
        "inputs":["Conditional-offer state as applicable","Permission for checks","Versioned credential requirements","Authoritative verification results"],
        "outputs":["Requirement checklist","Recorded clearance decision from authorized human owner (T063)","Expiry events","Attestation appointments"],
        "autonomy":"B","gate":"Separate consent, work authorization, professional authority and clinical suitability. T063's authorized human owner makes work-readiness clearance; this agent records that decision. Required examination/attestation is person-led.",
        "exception":"Name mismatch, restriction, adverse background result, medical question or missing practice authority → credential/HR/clinical owner.",
        "source_urls":["https://www.amergis.com/help-center/","https://www.amergis.com/resources/company-news/looking-for-per-diem-shifts-how-maxview-jobs-can-help/"],
        "kpi":"Verified-complete rate; expired/incorrect clearance incidents; time to readiness; exception age."
    },
    {
        "id":"W07","name":"Scheduling and coverage","owner":"Scheduling / account management",
        "observed_basis":"The per-diem guide documents automatic scheduling for existing compliant applicants; shift status vocabulary is published.",
        "agent_function":"Book eligible consenting workers, check conflicts and approved hour limits, confirm schedules and initiate coverage requests.",
        "inputs":["Current recorded clearance from T063 authorized human owner","Worker availability and consent","Client-approved shift","Contract limits"],
        "outputs":["Shift reservation","Confirmation","Schedule change event"],
        "autonomy":"A","gate":"All checks revalidated at booking; atomic reservation and idempotency prevent double booking.",
        "exception":"Expired credential, overtime exception, no-show, cancellation ambiguity or competing booking → scheduler/account owner.",
        "source_urls":["https://www.amergis.com/resources/company-news/looking-for-per-diem-shifts-how-maxview-jobs-can-help/","https://www.amergis.com/resources/company-news/features-of-the-maxview-workforce-management-dashboard/"],
        "kpi":"Fill rate with explicit denominator; double bookings; coverage response; schedule overrides."
    },
    {
        "id":"W08","name":"Time and expense","owner":"Time and expense / client supervisor",
        "observed_basis":"Public agreements use different time sources, supervisor approvals and multi-person verification.",
        "agent_function":"Import records, detect missing/overlapping time, calculate proposed hours and route approvals and corrections.",
        "inputs":["Approved timekeeping source","Worked-time records","Expenses","Contract and wage rules"],
        "outputs":["Time ledger","Exception queue","Client approval status","Payroll-ready data"],
        "autonomy":"A","gate":"Maintain original records and separate worker-pay obligation from customer invoice approval.",
        "exception":"Disputed time, missing shift evidence, conflicting clocks or deadline risk → payroll owner; no silent deletion of work.",
        "source_urls":["https://careers.amergis.com/job/877789-time-and-expense-field-support-specialist-i-los-angeles-california/"],
        "kpi":"Timecard correction rate; approval latency; unresolved hours before payroll cutoff."
    },
    {
        "id":"W09","name":"Payroll preparation","owner":"Payroll / finance",
        "observed_basis":"Public support material identifies payroll integration and time/expense roles describe payroll handoffs.",
        "agent_function":"Apply approved pay rules, reconcile batches, identify anomalies and prepare an authorization package.",
        "inputs":["Verified worked time","Approved pay terms","Employee payroll setup","Tax/payroll service calculations"],
        "outputs":["Reconciled payroll batch","Variance report","Release request"],
        "autonomy":"B","gate":"Proposed launch control: authorized payroll owner approves release. Calculation and release are separate privileges.",
        "exception":"Missing wages, unexplained variance, bank-detail change, disputed hours or duplicate batch → payroll/finance.",
        "source_urls":["https://www.amergis.com/help-center/"],
        "kpi":"Payroll accuracy; on-time payment; duplicate prevention; unresolved pay disputes."
    },
    {
        "id":"W10","name":"Billing and collections","owner":"Billing / revenue cycle / finance",
        "observed_basis":"Customer agreements vary in invoice frequency, approval triggers, supporting documents and payment timing.",
        "agent_function":"Calculate approved charges, generate contract-compliant invoices, reconcile receipts and send authorized reminders.",
        "inputs":["Approved billable time","Contract rule version","Client approval and supporting evidence","Payments"],
        "outputs":["Invoice draft or authorized standard invoice","Receivable ledger","Exception/credit proposal"],
        "autonomy":"A","gate":"Issue only within delegated limits after required approvals; rates and deadlines must be deterministically derived.",
        "exception":"Ambiguous conversion fee, disputed bill, nonstandard credit, missing approval or unmatched cash → billing/finance.",
        "source_urls":["https://www.sourcewell-mn.gov/cooperative-purchasing/061324-AMH"],
        "kpi":"Invoice first-pass acceptance; correction rate; overdue balance by contractual due date."
    },
    {
        "id":"W11","name":"MSP and supplier operations","owner":"Program / supplier management",
        "observed_basis":"Sunburst describes supplier qualification, VMS use and consolidated reporting; selected education material names MatterWorx.",
        "agent_function":"Route approved orders to qualified suppliers, monitor SLA/compliance evidence and prepare consolidated reporting.",
        "inputs":["Approved supplier roster","Client-specific distribution rules","VMS events","Fee schedule"],
        "outputs":["Order distribution","Supplier exceptions","Consolidated billing inputs","Program report"],
        "autonomy":"A","gate":"Use contracted VMS access and approved supplier eligibility; partner-specific integration semantics remain configurable.",
        "exception":"Vendor disqualification, disputed allocation, contract change or unresolved supplier invoice → program manager.",
        "source_urls":["https://www.sunburstworkforce.com/vendor-management-system/","https://www.sunburstworkforce.com/suppliers/"],
        "kpi":"Order response; supplier fill and quality measures; invoice reconciliation exceptions."
    },
    {
        "id":"W12","name":"Quality, incidents and retention","owner":"Clinical leadership, HR and account management",
        "observed_basis":"Clinical investigator and education roles describe incident investigation, follow-up, coaching and corrective actions.",
        "agent_function":"Capture reports, route urgency, organize evidence, track actions and prepare trend reports and renewal reminders.",
        "inputs":["Incident or service report","Assignment facts","Approved escalation policy","Clinical/HR assessment"],
        "outputs":["Owned incident case","Evidence chronology","Action tracker","Retention/renewal task"],
        "autonomy":"C","gate":"Urgent issues reach a staffed escalation route. People perform clinical judgment, investigation conclusions and discipline.",
        "exception":"Safety concern, allegation, medical interpretation, disputed conduct or threatened service interruption → qualified owner immediately.",
        "source_urls":["https://www.amergis.com/job/955292-clinical-investigator-rn-educational-services-columbia-md/"],
        "kpi":"Escalation latency; time to owned response; corrective-action closure; recurrence."
    },
]

DATA_DOMAINS = [
    ("Source and evidence","source_id, URL, publisher, retrieved_at, hash, page/row, evidence_status","Public evidence; supplier claims, observed fields and independent proposals are separate."),
    ("Organization and worksite","client_id, legal_entity, location, service_line, account_owner","New operator's authorized customer records; office directory does not establish Amergis customers."),
    ("Contract and rule version","contract_id, effective_dates, precedence, worksite, jurisdiction, rule_value, unit, evidence, approver","Ambiguous or missing rules block affected calculations."),
    ("Requisition and shift","order_id, source_ids, discipline, schedule, location, requirements_version, state","Keep source identifiers separate; no count-to-headcount conversion."),
    ("Professional and consent","person_id, identity, availability, consent_scope, contact_preference","Build a consented pool; public job feeds provide no candidate pool."),
    ("Credential and verification","credential_id, authority, person_match, scope, restrictions, expires_at, verified_at, evidence","Store source freshness and jurisdiction; OCR alone is not verification."),
    ("Application and submission","application_id, order_id, person_id, criteria_version, rationale, approvals","Track selection reasons and separate candidate/client decisions."),
    ("Onboarding and attestation","requirement_id, stage, responsible_actor, status, completed_at, proof","Medical and identity documents use restricted stores and role-specific access."),
    ("Assignment and booking","assignment_id, worker, client, terms_version, shift_id, reservation_key, state","Atomic booking and explicit cancellation transitions."),
    ("Time and expense","entry_id, original_time, source_clock, changes, worked_hours, approvals, dispute","Keep payroll and billing eligibility distinct."),
    ("Payroll and payment batch","pay_batch_id, rate_rule, hours, deductions, totals, approver, release_id","No model-only money movement; idempotent release and reconciliation."),
    ("Invoice and receivable","invoice_id, line_evidence, bill_rule, client_approval, due_trigger, credits, payments","Do not treat publication ceilings as negotiated transaction rates."),
    ("Supplier program","program_id, vendor_id, eligibility, distribution_rule, VMS, fee_version","Client-specific VMS and supplier contracts."),
    ("Incident and corrective action","case_id, urgency, evidence, owner, restricted_notes, decision, followup","AI assists with case administration; professional/HR judgments are owned."),
    ("Action, approval and audit","event_id, payload_hash, actor, model_version, policy_version, approval, outcome","Approvals bind to the exact action version; retries cannot duplicate actions."),
]

RUNTIME = [
    {"component":"Workflow engine","responsibility":"Own states, transitions, clocks, required evidence and exception routing. The language model cannot bypass a transition guard."},
    {"component":"Versioned policy and contract rules","responsibility":"Apply effective dates, jurisdiction, customer amendments, pay/bill units and rule precedence. Missing rules remain unknown."},
    {"component":"Permission-scoped agents","responsibility":"Agents receive only necessary data and explicit tool permissions. Draft, approve and release privileges are separate."},
    {"component":"Verified integrations","responsibility":"Use the future operator's authorized ATS/CRM, credential vendors, scheduling, payroll, VMS and communications. Public competitor documentation is not access authority."},
    {"component":"Action validation and idempotency","responsibility":"Validate payloads, consent, limits and freshness; reserve resources atomically; assign a unique key to each send, booking and payment."},
    {"component":"Approval and exception console","responsibility":"Show evidence, proposed action and deadline to a named owner; approval binds payload version; unresolved cases remain visible."},
    {"component":"Audit and quality measurement","responsibility":"Retain source and policy/model versions, decisions, interventions and outcomes; measure real errors and exception rates before increasing authority."},
]

ROLLOUT = [
    {"phase":"1. Evidence and schema","scope":"Consolidate public records and contracts; design the operator's own data model and synthetic test cases.","dependency":"Source provenance and customer-rule precedence.",
     "acceptance":"Every extracted rule has provenance and scope; ambiguous rules stay unresolved; listing IDs and pay units remain distinct.","authority":"Research and draft only."},
    {"phase":"2. Shadow workflow","scope":"Run intake, document tracking, matching recommendations and time/billing calculations against synthetic or authorized historical cases.","dependency":"Selected service line, state, client profile and approved criteria.",
     "acceptance":"All required positive, negative and exception scenarios produce the expected outcome; material disagreements are resolved by the relevant owner.","authority":"No external actions or financial release."},
    {"phase":"3. Bounded operating pilot","scope":"One client/worksite group, one state and one staffing specialty; delegate approved reminders, record updates and fully cleared shift bookings.","dependency":"Consented supply, client agreement, approved vendor connections and staffed exception queue.",
     "acceptance":"Correctness, response time and exception handling meet thresholds set by accountable owners; no unresolved critical test failures.","authority":"A tasks only within explicit delegation; B/C gates remain."},
    {"phase":"4. Controlled expansion","scope":"Add clients, specialties and jurisdictions only with tested rule packs and measured operating results.","dependency":"Stable pilot measurements and approved changes to limits.",
     "acceptance":"Replay regression cases, verify contract changes and monitor selection/pay/quality outcomes; rollback authority changes on failure.","authority":"Expand specific tasks, never infer whole-role removal from task counts."},
]

SCENARIOS = [
    ("T01","Same title and city, different source IDs","Keep separate listing observations; suggest review but do not merge as one vacancy.","W03"),
    ("T02","Weekly pay listing with no guaranteed hours","Preserve weekly unit; no invented hourly equivalent.","W03"),
    ("T03","Credential expired after approval but before booking","Recheck at booking and route unresolved eligibility; no assignment.","W06,W07"),
    ("T04","Two concurrent requests book the same worker","One atomic reservation succeeds; other is returned for alternate coverage.","W07"),
    ("T05","Background flag with no valid report permission","Block report ordering or downstream use as applicable; route permission/dispute workflow.","W06"),
    ("T06","Uploaded I-9 document but no required examination/attestation","Keep incomplete; schedule authorized representative step.","W06"),
    ("T07","Worked time exists but client invoice approval is missing","Keep worker-pay review active; separately hold the affected invoice action.","W08,W09,W10"),
    ("T08","Santa Barbara conversion fee cell contains an hour range, not a fee","Flag the contract defect; no inferred conversion charge; contracting owner resolves.","W02,W10"),
    ("T09","Holiday differs between two customer contracts","Use applicable contract version and effective dates, not a global holiday list.","W02,W08,W10"),
    ("T10","Retry occurs after invoice or payroll release succeeded","Idempotency key returns prior outcome; no duplicate transaction.","W09,W10"),
    ("T11","Candidate requests an accommodation","Route an accessible process and individualized reviewer; no automatic disqualification.","W04,W05"),
    ("T12","Incident report indicates urgent safety concern","Notify the staffed clinical route immediately; preserve evidence without AI deciding clinical action.","W12"),
    ("T13","Approval payload edited after sign-off","Invalidate prior approval and obtain approval for the changed version.","W02,W05,W09"),
    ("T14","Source says a product feature was planned in 2024","Keep historical-roadmap status until current release evidence is obtained.","W01"),
]
