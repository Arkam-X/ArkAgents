const state = {
  agents: {},
  history: [],
  lastResult: null,
};

const el = {
  apiStatusDot: document.getElementById("apiStatusDot"),
  apiStatusText: document.getElementById("apiStatusText"),
  llmStatusDot: document.getElementById("llmStatusDot"),
  llmStatusText: document.getElementById("llmStatusText"),
  systemClock: document.getElementById("systemClock"),
  runState: document.getElementById("runState"),
  taskInput: document.getElementById("taskInput"),
  agentSelect: document.getElementById("agentSelect"),
  dbPathInput: document.getElementById("dbPathInput"),
  sqlInput: document.getElementById("sqlInput"),
  metadataInput: document.getElementById("metadataInput"),
  useLlmInput: document.getElementById("useLlmInput"),
  allowWritesInput: document.getElementById("allowWritesInput"),
  runButton: document.getElementById("runButton"),
  clearButton: document.getElementById("clearButton"),
  templatesButton: document.getElementById("templatesButton"),
  schemaButton: document.getElementById("schemaButton"),
  clearHistoryBtn: document.getElementById("clearHistoryBtn"),
  agentCount: document.getElementById("agentCount"),
  agentList: document.getElementById("agentList"),
  schemaView: document.getElementById("schemaView"),
  historyList: document.getElementById("historyList"),
  resultTable: document.getElementById("resultTable"),
  tableEmpty: document.getElementById("tableEmpty"),
  jsonOutput: document.getElementById("jsonOutput"),
  timeline: document.getElementById("timeline"),
  copyButton: document.getElementById("copyButton"),
  templatesModal: document.getElementById("templatesModal"),
  templatesList: document.getElementById("templatesList"),
  toast: document.getElementById("toast"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function tickClock() {
  const now = new Date();
  el.systemClock.textContent = now.toLocaleTimeString("en-US", { hour12: false });
}

function showToast(message) {
  el.toast.textContent = message;
  el.toast.classList.add("visible");
  window.setTimeout(() => el.toast.classList.remove("visible"), 2600);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function parseMetadata() {
  const metadata = {};
  for (const line of el.metadataInput.value.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || !trimmed.includes("=")) continue;
    const [key, ...rest] = trimmed.split("=");
    metadata[key.trim()] = rest.join("=").trim();
  }

  const sql = el.sqlInput.value.trim();
  if (sql) metadata.sql = sql;
  return metadata;
}

function setRunState(label, tone = "idle") {
  el.runState.textContent = label;
  el.runState.className = `panel-status ${tone}`;
}

function setLoading(isLoading) {
  el.runButton.disabled = isLoading;
  el.runButton.classList.toggle("loading", isLoading);
  setRunState(isLoading ? "RUNNING" : "READY", isLoading ? "running" : "idle");
}

function renderAgents() {
  const entries = Object.entries(state.agents);
  el.agentCount.textContent = String(entries.length);
  el.agentSelect.innerHTML = `<option value="">AUTO_ROUTE</option>`;
  el.agentList.innerHTML = "";

  for (const [name, description] of entries) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name.toUpperCase();
    el.agentSelect.appendChild(option);

    const card = document.createElement("article");
    card.className = "agent-card";
    card.innerHTML = `
      <div class="agent-chip">${escapeHtml(name.slice(0, 2).toUpperCase())}</div>
      <div>
        <strong>${escapeHtml(name.toUpperCase())}</strong>
        <span>${escapeHtml(description)}</span>
      </div>
    `;
    el.agentList.appendChild(card);
  }
}

function renderSchema(schema) {
  const entries = Object.entries(schema || {});
  if (!entries.length) {
    el.schemaView.innerHTML = `<div class="empty-state">[ NO TABLES FOUND ]</div>`;
    return;
  }

  el.schemaView.innerHTML = entries.map(([table, columns]) => {
    const columnText = columns.map((column) => `${column.name}:${column.type || "ANY"}`).join(" // ");
    return `
      <article class="schema-card">
        <strong>${escapeHtml(table.toUpperCase())}</strong>
        <code>${escapeHtml(columnText)}</code>
      </article>
    `;
  }).join("");
}

function findRows(payload) {
  const results = payload?.result?.results || [];
  for (const item of results) {
    const directRows = item?.result?.result;
    if (Array.isArray(directRows)) return directRows;
    const exportedRows = item?.result?.result?.data;
    if (Array.isArray(exportedRows)) return exportedRows;
  }
  return [];
}

function renderTable(rows) {
  const thead = el.resultTable.querySelector("thead");
  const tbody = el.resultTable.querySelector("tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  if (!rows.length || typeof rows[0] !== "object") {
    el.tableEmpty.style.display = "grid";
    return;
  }

  el.tableEmpty.style.display = "none";
  const columns = Object.keys(rows[0]);
  thead.innerHTML = `<tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>`;
  tbody.innerHTML = rows.map((row) => `
    <tr>${columns.map((column) => `<td>${escapeHtml(row[column])}</td>`).join("")}</tr>
  `).join("");
}

function renderTimeline(payload) {
  const subtasks = payload?.subtasks || [];
  if (!subtasks.length) {
    el.timeline.innerHTML = `<div class="empty-state">[ NO SUBTASKS ]</div>`;
    return;
  }

  el.timeline.innerHTML = subtasks.map((task, index) => `
    <article class="timeline-item ${task.status === "failed" ? "failed" : ""}">
      <div class="timeline-index">${String(index + 1).padStart(2, "0")}</div>
      <div>
        <strong>${escapeHtml(task.agent || "UNASSIGNED")}</strong>
        <span>${escapeHtml(task.description)}</span>
        <small>STATUS: ${escapeHtml(task.status)}</small>
      </div>
    </article>
  `).join("");
}

function addHistory(payload) {
  state.history.unshift({
    timestamp: new Date().toISOString(),
    description: payload.description || "Unknown task",
    agent: payload.agent || "auto",
    status: payload.status || "unknown",
  });
  state.history = state.history.slice(0, 25);
  renderHistory();
}

function renderHistory() {
  if (!state.history.length) {
    el.historyList.innerHTML = `<div class="empty-state">[ NO EXECUTIONS RECORDED ]</div>`;
    return;
  }

  el.historyList.innerHTML = state.history.map((item) => `
    <article class="history-item ${item.status === "failed" ? "failed" : ""}">
      <div>
        <strong>${escapeHtml(item.description)}</strong>
        <span>${escapeHtml(item.agent)} // ${new Date(item.timestamp).toLocaleString()}</span>
      </div>
      <em>${escapeHtml(item.status)}</em>
    </article>
  `).join("");
}

function renderResult(payload) {
  state.lastResult = payload;
  el.jsonOutput.textContent = JSON.stringify(payload, null, 2);
  renderTable(findRows(payload));
  renderTimeline(payload);
  addHistory(payload);
  setRunState(payload.status === "failed" ? "FAILED" : "COMPLETE", payload.status === "failed" ? "error" : "success");
}

async function refresh() {
  const [health, agents] = await Promise.all([
    api("/api/health"),
    api("/api/agents"),
  ]);
  el.apiStatusText.textContent = health.status === "ok" ? "ONLINE" : "ISSUE";
  el.apiStatusDot.className = `status-dot ${health.status === "ok" ? "online" : "error"}`;
  el.llmStatusText.textContent = health.llm_enabled_by_default ? "LLM ON" : "MANUAL";
  el.llmStatusDot.className = `status-dot ${health.llm_enabled_by_default ? "online" : "warning"}`;
  state.agents = agents;
  renderAgents();
}

async function loadSchema() {
  const dbPath = encodeURIComponent(el.dbPathInput.value.trim() || "arkagents.db");
  const data = await api(`/api/schema?db_path=${dbPath}`);
  renderSchema(data.schema);
  showToast("SCHEMA LOADED");
}

async function loadHistory() {
  const data = await api("/api/history");
  state.history = (data.history || []).map((item) => ({
    timestamp: item.timestamp,
    description: item.description,
    agent: item.agent,
    status: item.status,
  }));
  renderHistory();
}

async function runTask() {
  const description = el.taskInput.value.trim();
  if (!description) {
    showToast("TASK DESCRIPTION REQUIRED");
    return;
  }

  setLoading(true);
  try {
    const result = await api("/api/run", {
      method: "POST",
      body: JSON.stringify({
        description,
        agent: el.agentSelect.value || null,
        db_path: el.dbPathInput.value.trim() || "arkagents.db",
        metadata: parseMetadata(),
        use_llm: el.useLlmInput.checked,
        allow_db_writes: el.allowWritesInput.checked,
      }),
    });
    renderResult(result);
    showToast("EXECUTION COMPLETE");
  } catch (error) {
    setRunState("FAILED", "error");
    showToast(error.message);
  } finally {
    el.runButton.disabled = false;
    el.runButton.classList.remove("loading");
  }
}

async function loadTemplates() {
  const templates = await api("/api/templates", { method: "POST", body: "{}" });
  el.templatesList.innerHTML = Object.entries(templates).map(([name, template]) => `
    <article class="template-card">
      <strong>${escapeHtml(name.toUpperCase())}</strong>
      <span>${escapeHtml(template.subject)}</span>
      <p>${escapeHtml(template.body_preview)}</p>
      <button class="btn-secondary template-use" data-template="${escapeHtml(name)}">LOAD TEMPLATE</button>
    </article>
  `).join("");

  el.templatesList.querySelectorAll(".template-use").forEach((button) => {
    button.addEventListener("click", () => {
      const template = button.dataset.template;
      el.agentSelect.value = "email";
      el.taskInput.value = `Send ${template} email`;
      el.metadataInput.value = `template=${template}\nvariables.contact_name=Client Name\nvariables.company_name=Company Name\nvariables.sender_name=Your Name`;
      closeModal();
      showToast("TEMPLATE LOADED");
    });
  });

  openModal();
}

function openModal() {
  el.templatesModal.classList.add("visible");
}

function closeModal() {
  el.templatesModal.classList.remove("visible");
}

function clearOutput() {
  state.lastResult = null;
  el.jsonOutput.textContent = "{}";
  renderTable([]);
  renderTimeline({ subtasks: [] });
  setRunState("READY", "idle");
}

function clearHistory() {
  state.history = [];
  renderHistory();
  showToast("LOCAL HISTORY CLEARED");
}

async function copyJson() {
  if (!state.lastResult) {
    showToast("NO JSON TO COPY");
    return;
  }
  await navigator.clipboard.writeText(JSON.stringify(state.lastResult, null, 2));
  showToast("JSON COPIED");
}

function setResultTab(name) {
  document.querySelectorAll(".tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === name);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.remove("active");
  });
  document.getElementById(`${name}Panel`).classList.add("active");
}

function bindEvents() {
  el.runButton.addEventListener("click", runTask);
  el.clearButton.addEventListener("click", clearOutput);
  el.templatesButton.addEventListener("click", () => loadTemplates().catch((error) => showToast(error.message)));
  el.schemaButton.addEventListener("click", () => loadSchema().catch((error) => showToast(error.message)));
  el.clearHistoryBtn.addEventListener("click", clearHistory);
  el.copyButton.addEventListener("click", copyJson);

  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => setResultTab(button.dataset.tab));
  });

  document.querySelector(".modal-close").addEventListener("click", closeModal);
  document.querySelector(".modal-overlay").addEventListener("click", closeModal);
}

async function boot() {
  tickClock();
  window.setInterval(tickClock, 1000);
  bindEvents();
  try {
    await refresh();
    await loadSchema();
    await loadHistory();
    showToast("ARKAGENTS ONLINE");
  } catch (error) {
    el.apiStatusText.textContent = "OFFLINE";
    el.apiStatusDot.className = "status-dot error";
    showToast(error.message);
  }
}

boot();
