import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const inputDir = path.join(root, "work/amergis-phase2");
const scratch = path.join(inputDir, "workbook");
const outputPath = path.join(root, "outputs/amergis-operating-blueprint.xlsx");
const C = {
  navy: "#17324D", teal: "#007F82", light: "#F0F5F8",
  ink: "#172E43", muted: "#5B6D7C", line: "#CAD8E2",
  amber: "#FFF2CC", warning: "#FFF4E5", white: "#FFFFFF",
};
const wb = Workbook.create();
const sheets = {};
const checks = [];

function col(n) {
  let s = "";
  for (n++; n > 0; n = Math.floor((n - 1) / 26)) s = String.fromCharCode(65 + (n - 1) % 26) + s;
  return s;
}
function arr(v) { return Array.isArray(v) ? v : v == null ? [] : [v]; }
function text(v) { return arr(v).map(x => typeof x === "object" ? JSON.stringify(x) : String(x)).join("\n"); }
function safe(v) {
  if (typeof v === "number" || typeof v === "boolean" || v instanceof Date) return v;
  const t = text(v); return t.startsWith("=") ? "'" + t : t;
}
function lines(value, width) {
  return text(value).split("\n").reduce((sum, line) => sum + Math.max(1, Math.ceil(line.length / Math.max(8, Math.floor(width / 7.2)))), 0);
}
function base(name, title, subtitle, widths, rows) {
  const s = wb.worksheets.add(name); sheets[name] = s; s.showGridLines = false;
  const end = col(widths.length - 1);
  s.getRange(`A1:${end}${rows}`).format.font = { name: "Arial", size: 10, color: C.ink };
  s.getRange(`A1:${end}${rows}`).format.verticalAlignment = "center";
  widths.forEach((width, i) => s.getRange(`${col(i)}1:${col(i)}${rows}`).format.columnWidthPx = width);
  s.getRange(`A1:${end}1`).format.rowHeightPx = 16;
  s.getRange("A2").values = [[title]];
  s.getRange("A2").format.font = { name: "Arial", size: 16, bold: true, color: C.navy };
  s.getRange(`A2:${end}2`).format.rowHeightPx = 30;
  s.getRange("A3").values = [[subtitle]];
  s.getRange("A3").format.font = { name: "Arial", size: 10, italic: true, color: C.muted };
  s.getRange(`A3:${end}3`).format.borders = { bottom: { style: "thin", color: C.teal } };
  s.getRange(`A3:${end}3`).format.rowHeightPx = 27;
  return s;
}
function table(s, name, headers, rows, widths, start = 5, sourceCol = null) {
  const end = col(headers.length - 1);
  const last = start + rows.length;
  s.getRange(`A${start}:${end}${last}`).values = [headers, ...rows.map(row => row.map(safe))];
  s.getRange(`A${start}:${end}${start}`).format = {
    fill: C.navy, font: { name: "Arial", size: 10, bold: true, color: C.white },
    horizontalAlignment: "center", verticalAlignment: "center", wrapText: true,
    rowHeightPx: 36,
    borders: { insideVertical: { style: "thin", color: C.white } },
  };
  if (rows.length) {
    s.getRange(`A${start + 1}:${end}${last}`).format.wrapText = true;
    s.getRange(`A${start + 1}:${end}${last}`).format.verticalAlignment = "top";
    rows.forEach((row, idx) => {
      const r = start + idx + 1;
      const maxLines = Math.max(...row.map((cell, i) => i === sourceCol ? 2 : lines(cell, widths[i])));
      s.getRange(`A${r}:${end}${r}`).format.rowHeightPx = Math.max(45, maxLines * 15 + 13);
      if (idx % 2 === 1) s.getRange(`A${r}:${end}${r}`).format.fill = C.light;
    });
  }
  const t = s.tables.add(`A${start}:${end}${last}`, true, name);
  t.style = "TableStyleLight1";
  t.showFilterButton = true;
  s.freezePanes.freezeRows(start);
  s.freezePanes.freezeColumns(1);
  return last;
}
function header(s, address, label) {
  s.getRange(address).values = [[label]];
  s.getRange(address).format.font = { name: "Arial", size: 10, bold: true, color: C.teal };
  s.getRange(address).format.wrapText = true;
}
function link(s, address, url, label = "Public source") {
  if (url && /^https?:\/\//.test(url)) {
    s.getRange(address).values = [[label]];
    s.getRange(address).format.font = { name: "Arial", size: 10, color: C.teal };
    s.getRange(address).format.wrapText = true;
    s.getRange(address).format.verticalAlignment = "top";
    wb.notes.add({
      id: `${s.name}:${address}`,
      target: { cell: { sheetName: s.name, sheetId: s.sheetId, address } },
      authorId: "", createdAt: "", body: { plainText: `${label}\nSource: ${url}\nRetrieved: October 20, 2026` },
    });
  }
}
function sourceNote(s, address, sources, label) {
  s.getRange(address).values = [[label]];
  s.getRange(address).format.font = { name: "Arial", size: 10, color: C.teal };
  s.getRange(address).format.wrapText = true;
  s.getRange(address).format.verticalAlignment = "top";
  wb.notes.add({
    id: `${s.name}:${address}`,
    target: { cell: { sheetName: s.name, sheetId: s.sheetId, address } },
    authorId: "", createdAt: "",
    body: { plainText: sources.map(src => `${src.title || src.source_feed_id || label}\nSource: ${src.url}`).join("\n\n") + "\nRetrieved: October 20, 2026" },
  });
}
async function readJSON(rel) { return JSON.parse(await fs.readFile(path.join(inputDir, rel), "utf8")); }

const [roles, tasks, contracts, rules] = await Promise.all([
  readJSON("roles/roles.json"), readJSON("roles/tasks.json"),
  readJSON("contracts/contracts.json"), readJSON("contracts/rules.json"),
]);
const roleById = new Map(roles.map(r => [r.role_family_id, r]));
const mode = {
  A: "Agent operates within rules",
  B: "Agent prepares; person approves",
  C: "Person leads; agent assists",
};
const phase = {
  A: "1. Bounded operations",
  B: "2. Approval workflows",
  C: "3. Human-led services",
};
const counts = Object.fromEntries(["A", "B", "C"].map(k => [k, tasks.filter(t => t.autonomy_class === k).length]));
if (roles.length !== new Set(roles.map(r => r.role_family_id)).size) throw new Error("Duplicate role key");
if (tasks.length !== new Set(tasks.map(t => t.task_id)).size) throw new Error("Duplicate task key");
if (rules.some(r => !contracts.some(c => c.contract_id === r.contract_id))) throw new Error("Unmatched contract key");
if (tasks.some(t => !roleById.has(t.role_family_id) || !mode[t.autonomy_class])) throw new Error("Task mapping incomplete");

const summary = base("Summary", "Amergis operating blueprint", "Public evidence assessed October 20, 2026. Proposed agent design and review decisions are separate from observed duties.",
  [255, 100, 26, 90, 315, 95, 155], 34);
summary.tabColor = C.navy;
const taskWidths = [66, 190, 275, 180, 75, 190, 380];
const matrix = base("Agent tasks", "Agent task matrix", "A = operates within rules. B = person approves. C = person leads. Proposed authority is not Amergis policy.",
  taskWidths, tasks.length + 6);
matrix.tabColor = C.navy;
const reviewWidths = [66, 275, 190, 170, 170, 360, 175];
const review = base("Implementation review", "Implementation review", "Amber cells are editable. Complete the owner, decision and acceptance evidence for each task; review completion is not deployment completion.",
  reviewWidths, tasks.length + 6);
review.tabColor = C.teal;
const evidenceWidths = [66, 300, 210, 235, 230, 260, 210, 120];
const evidence = base("Task evidence", "Task evidence and proposed workflow", "Only public duties are observed; other fields are proposed. Source cells identify postings and retain full URLs in Excel notes.",
  evidenceWidths, tasks.length + 6);
const roleWidths = [66, 230, 85, 405, 230, 320, 360, 115];
const roleSheet = base("Role catalog", "Role families and public responsibilities", "Posting records are not headcount or verified vacancies. Families group advertised duties. Source cells retain full URLs in Excel notes.",
  roleWidths, roles.length + 6);
const ruleWidths = [66, 80, 125, 420, 330, 175, 125, 115];
const ruleSheet = base("Contract rules", "Customer-specific contract rules", "Rules apply only to the named contract; consult Contract catalog for customer, scope and dates. Source cells retain URLs in Excel notes.",
  ruleWidths, rules.length + 6);
const contractWidths = [66, 245, 470, 95, 95, 230, 95, 115];
const contractSheet = base("Contract catalog", "Public contract catalog", "Optional extensions are not assumed; ceilings are not realized spending. Source cells retain full document URLs in Excel notes.",
  contractWidths, contracts.length + 6);

const taskRows = tasks.map(t => [
  t.task_id, `${t.role_family_id}  ${t.role_family}`, t.task_name, t.proposed_ai_agent,
  t.autonomy_class, t.human_owner,
  `${t.decisions}\nReason: ${t.rationale}\nException: ${t.exception_route}`,
]);
const taskLast = table(matrix, "AgentTasks", ["Task ID", "Role family", "Task", "Proposed agent", "Mode", "Accountable human", "Decision boundary and exception"], taskRows, taskWidths);
matrix.getRange(`E6:E${taskLast}`).format.horizontalAlignment = "center";
for (const [code, fill] of [["A", "#DCEFED"], ["B", "#E8EEF5"], ["C", "#F0EBF5"]]) {
  matrix.getRange(`E6:E${taskLast}`).conditionalFormats.add("cellIs", { operator: "equal", formula: `"${code}"`, format: { fill, font: { bold: true, color: C.ink } } });
}
matrix.getRange(`E6:E${taskLast}`).dataValidation = { rule: { type: "list", values: ["A", "B", "C"] } };

const reviewRows = tasks.map(t => [t.task_id, t.task_name, phase[t.autonomy_class], "", "Not reviewed", "", ""]);
const reviewLast = table(review, "ImplementationReview", ["Task ID", "Task", "Proposed phase", "Named review owner", "Review decision", "Acceptance evidence / condition", "Review status"], reviewRows, reviewWidths);
review.getRange(`C6:F${reviewLast}`).format.fill = C.amber;
review.getRange(`C6:C${reviewLast}`).dataValidation = { rule: { type: "list", values: Object.values(phase) } };
review.getRange(`E6:E${reviewLast}`).dataValidation = { rule: { type: "list", values: ["Not reviewed", "Approved for pilot", "Needs changes", "Deferred"] } };
review.getRange("G6").formulas = [[`=IF(E6="Deferred","Deferred",IF(D6="","Assign owner",IF(E6="Not reviewed","Review decision",IF(F6="","Record acceptance evidence",IF(E6="Approved for pilot","Review complete","Resolve conditions")))))`]];
review.getRange(`G6:G${reviewLast}`).fillDown();
review.getRange(`G6:G${reviewLast}`).conditionalFormats.add("containsText", { text: "Assign owner", format: { fill: C.warning } });
review.getRange(`G6:G${reviewLast}`).conditionalFormats.add("containsText", { text: "Record acceptance", format: { fill: C.warning } });

const evidenceRows = tasks.map(t => [
  t.task_id, t.observed_public_duty, t.trigger, text(t.inputs), text(t.outputs),
  text(t.dependencies), text(t.kpi), t.sources.map(src => src.source_feed_id).join("\n"),
]);
table(evidence, "TaskEvidence", ["Task ID", "Observed public duty", "Proposed trigger", "Proposed inputs", "Proposed output", "Proposed dependencies", "Proposed KPI", "Source posting IDs"], evidenceRows, evidenceWidths);
tasks.forEach((t, i) => sourceNote(evidence, `H${i + 6}`, t.sources, t.sources.map(src => src.source_feed_id).join("\n")));

const roleRows = roles.map(r => [
  r.role_family_id, r.role_family, r.public_posting_count, text(r.observed_public_duties),
  text(r.observed_handoff_partners),
  r.explicit_system_mentions.length ? r.explicit_system_mentions.map(s => `${s.name}\n${s.evidence_scope}`).join("\n") : "No specific systems disclosed in reviewed descriptions.",
  r.limitations, `${r.sources.length} posting${r.sources.length === 1 ? "" : "s"}`,
]);
const roleLast = table(roleSheet, "RoleCatalog", ["Role ID", "Role family", "Posting records", "Observed public duties", "Observed handoffs", "System mentions and evidence scope", "Limitations", "Sources"], roleRows, roleWidths);
roleSheet.getRange(`C6:C${roleLast}`).format.numberFormat = "#,##0";
roleSheet.getRange(`C6:C${roleLast}`).format.horizontalAlignment = "right";
roles.forEach((r, i) => sourceNote(roleSheet, `H${i + 6}`, r.sources, `${r.sources.length} posting${r.sources.length === 1 ? "" : "s"}`));

const ruleRows = rules.map(r => [
  r.rule_id, r.contract_id, r.category.replaceAll("_", " "),
  `${r.summary}${Object.keys(r.parameters || {}).length ? "\nParameters: " + JSON.stringify(r.parameters) : ""}`,
  r.proposed_agent_control, r.human_exception_owner,
  `PDF p${r.pdf_page}\n${r.section || ""}`, `Rule ${r.rule_id}`,
]);
const ruleLast = table(ruleSheet, "ContractRules", ["Rule ID", "Contract ID", "Category", "Documented rule", "Proposed agent control", "Exception reviewer", "Document location", "Source"], ruleRows, ruleWidths);
rules.forEach((r, i) => link(ruleSheet, `H${i + 6}`, r.source_url, `Rule ${r.rule_id}`));

const date = d => d ? new Date(`${d}T12:00:00Z`) : null;
const contractRows = contracts.map(c => [
  c.contract_id, `${c.customer}\n${c.title}`, `${c.scope}\n${c.notes || ""}`,
  date(c.effective_start), date(c.effective_end),
  `${c.status_as_of_2026_10_20.replaceAll("_", " ")}\n${c.evidence_status.replaceAll("_", " ")}`,
  date(c.source_date), c.contract_id + " document",
]);
const contractLast = table(contractSheet, "ContractCatalog", ["Contract ID", "Customer and document", "Scope and term notes", "Term starts", "Term ends", "Status as of 10/20/26", "Source date", "Source"], contractRows, contractWidths);
contractSheet.getRange(`D6:E${contractLast}`).format.numberFormat = "mm/dd/yy";
contractSheet.getRange(`G6:G${contractLast}`).format.numberFormat = "mm/dd/yy";
contracts.forEach((c, i) => link(contractSheet, `H${i + 6}`, c.source_url, c.contract_id + " document"));

summary.getRange("A5:B10").values = [
  ["Evidence inventory", "Records"], ["Role families", null], ["Public internal postings", null],
  ["Mapped operating tasks", null], ["Public contract documents", null], ["Customer-specific rules", null],
];
summary.getRange("B6:B10").formulas = [
  [`=COUNTA('Role catalog'!A6:A${roleLast})`],
  [`=SUM('Role catalog'!C6:C${roleLast})`],
  [`=COUNTA('Agent tasks'!A6:A${taskLast})`],
  [`=COUNTA('Contract catalog'!A6:A${contractLast})`],
  [`=COUNTA('Contract rules'!A6:A${ruleLast})`],
];
summary.getRange("D5:F8").values = [
  ["Mode", "Proposed operating authority", "Tasks"],
  ["A", mode.A, null], ["B", mode.B, null], ["C", mode.C, null],
];
summary.getRange("F6:F8").formulas = [
  [`=COUNTIF('Agent tasks'!E6:E${taskLast},D6)`],
  [`=COUNTIF('Agent tasks'!E6:E${taskLast},D7)`],
  [`=COUNTIF('Agent tasks'!E6:E${taskLast},D8)`],
];
summary.getRange("D10").values = [["A requires approved inputs, authority, rules and exception routing."]];
summary.getRange("D11").values = [["B and C are proposed design choices; no universal legal rule is implied."]];
summary.getRange("D10:G11").format.font = { name: "Arial", size: 10, color: C.muted };
summary.getRange("A13:B17").values = [
  ["Implementation review", "Tasks"], ["Review complete", null], ["Awaiting review", null],
  ["Deferred", null], ["Total", null],
];
summary.getRange("B14:B17").formulas = [
  [`=COUNTIF('Implementation review'!G6:G${reviewLast},"Review complete")`],
  ["=B17-B14-B16"],
  [`=COUNTIF('Implementation review'!G6:G${reviewLast},"Deferred")`],
  [`=COUNTA('Implementation review'!A6:A${reviewLast})`],
];
summary.getRange("D13").values = [["Review sequence"]];
summary.getRange("D14").values = [["1. Validate the task boundary and customer-specific rules."]];
summary.getRange("D15").values = [["2. Assign an accountable owner in Implementation review."]];
summary.getRange("D16").values = [["3. Record a decision and measurable acceptance evidence."]];
summary.getRange("D17").values = [["4. Prove the workflow in a controlled pilot before expansion."]];
summary.getRange("A20").values = [["Interpretation"]];
summary.getRange("A21").values = [["Counts describe evidence and designed tasks. They do not measure employees, effort, savings or an automation percentage."]];
summary.getRange("A23").values = [["Source duties are paraphrased from public postings. Workflow triggers, agent roles, authority, owners and KPIs are proposed."]];
summary.getRange("A25").values = [["Contract rules are customer-specific. Historical documents remain useful process evidence but are not assumed current."]];
summary.getRange("A27").values = [["Source cells retain full URLs in Excel notes. Role catalog preserves technology mentions and their evidentiary limits."]];
summary.getRange("A29").values = [["The workbook supports review of a new operating model. It does not recover Amergis's private databases or prove full autonomy."]];
for (const r of ["A5:B5", "D5:F5", "A13:B13"]) {
  summary.getRange(r).format = { fill: C.navy, font: { name: "Arial", size: 10, color: C.white, bold: true }, rowHeightPx: 28, horizontalAlignment: "center" };
}
for (const r of ["A6:B10", "D6:F8", "A14:B17"]) {
  summary.getRange(r).format.rowHeightPx = 30;
  summary.getRange(r).format.borders = { bottom: { style: "thin", color: C.line } };
}
summary.getRange("B6:B10").format.numberFormat = "#,##0";
summary.getRange("F6:F8").format.numberFormat = "#,##0";
summary.getRange("B14:B17").format.numberFormat = "#,##0";
summary.getRange("A20").format.font = { name: "Arial", size: 10, bold: true, color: C.teal };
summary.getRange("D13").format.font = { name: "Arial", size: 10, bold: true, color: C.teal };
summary.getRange("A21:G30").format.rowHeightPx = 23;

// Verify review prerequisites without retaining the temporary inputs.
const status = () => review.getRange("G6").values[0][0];
review.getRange("E6").values = [["Approved for pilot"]];
wb.recalculate();
checks.push({ test: "Approval without owner is incomplete", value: status(), pass: status() === "Assign owner" });
review.getRange("D6").values = [["Test owner"]];
wb.recalculate();
checks.push({ test: "Owner and approval without evidence is incomplete", value: status(), pass: status() === "Record acceptance evidence" });
review.getRange("F6").values = [["Test acceptance evidence"]];
wb.recalculate();
checks.push({ test: "All review fields complete", value: status(), pass: status() === "Review complete" });
checks.push({ test: "Summary reacts to completed review", value: summary.getRange("B14").values[0][0], pass: summary.getRange("B14").values[0][0] === 1 });
review.getRange("D6").values = [[""]];
review.getRange("E6").values = [["Not reviewed"]];
review.getRange("F6").values = [[""]];

// Verify a mode edit updates the proposed task count, then restore it.
const originalMode = matrix.getRange("E6").values[0][0];
matrix.getRange("E6").values = [[originalMode === "A" ? "B" : "A"]];
wb.recalculate();
checks.push({
  test: "Task mode summary responds to edits",
  value: summary.getRange("F6").values[0][0],
  pass: summary.getRange("F6").values[0][0] === counts.A + (originalMode === "A" ? -1 : 1),
});
matrix.getRange("E6").values = [[originalMode]];
wb.recalculate();
const summaryCounts = summary.getRange("B6:B10").values.flat();
const expectedCounts = [roles.length, roles.reduce((s, r) => s + r.public_posting_count, 0), tasks.length, contracts.length, rules.length];
checks.push({ test: "Evidence counts reconcile", value: summaryCounts, expected: expectedCounts, pass: JSON.stringify(summaryCounts) === JSON.stringify(expectedCounts) });
checks.push({ test: "Mode counts reconcile", value: summary.getRange("F6:F8").values.flat(), expected: [counts.A, counts.B, counts.C], pass: JSON.stringify(summary.getRange("F6:F8").values.flat()) === JSON.stringify([counts.A, counts.B, counts.C]) });
checks.push({ test: "Review test inputs restored", value: summary.getRange("B14:B17").values.flat(), pass: summary.getRange("B14").values[0][0] === 0 && summary.getRange("B15").values[0][0] === tasks.length });
if (checks.some(c => !c.pass)) throw new Error(JSON.stringify(checks.filter(c => !c.pass)));

const inspect = await wb.inspect({ kind: "table", range: "Summary!A5:F17", include: "values,formulas", tableMaxRows: 13, tableMaxCols: 6, maxChars: 7000 });
await fs.writeFile(path.join(scratch, "summary-inspect.ndjson"), inspect.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 300 }, summary: "Final formula error scan" });
await fs.writeFile(path.join(scratch, "formula-errors.ndjson"), errors.ndjson);

const renderRanges = [
  ["Summary", "A1:G31", "summary"],
  ["Agent tasks", "A1:G11", "agent-tasks"],
  ["Agent tasks", "A32:G38", "agent-tasks-middle"],
  ["Implementation review", "A1:G12", "implementation-review"],
  ["Task evidence", "A1:H10", "task-evidence"],
  ["Role catalog", "A1:H9", "role-catalog"],
  ["Contract rules", "A1:H11", "contract-rules"],
  ["Contract rules", "A43:H49", "contract-rules-later"],
  ["Contract catalog", "A1:H11", "contract-catalog"],
];
await fs.mkdir(path.join(scratch, "previews"), { recursive: true });
for (const [sheetName, range, filename] of renderRanges) {
  const blob = await wb.render({ sheetName, range, scale: 1.5, format: "png" });
  await fs.writeFile(path.join(scratch, "previews", filename + ".png"), new Uint8Array(await blob.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(outputPath);
await fs.writeFile(path.join(scratch, "verification.json"), JSON.stringify({
  outputPath, counts: { roleFamilies: roles.length, sourcePostings: expectedCounts[1], tasks: tasks.length, contracts: contracts.length, rules: rules.length, autonomy: counts },
  checks, renderedSheets: Object.keys(sheets), formulaScan: errors.ndjson,
}, null, 2));
console.log(JSON.stringify({ outputPath, counts: expectedCounts, autonomy: counts, checks: checks.length, sheets: Object.keys(sheets) }));
