const state = {
  agents: {},
  lastResult: null,
  history: [],
};

const el = {
  appShell: document.getElementById("appShell"),
  apiStatus: document.getElementById("apiStatus"),
  llmStatus: document.getElementById("llmStatus"),
  agentCount: document.getElementById("agentCount"),
  taskCount: document.getElementById("taskCount"),
  lastStatus: document.getElementById("lastStatus"),
  rowCount: document.getElementById("rowCount"),
  agentSelect: document.getElementById("agentSelect"),
  agentList: document.getElementById("agentList"),
  taskInput: document.getElementById("taskInput"),
  dbPathInput: document.getElementById("dbPathInput"),
  sqlInput: document.getElementById("sqlInput"),
  metadataInput: document.getElementById("metadataInput"),
  useLlmInput: document.getElementById("useLlmInput"),
  allowWritesInput: document.getElementById("allowWritesInput"),
  runButton: document.getElementById("runButton"),
  seedButton: document.getElementById("seedButton"),
  clearButton: document.getElementById("clearButton"),
  refreshButton: document.getElementById("refreshButton"),
  schemaButton: document.getElementById("schemaButton"),
  copyButton: document.getElementById("copyButton"),
  templatesButton: document.getElementById("templatesButton"),
  runState: document.getElementById("runState"),
  schemaView: document.getElementById("schemaView"),
  jsonOutput: document.getElementById("jsonOutput"),
  resultTable: document.getElementById("resultTable"),
  tableEmpty: document.getElementById("tableEmpty"),
  timeline: document.getElementById("timeline"),
  historyList: document.getElementById("historyList"),
  templatesModal: document.getElementById("templatesModal"),
  templatesList: document.getElementById("templatesList"),
  toast: document.getElementById("toast"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}

function iconUse(id) {
  return `<svg aria-hidden="true"><use href="#${id}"></use></svg>`;
}

function showToast(message) {
  el.toast.textContent = message;
  el.toast.classList.add("visible");
  window.setTimeout(() => el.toast.classList.remove("visible"), 2600);
}

function parseMetadata() {
  const metadata = {};
  const lines = el.metadataInput.value.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const index = trimmed.indexOf("=");
    if (index === -1) continue;
    metadata[trimmed.slice(0, index).trim()] = trimmed.slice(index + 1).trim();
  }
  const sql = el.sqlInput.value.trim();
  if (sql) metadata.sql = sql;
  return metadata;
}

function setRunning(isRunning) {
  el.runButton.disabled = isRunning;
  el.runButton.classList.toggle("loading", isRunning);
  el.runState.textContent = isRunning ? "Running" : "Ready";
  el.runState.classList.toggle("running", isRunning);
}

function setStatus(status, isError = false) {
  el.lastStatus.textContent = status;
  el.runState.textContent = status;
  el.runState.classList.toggle("error", isError);
}

function renderAgents() {
  const entries = Object.entries(state.agents);
  el.agentCount.textContent = entries.length;
  el.agentSelect.innerHTML = `<option value="">Auto route</option>`;
  el.agentList.innerHTML = "";

  for (const [name, description] of entries) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    el.agentSelect.appendChild(option);

    const card = document.createElement("article");
    card.className = "agent-card";
    card.innerHTML = `
      <div class="agent-dot"></div>
      <div>
        <strong>${escapeHtml(name)}</strong>
        <span>${escapeHtml(description)}</span>
      </div>
    `;
    el.agentList.appendChild(card);
  }
}

function renderSchema(schema) {
  const entries = Object.entries(schema || {});
  if (!entries.length) {
    el.schemaView.innerHTML = `<div class="empty-state">No tables found</div>`;
    return;
  }

  el.schemaView.innerHTML = entries.map(([table, columns]) => {
    const columnText = columns.map((column) => `${column.name}:${column.type || "ANY"}`).join(", ");
    return `
      <article class="schema-table">
        <strong>${escapeHtml(table)}</strong>
        <code>${escapeHtml(columnText)}</code>
      </article>
    `;
  }).join("");
}

function findRows(payload) {
  const results = payload?.result?.results || [];
  for (const item of results) {
    const rows = item?.result?.result;
    if (Array.isArray(rows)) return rows;
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
    el.rowCount.textContent = "0";
    return;
  }

  el.tableEmpty.style.display = "none";
  el.rowCount.textContent = rows.length;
  const columns = Object.keys(rows[0]);
  thead.innerHTML = `<tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>`;
  tbody.innerHTML = rows.map((row) => {
    return `<tr>${columns.map((column) => `<td>${escapeHtml(String(row[column] ?? ""))}</td>`).join("")}</tr>`;
  }).join("");
}

function renderTimeline(payload) {
  const subtasks = payload?.subtasks || [];
  if (!subtasks.length) {
    el.timeline.innerHTML = `<div class="empty-state">No subtasks recorded</div>`;
    return;
  }
  el.timeline.innerHTML = subtasks.map((task, index) => `
    <article class="timeline-item">
      <strong>${index + 1}. ${escapeHtml(task.agent || "unassigned")}</strong>
      <span>${escapeHtml(task.description)}</span>
      <span>Status: ${escapeHtml(task.status)}</span>
    </article>
  `).join("");
}

function renderResult(payload) {
  state.lastResult = payload;
  state.history.unshift(payload);
  state.history = state.history.slice(0, 20);
  el.taskCount.textContent = state.history.length;
  el.jsonOutput.textContent = JSON.stringify(payload, null, 2);
  renderTable(findRows(payload));
  renderTimeline(payload);
  setStatus(payload.status || "Completed", payload.status === "failed");
  renderHistory();
}

function renderHistory() {
  if (!state.history.length) {
    el.historyList.innerHTML = `<div class="empty-state">No tasks executed yet</div>`;
    return;
  }
  el.historyList.innerHTML = state.history.map((item, index) => `
    <article class="history-item">
      <div class="history-main">
        <strong>${escapeHtml(item.description || "Unknown task")}</strong>
        <span class="history-meta">${escapeHtml(item.agent || "auto")} • ${new Date(item.timestamp).toLocaleString()}</span>
      </div>
      <span class="status-badge ${item.status === "completed" ? "success" : item.status === "failed" ? "error" : ""}">${escapeHtml(item.status)}</span>
    </article>
  `).join("");
}

function renderTemplates(templates) {
  el.templatesList.innerHTML = Object.entries(templates).map(([name, tmpl]) => `
    <article class="template-card">
      <div class="template-header">
        <strong>${escapeHtml(name)}</strong>
      </div>
      <div class="template-subject">Subject: ${escapeHtml(tmpl.subject)}</div>
      <div class="template-preview">${escapeHtml(tmpl.body_preview)}</div>
      <button class="ghost-button template-use" data-template="${escapeHtml(name)}">Use Template</button>
    </article>
  `).join("");

  document.querySelectorAll(".template-use").forEach(btn => {
    btn.addEventListener("click", () => {
      const templateName = btn.dataset.template;
      el.taskInput.value = `Send email using ${templateName} template`;
      el.metadataInput.value = `template=${templateName}\nvariables.contact_name=John Doe\nvariables.company_name=Acme Corp\nvariables.sender_name=Jane Smith`;
      closeModal();
      showToast(`Template "${templateName}" loaded. Fill in variables and run.`);
    });
  });
}

async function refresh() {
  try {
    const [health, agents] = await Promise.all([
      api("/api/health"),
      api("/api/agents"),
    ]);

    el.apiStatus.textContent =
      health.status === "ok" ? "Online" : "Issue";

    el.llmStatus.textContent =
      health.llm_enabled_by_default ? "Default on" : "Manual";

    state.agents = agents;
    renderAgents();
  } catch (error) {
    el.apiStatus.textContent = "Offline";
    showToast(error.message);
  }
}

async function loadSchema() {
  try {
    const dbPath = encodeURIComponent(el.dbPathInput.value.trim() || "arkagents.db");
    const data = await api(`/api/schema?db_path=${dbPath}`);
    renderSchema(data.schema);
    showToast("Schema loaded");
  } catch (error) {
    showToast(error.message);
  }
}

async function seedDb() {
  try {
    const data = await api("/api/seed-db", {
      method: "POST",
      body: JSON.stringify({ db_path: el.dbPathInput.value.trim() || "arkagents.db" }),
    });
    showToast(`Seed complete: ${data.rows_available || 0} demo rows available`);
    await loadSchema();
  } catch (error) {
    showToast(error.message);
  }
}

async function loadTemplates() {
  try {
    const data = await api("/api/templates");
    renderTemplates(data);
    el.templatesModal.style.display = "flex";
  } catch (error) {
    showToast(error.message);
  }
}

function closeModal() {
  el.templatesModal.style.display = "none";
}

async function runTask() {
  const description = el.taskInput.value.trim();
  if (!description) {
    showToast("Task description is required");
    return;
  }

  setRunning(true);
  try {
    const payload = {
      description,
      agent: el.agentSelect.value || null,
      db_path: el.dbPathInput.value.trim() || "arkagents.db",
      metadata: parseMetadata(),
      use_llm: el.useLlmInput.checked,
      allow_db_writes: el.allowWritesInput.checked,
    };
    const result = await api("/api/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderResult(result);
    showToast("Task completed");
  } catch (error) {
    setStatus("Failed", true);
    showToast(error.message);
  } finally {
    setRunning(false);
  }
}

function clearOutput() {
  state.lastResult = null;
  el.jsonOutput.textContent = "{}";
  renderTable([]);
  renderTimeline({ subtasks: [] });
  setStatus("Idle");
}

async function copyJson() {
  if (!state.lastResult) {
    showToast("No JSON to copy");
    return;
  }
  await navigator.clipboard.writeText(JSON.stringify(state.lastResult, null, 2));
  showToast("JSON copied");
}

function setActiveTab(name) {
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === name);
  });
  document.querySelectorAll(".panel").forEach((panel) => panel.classList.remove("active"));
  document.getElementById(name).classList.add("active");
}

function setResultTab(name) {
  document.querySelectorAll(".tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === name);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
  document.getElementById(`${name}Panel`).classList.add("active");
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&")
    .replaceAll("<", "<")
    .replaceAll(">", ">")
    .replaceAll('"', '"')
    .replaceAll("'", "&#039;");
}

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", (e) => {
    e.preventDefault();
    setActiveTab(button.dataset.tab);
  });
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => setResultTab(button.dataset.tab));
});

el.runButton.addEventListener("click", runTask);
el.seedButton.addEventListener("click", seedDb);
el.clearButton.addEventListener("click", clearOutput);
el.refreshButton.addEventListener("click", () => refresh().then(() => showToast("Status refreshed")));
el.schemaButton.addEventListener("click", loadSchema);
el.copyButton.addEventListener("click", copyJson);
el.templatesButton.addEventListener("click", loadTemplates);

document.querySelector(".modal-close").addEventListener("click", closeModal);
el.templatesModal.querySelector(".modal-overlay").addEventListener("click", closeModal);

// Start dashboard immediately — no authentication required.
el.appShell.style.display = "grid";

refresh().catch((error) => {
  console.error("Dashboard startup error:", error);
});