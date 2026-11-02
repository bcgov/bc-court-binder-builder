/*
 * app.js
 * Purpose: Navigation and the three actions (create sample filings, build a
 *          binder, check a binder). Calls Python through window.pywebview.api.
 *          All dynamic text is set with textContent, never innerHTML.
 * Layer:   Application / UI
 */

const $ = (id) => document.getElementById(id);
const state = { buildFolder: "", checkFile: "", workspace: "", outputDir: "", saveDir: "", lastSuggested: "", createWork: "", createOut: "" };
const SVG_NS = "http://www.w3.org/2000/svg";
const ICONS = {
  success: "M5 13l4 4L19 7",
  warning: "M12 4l9 16H3zM12 10v4M12 17h.01",
  danger: "M6 6l12 12M18 6L6 18",
  info: "M12 8h.01M11 12h1v5h1",
};

// Build an element with optional class and text.
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// Build a small outline icon from a fixed path string.
function icon(kind) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", "verdict-icon");
  svg.setAttribute("aria-hidden", "true");
  const path = document.createElementNS(SVG_NS, "path");
  path.setAttribute("d", ICONS[kind]);
  svg.append(path);
  return svg;
}

// Build a button that runs a callback.
function button(label, className, onClick) {
  const btn = el("button", `btn ${className}`, label);
  btn.type = "button";
  btn.addEventListener("click", onClick);
  return btn;
}

// Build a result banner: icon, title, optional subtitle and action buttons.
function verdict(level, title, sub, actions = []) {
  const box = el("div", `verdict verdict-${level}`);
  box.setAttribute("role", level === "danger" ? "alert" : "status");
  const body = el("div", "verdict-body");
  body.append(el("h3", null, title));
  if (sub) body.append(el("p", "verdict-sub", sub));
  if (actions.length) {
    const row = el("div", "actions");
    row.append(...actions);
    body.append(row);
  }
  box.append(icon(level), body);
  return box;
}

// Buttons that open or reveal a created file.
function fileActions(path) {
  const api = window.pywebview.api;
  return [
    button("Open PDF", "btn-secondary btn-sm", () => api.open_file(path)),
    button("Show in folder", "btn-tertiary btn-sm", () => api.reveal(path)),
  ];
}

// Replace the contents of a result area.
function show(target, ...nodes) {
  target.replaceChildren(...nodes);
}

// Run an async action: disable the button, show progress, report failures.
async function withBusy(btn, target, message, action) {
  btn.disabled = true;
  const busy = el("div", "actions");
  busy.append(el("span", "spinner"), el("span", null, message));
  show(target, busy);
  try {
    await action();
  } catch (err) {
    show(target, verdict("danger", "Something went wrong", String(err)));
  } finally {
    btn.disabled = false;
  }
}

// Format a byte count for display.
function formatSize(bytes) {
  return bytes > 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : `${Math.round(bytes / 1024)} KB`;
}

// Render one quality gate as an expandable row.
function renderGate(check) {
  const kind = check.passed ? "pass" : check.severity === "HARD_STOP" ? "hard" : "soft";
  const label = { pass: "Passed", hard: "Hard stop", soft: "Advisory" }[kind];
  const item = el("li");
  const details = el("details", `gate gate-${kind}`);
  if (kind !== "pass") details.open = true;
  const summary = el("summary");
  summary.append(el("span", "gate-status", label), el("span", null, `Rule ${check.rule}: ${check.title}`));
  const body = el("div", "gate-body");
  body.append(el("p", null, check.details), el("p", null, `Authority: ${check.authority}`));
  if (!check.passed && check.remediation) body.append(el("p", "fix", `How to fix: ${check.remediation}`));
  details.append(summary, body);
  item.append(details);
  return item;
}

// Render a list of gates.
function gateList(checks, label) {
  const list = el("ul", "gates");
  list.setAttribute("aria-label", label);
  checks.forEach((c) => list.append(renderGate(c)));
  return list;
}

// Render a 20-segment meter, one block per gate.
function renderMeter(v) {
  const wrap = el("div", "meter-wrap");
  const meter = el("div", "meter");
  meter.setAttribute("aria-hidden", "true");
  v.checks.forEach((c) => meter.append(el("span", c.passed ? "" : c.severity === "HARD_STOP" ? "hard" : "soft")));
  const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
  const text = `${v.passed_count} of ${v.total} gates passed · ${plural(v.hard_stops, "hard stop")} · ${plural(v.soft_warnings, "advisory").replace("advisorys", "advisories")}`;
  wrap.append(meter, el("p", "meter-label", text));
  return wrap;
}

// Render the validation verdict, meter, problems first, then passed gates.
function renderValidation(v, actions = []) {
  const nodes = [verdict(v.level, v.verdict, v.file, actions), renderMeter(v)];
  const rank = (c) => (c.severity === "HARD_STOP" ? 0 : 1);
  const problems = v.checks.filter((c) => !c.passed).sort((a, b) => rank(a) - rank(b));
  const passed = v.checks.filter((c) => c.passed);
  if (problems.length) {
    nodes.push(el("h3", "group-title", `Needs attention (${problems.length})`), gateList(problems, "Gates needing attention"));
  }
  const group = el("details", "passed-group");
  group.append(el("summary", null, `Passed gates (${passed.length})`), gateList(passed, "Passed gates"));
  group.open = problems.length === 0;
  nodes.push(group);
  return nodes;
}

// Feature 1: generate sample filings and run the full cycle.
async function runCreate() {
  const target = $("result-create");
  const res = await window.pywebview.api.run_full_cycle(state.createWork, state.createOut);
  if (!res.ok) return show(target, verdict("danger", "Could not create sample filings", res.error));
  const pdf = res.assembled.output_pdf;
  const summary = `${res.generated.document_count} filings saved in ${res.run_dir}. ${formatSize(res.assembled.size_bytes)} binder saved in ${res.output_dir}.`;
  show(target, verdict("info", "Sample run complete", summary, fileActions(pdf)), ...renderValidation(res.validation));
}

const CASE_INPUTS = {
  court: "cd-court", registry: "cd-registry", file_number: "cd-file-number", plaintiff: "cd-plaintiff",
  defendant: "cd-defendant", application_date: "cd-date", time_estimate: "cd-time",
  counsel_applicant: "cd-counsel-applicant", counsel_respondent: "cd-counsel-respondent",
};

// Read the case details form.
function collectCaseDetails() {
  const details = {};
  Object.entries(CASE_INPUTS).forEach(([field, id]) => { details[field] = $(id).value; });
  return details;
}

// Fill the case details form from the folder's manifest (or empty defaults).
async function loadCaseDetails(folder) {
  const res = await window.pywebview.api.case_details(folder);
  if (!res.ok) return;
  Object.entries(CASE_INPUTS).forEach(([field, id]) => { $(id).value = res[field] || ""; });
  document.querySelectorAll("[data-title-only]").forEach((node) => { node.hidden = Boolean(res.has_cover_file); });
  $("cover-note").hidden = !res.has_cover_file;
  $("case-details").hidden = false;
}

// Keep the suggested file name in step with the hearing date until the user edits the name.
async function refreshSuggestedName() {
  if (!state.buildFolder || $("build-name").value !== state.lastSuggested) return;
  state.lastSuggested = await window.pywebview.api.suggest_binder_name(state.buildFolder, $("cd-date").value);
  $("build-name").value = state.lastSuggested;
}

// Feature 2: build a binder from the chosen folder.
async function runBuild() {
  const target = $("result-build");
  const res = await window.pywebview.api.assemble(state.buildFolder, $("build-name").value, state.saveDir, collectCaseDetails());
  if (!res.ok) return show(target, verdict("danger", "Could not build the binder", res.error));
  const sub = `${res.output_pdf} (${formatSize(res.size_bytes)})`;
  const checkNow = button("Check this binder", "btn-primary btn-sm", () => {
    setPicked("check", res.output_pdf);
    selectTab($("tab-check"));
    $("run-check").click();
  });
  const notices = (res.warnings || []).map((w) => verdict("warning", "Review before filing", w));
  show(target, verdict("success", "Binder built", sub, [...fileActions(res.output_pdf), checkNow]), ...notices);
}

// Feature 3: validate the chosen PDF.
async function runCheck() {
  const target = $("result-check");
  const res = await window.pywebview.api.validate(state.checkFile);
  if (!res.ok) return show(target, verdict("danger", "Could not check the binder", res.error));
  show(target, ...renderValidation(res, fileActions(res.file)));
}

// Record a picked path and update its picker and the matching button.
function setPicked(kind, path) {
  const isBuild = kind === "build";
  state[isBuild ? "buildFolder" : "checkFile"] = path;
  $(isBuild ? "build-folder" : "check-file").textContent = path;
  $(isBuild ? "build-picker" : "check-picker").classList.add("has-value");
  $(isBuild ? "run-build" : "run-check").disabled = false;
}

// Show what the chosen folder contains.
async function previewFolder(path) {
  const meta = $("build-meta");
  const res = await window.pywebview.api.inspect_folder(path);
  if (!res.ok) return (meta.textContent = res.error);
  const parts = [`${res.pdf_count} PDF${res.pdf_count === 1 ? "" : "s"}`];
  if (res.txt_count) parts.push(`${res.txt_count} text file${res.txt_count === 1 ? "" : "s"}`);
  if (res.has_cover_file) parts.push("your own cover page found");
  parts.push(res.has_manifest ? "manifest.json found" : "no manifest.json (order is inferred from file names)");
  meta.textContent = parts.join(" · ");
}

// Pick the folder of filings.
async function pickFolder() {
  const chosen = await window.pywebview.api.pick_folder();
  if (!chosen) return;
  setPicked("build", chosen);
  state.saveDir = "";
  state.lastSuggested = await window.pywebview.api.suggest_binder_name(chosen);
  $("build-name").value = state.lastSuggested;
  await loadCaseDetails(chosen);
  $("save-folder").textContent = await window.pywebview.api.default_binder_dir(chosen);
  $("save-picker").classList.add("has-value");
  await previewFolder(chosen);
}

// Choose a different folder to save this binder in.
async function pickSaveDir() {
  const chosen = await window.pywebview.api.pick_folder();
  if (!chosen) return;
  state.saveDir = chosen;
  $("save-folder").textContent = chosen;
  $("save-picker").classList.add("has-value");
}

// Choose a different folder for this run's sample filings.
async function pickCreateWork() {
  const chosen = await window.pywebview.api.pick_folder();
  if (!chosen) return;
  state.createWork = chosen;
  $("create-work-folder").textContent = chosen;
}

// Choose a different folder for this run's binder.
async function pickCreateOut() {
  const chosen = await window.pywebview.api.pick_folder();
  if (!chosen) return;
  state.createOut = chosen;
  $("create-out-folder").textContent = chosen;
}

// Choose and save a new output folder.
async function changeOutput() {
  const chosen = await window.pywebview.api.pick_folder();
  if (!chosen) return;
  const res = await window.pywebview.api.set_output_dir(chosen);
  if (res.ok) {
    state.outputDir = res.output_dir;
    $("output-path").textContent = res.output_dir;
    if (!state.createOut) $("create-out-folder").textContent = res.output_dir;
    $("output-hint").textContent = "Saved. New binders go here, in a subfolder named after your filings.";
    if (state.buildFolder && !state.saveDir) $("save-folder").textContent = await window.pywebview.api.default_binder_dir(state.buildFolder);
  } else {
    $("output-hint").textContent = `Could not use that folder: ${res.error}`;
  }
}

// Pick the PDF to check.
async function pickPdf() {
  const chosen = await window.pywebview.api.pick_pdf();
  if (chosen) setPicked("check", chosen);
}

// Choose and save a new working folder.
async function changeWorkspace() {
  const chosen = await window.pywebview.api.pick_folder();
  if (!chosen) return;
  const res = await window.pywebview.api.set_workspace(chosen);
  if (res.ok) {
    state.workspace = res.workspace;
    $("workspace-path").textContent = res.workspace;
    if (!state.createWork) $("create-work-folder").textContent = res.workspace;
    $("workspace-hint").textContent = "Saved. New files go here.";
  } else {
    $("workspace-hint").textContent = `Could not use that folder: ${res.error}`;
  }
}

// Switch the visible panel; supports arrow-key navigation.
function selectTab(tab) {
  document.querySelectorAll(".nav-item").forEach((t) => {
    const active = t === tab;
    t.setAttribute("aria-selected", String(active));
    t.tabIndex = active ? 0 : -1;
    $(t.getAttribute("aria-controls")).hidden = !active;
  });
  tab.focus();
}

function wireTabs() {
  const tabs = [...document.querySelectorAll(".nav-item")];
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => selectTab(tab));
    tab.addEventListener("keydown", (e) => {
      const step = { ArrowDown: 1, ArrowUp: -1 }[e.key];
      if (step) selectTab(tabs[(i + step + tabs.length) % tabs.length]);
    });
  });
}

function wireActions() {
  const busy = (id, resultId, message, fn) =>
    $(id).addEventListener("click", (e) => withBusy(e.currentTarget, $(resultId), message, fn));
  busy("run-create", "result-create", "Generating filings, building the binder and checking 20 gates…", runCreate);
  busy("run-build", "result-build", "Building your binder…", runBuild);
  busy("run-check", "result-check", "Checking 20 gates…", runCheck);
  $("pick-folder").addEventListener("click", pickFolder);
  $("pick-pdf").addEventListener("click", pickPdf);
  $("pick-workspace").addEventListener("click", changeWorkspace);
  $("pick-save-dir").addEventListener("click", pickSaveDir);
  $("pick-create-work").addEventListener("click", pickCreateWork);
  $("pick-create-out").addEventListener("click", pickCreateOut);
  $("cd-date").addEventListener("change", refreshSuggestedName);
  $("pick-output").addEventListener("click", changeOutput);
  $("show-output").addEventListener("click", () => window.pywebview.api.reveal(state.outputDir));
  $("show-workspace").addEventListener("click", () => window.pywebview.api.reveal(state.workspace));
}


// ---------- File with CSO: guided setup ----------

// Build a button that opens one official CSO page in the user's browser.
function csoButton(key, label, className = "btn-secondary") {
  const btn = button(label, className, async () => {
    const res = await window.pywebview.api.open_cso_page(key);
    note.textContent = res.ok ? "Opened in your browser. Come back here when you are done." : `Could not open the page: ${res.error}`;
  });
  const note = el("span", "hint");
  const wrap = el("span", "link-row");
  wrap.append(btn, note);
  return wrap;
}

// Build a bulleted list from strings.
function bullets(items) {
  const list = el("ul");
  items.forEach((text) => list.append(el("li", null, text)));
  return list;
}

// Question 1: account.
function renderAccount(value) {
  if (value === "yes") return [el("p", null, "Good. Go to question 2.")];
  return [
    el("p", null, "Registering takes two steps. Searching court files needs no account, but filing does."),
    bullets([
      "Step A: get an identity CSO accepts. A Basic BCeID suits one person; a Business BCeID suits several people sharing an account; a BC Services Card or a premium BC Registries and Online Services account also work. If you have used other B.C. government online services you may already have one.",
      "Step B: register that identity with CSO. On the CSO register page, sign in, accept the service agreement and enter your account and account manager details.",
    ]),
    el("p", "hint", "Need a BCeID? Apply at bceid.ca/register or call the BCeID Help Desk, 1-888-356-2741 (8:30 a.m. to 4:30 p.m., Monday to Friday)."),
    csoButton("register", "Open the CSO register page", "btn-primary"),
  ];
}

// Question 2: logged on.
function renderLogon(value) {
  if (value === "yes") {
    return [
      el("p", null, "Open the E-file home page. Its Add Package button is for filing into a court file. For a binder, choose Application Records in the left-hand E-file menu instead."),
      csoButton("efile_home", "Open CSO E-file home", "btn-primary"),
      el("p", "hint", "If CSO asks you to log on, use the log on page instead."),
    ];
  }
  return [
    el("p", null, "Log on with your BCeID or BC Services Card, not your CSO Client ID."),
    csoButton("logon", "Open the CSO log on page", "btn-primary"),
    csoButton("logon_bc_service_card", "Log on with BC Services Card"),
    csoButton("logon_bceid", "Log on with BCeID"),
  ];
}

// Question 3: credit card.
function renderCard(value) {
  if (value === "yes") return [el("p", null, "Good. You can file once you are on the Application Records page.")];
  return [
    el("p", null, "CSO will not let you file until a credit card is registered. Do this before your filing deadline, not on filing day."),
    bullets([
      "Log on to CSO. In the left-hand menu choose Profile, then Register Credit Card, then press the Register Credit Card button.",
      "CSO sends you to the Province's payment page. Enter your card details there only, never in this app. Accepted cards: Visa, Visa Debit, MasterCard, MasterCard Debit and American Express.",
      "Using a corporate card? CSO warns that it must be registered for government services with your card's bank first.",
      "A premium BC Registries and Online Services account can pay instead of a card.",
    ]),
    el("p", "hint", "Stuck? CSO Support Centre: 1-800-663-6102, 8:30 a.m. to 4:30 p.m. Pacific, Monday to Friday. Email Courts.CSO@gov.bc.ca."),
    csoButton("register_credit_card", "Open the Register Credit Card page", "btn-primary"),
    el("p", "hint", "Not logged on yet? CSO will ask you to log on first."),
    csoButton("logon", "Open the CSO log on page"),
    csoButton("registration_guide", "CSO registration guide (PDF)"),
  ];
}

const RENDERERS = { "q-account": ["answer-account", renderAccount], "q-logon": ["answer-logon", renderLogon], "q-card": ["answer-card", renderCard] };

// Show the guidance for a chosen answer.
function onQuestionChange(event) {
  const radio = event.target;
  const entry = RENDERERS[radio.name];
  if (entry) show($(entry[0]), ...entry[1](radio.value));
}

// Pick the binder and show how it must be uploaded.
async function pickFilePdf() {
  const chosen = await window.pywebview.api.pick_pdf();
  if (!chosen) return;
  $("file-pdf").textContent = chosen;
  $("file-picker").classList.add("has-value");
  const res = await window.pywebview.api.filing_route(chosen);
  const target = $("answer-binder");
  if (!res.ok) return show(target, verdict("danger", "Could not read the file", res.error));
  const titles = { direct: "Upload it directly", large_file: "Use Upload Large Files first", too_large: "Too large to file" };
  show(target, verdict(res.level, titles[res.route], res.message));
}

// Show when the CSO addresses were last verified.
async function showCsoVerified() {
  const res = await window.pywebview.api.cso_pages();
  if (res.ok) $("cso-verified").textContent = `CSO page addresses last verified ${res.verified_on}. If a page does not match what is described here, check the CSO website.`;
}

function wireCso() {
  document.querySelectorAll(".stage input[type=radio]").forEach((r) => r.addEventListener("change", onQuestionChange));
  $("pick-file-pdf").addEventListener("click", pickFilePdf);
  showCsoVerified();
}

window.addEventListener("pywebviewready", async () => {
  wireTabs();
  wireActions();
  wireCso();
  state.workspace = await window.pywebview.api.workspace();
  $("workspace-path").textContent = state.workspace;
  state.outputDir = await window.pywebview.api.output_dir();
  $("output-path").textContent = state.outputDir;
  $("create-work-folder").textContent = state.workspace;
  $("create-out-folder").textContent = state.outputDir;
});
