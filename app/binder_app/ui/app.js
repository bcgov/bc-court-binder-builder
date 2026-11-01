/*
 * app.js
 * Purpose: Navigation and the three actions (create sample filings, build a
 *          binder, check a binder). Calls Python through window.pywebview.api.
 *          All dynamic text is set with textContent, never innerHTML.
 * Layer:   Application / UI
 */

const $ = (id) => document.getElementById(id);
const state = { buildFolder: "", checkFile: "", workspace: "" };
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
  const res = await window.pywebview.api.run_full_cycle();
  if (!res.ok) return show(target, verdict("danger", "Could not create sample filings", res.error));
  const pdf = res.assembled.output_pdf;
  const summary = `${res.generated.document_count} filings and a ${formatSize(res.assembled.size_bytes)} binder saved in ${res.run_dir}`;
  show(target, verdict("info", "Sample run complete", summary, fileActions(pdf)), ...renderValidation(res.validation));
}

// Feature 2: build a binder from the chosen folder.
async function runBuild() {
  const target = $("result-build");
  const res = await window.pywebview.api.assemble(state.buildFolder, $("build-name").value);
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
  parts.push(res.has_manifest ? "manifest.json found" : "no manifest.json (order is inferred from file names)");
  meta.textContent = parts.join(" · ");
}

// Pick the folder of filings.
async function pickFolder() {
  const chosen = await window.pywebview.api.pick_folder();
  if (!chosen) return;
  setPicked("build", chosen);
  await previewFolder(chosen);
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
  $("show-workspace").addEventListener("click", () => window.pywebview.api.reveal(state.workspace));
}

window.addEventListener("pywebviewready", async () => {
  wireTabs();
  wireActions();
  state.workspace = await window.pywebview.api.workspace();
  $("workspace-path").textContent = state.workspace;
});
