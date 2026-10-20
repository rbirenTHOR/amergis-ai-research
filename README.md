# Amergis public research and AI operating blueprint

Public-source research collected on **October 20, 2026**, with an independent staffing operating model and a map of potential AI agent integrations.

Start with [the pilot market selection](outputs/school-therapy-pilot-selection.html), then [the school therapy requirements pack](outputs/school-therapy-requirements.html), [the digital product roadmap](outputs/amergis-product-roadmap.html) and [the API and reconstruction report](outputs/amergis-api-reconstruction.html). Download or clone this repository and open the HTML file locally; GitHub displays HTML source rather than executing the report.

## Deliverables

| Phase | Report | Structured data |
| --- | --- | --- |
| Public assessment | [HTML](outputs/amergis-public-assessment.html) | [Source map](outputs/amergis-source-map.json), [SQLite](outputs/amergis-public-intelligence.sqlite) |
| Operating blueprint | [HTML](outputs/amergis-operating-blueprint.html), [Excel workbook](outputs/amergis-operating-blueprint.xlsx) | [JSON](outputs/amergis-blueprint.json), [SQLite](outputs/amergis-phase2-intelligence.sqlite) |
| Portals and APIs | [HTML](outputs/amergis-api-reconstruction.html) | [JSON](outputs/amergis-api-reconstruction.json), [SQLite](outputs/amergis-api-reconstruction.sqlite) |
| Product roadmap | [HTML](outputs/amergis-product-roadmap.html) | [JSON](outputs/amergis-product-roadmap.json): build/establish decisions, reconstruction feasibility and release gates |
| School therapy requirements | [HTML](outputs/school-therapy-requirements.html) | [JSON](outputs/school-therapy-requirements.json): 43 requirements, 26 sources, 12 objects, 9 bounded state models and 26 proposed acceptance scenarios |
| Pilot market selection | [HTML](outputs/school-therapy-pilot-selection.html) | [JSON](outputs/school-therapy-pilot-selection.json): six-state comparison, 17 buyers, 70 source records, current entry routes and eligibility gates |
| Public offices | [61 normalized office records](outputs/amergis-public-locations.json) | Addresses, phones, public branch emails, service categories and preserved discrepancies |

The research includes 5,519 public listing observations, 20 role families, 63 proposed tasks, 12 workflow stages, six contract packets, and 12 platform/surface groups. Listing observations are not unique vacancies, placements or employee counts.

## Scope and evidence

Observed facts, historical supplier statements, vendor capabilities and proposed independent designs are distinguished in the reports. No authenticated tenant, private candidate or employee record, production schema or operational vendor API was accessed.

The blueprint is not a deployed staffing system. Exact Amergis configuration, permissions, rules and integration mappings remain unverified. Vendor documentation does not grant access to an Amergis tenant. The API report identifies applicable access conditions and unresolved dependencies.

The current requirements work targets **schools and therapists**, with SLP as a worked example and OT/PT differences recorded. The market screen recommends validating an in-person SLP pilot in **Rockland County, New York**, starting with East Ramapo and then Rockland BOCES. Frederick County, Maryland is a conditional ongoing-entry alternative. These are research priorities, not buyer commitments or a conclusion that this operator qualifies. Current deadlines are an October 20, 2026 snapshot; later addenda must be checked. Company readiness, clinician availability, actual orders and economics remain unverified.

District contract examples retain their dates and applicability; they are not adopted commercial terms. The staffing model preserves school-owned service records and separates approved service obligations, actual services, worked time and district billing. Clinical/IEP decisions and Medicaid claims are outside the initial product scope. The bounded domain model covers one provider/work block; broader school scenarios and eight dedicated case-design gaps are explicit. No interviews, outreach, registrations, bids, live integrations or operating-performance measurements were performed.

This repository contains curated findings, normalized public data, finished deliverables and report-build inputs. Raw portal bundles, HTTP headers/cookies, full downloaded reference pages and PDFs, raw job-description feeds, temporary files and installed packages are excluded. Source URLs and raw-feed SHA-256 hashes preserve provenance. Some historical evidence notes refer to original research files that are not distributed here.

No open-source license is granted to third-party source material. Source-specific rights and integration conditions remain applicable.

## Rebuild the HTML, JSON and SQLite reports

Requires Python 3.10+; these builders use the Python standard library and do not make network requests.

```sh
python3 work/amergis-audit/build_deliverables.py
python3 work/amergis-phase2/build_phase2.py
python3 work/amergis-phase3/build_report.py
python3 work/amergis-phase4/build_roadmap.py
python3 work/amergis-phase5/build_pack.py
python3 work/amergis-phase6/build_selection.py
```

Run in the listed order. The builds use the committed October 2026 evidence snapshot, not live data. The normalized public-office dataset is a committed input to phase 3.

## Check package consistency and report interactions

Requires Python 3.10+, Node.js 20+ and npm.

```sh
npm ci --ignore-scripts
npm run check
```

Checks exercise local DOM rendering, navigation, filtering, artifact links and selected evidence distinctions. The school requirements checks also validate source/trace references, state-graph consistency and artificial Decimal financial fixtures. Pilot-selection checks validate source and buyer references, snapshot dates and purchasing-route distinctions. They do not test an implemented staffing product, live integrations or clinical decisions, and do not replace rendered browser verification. Scenario acceptance tests are specified for future implementation; fixture checks do not execute those behaviors.

## Workbook

The reviewed `.xlsx` is included ready to use. Its optional source is `work/amergis-phase2/workbook/build.mjs`, which requires the Codex `@oai/artifact-tool` runtime. That runtime is not supplied or installed by this repository. Workbook validation evidence is retained in `work/amergis-phase2/workbook/verification.json`.

## Layout

- `outputs/`: user-facing reports, databases, workbook and datasets.
- `work/amergis-audit/`: phase 1 builder, normalized records and provenance.
- `work/amergis-phase2/`: operating model, curated evidence, template and checks.
- `work/amergis-phase3/`: API research, normalized CMS summary, template and checks.
- `work/amergis-phase4/`: product portfolio, reconstruction feasibility, release sequence and report builder.
- `work/amergis-phase5/`: school therapy requirements, primary-source evidence, domain specification, synthetic fixtures, traceability and independent review.
- `work/amergis-phase6/`: regional buyer research, credential/entity and buyer-risk evidence, conditional market selection, builder, checks and independent review.

The repository is private by default. It does not publish a website or enable GitHub Pages.
