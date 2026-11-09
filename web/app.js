const state = {
  data: null,
  selected: 0,
  running: false,
};

const el = (id) => document.getElementById(id);

function near(yocto) {
  if (yocto === null || yocto === undefined) return "—";
  const value = BigInt(yocto);
  const base = 10n ** 24n;
  const whole = value / base;
  const fraction = (value % base).toString().padStart(24, "0").slice(0, 4);
  return `${whole}.${fraction}`;
}

function short(value, head = 8, tail = 6) {
  if (!value) return "—";
  const text = String(value);
  if (text.length <= head + tail + 1) return text;
  return `${text.slice(0, head)}…${text.slice(-tail)}`;
}

function explorer(tx) {
  return `https://explorer.testnet.near.org/transactions/${tx}`;
}

function link(href, text, className = "") {
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.target = "_blank";
  anchor.rel = "noreferrer";
  anchor.textContent = text;
  if (className) anchor.className = className;
  return anchor;
}

function step(name, status) {
  const node = document.querySelector(`.step[data-step="${name}"]`);
  if (!node) return;
  node.classList.remove("active", "done", "fail");
  if (status) node.classList.add(status);
}

function resetTimeline() {
  ["request", "compute", "verify", "settle"].forEach((name) => step(name, null));
  el("timeline").classList.remove("hidden");
}

function showError(message) {
  el("error").textContent = message;
  el("error").classList.remove("hidden");
}

function clearError() {
  el("error").textContent = "";
  el("error").classList.add("hidden");
}

function selectedDataset() {
  return state.data?.datasets?.[state.selected] || null;
}

function renderBanner() {
  const banner = el("banner");
  if (state.data?.paused) {
    banner.textContent = "Contract is paused. New queries will be rejected until the owner unpauses.";
    banner.classList.remove("hidden");
  } else {
    banner.classList.add("hidden");
  }
}

function renderDatasets() {
  const container = el("datasets");
  container.innerHTML = "";
  const datasets = state.data?.datasets || [];
  el("dataset-count").textContent = String(datasets.length);

  datasets.forEach((entry, index) => {
    const card = document.createElement("button");
    card.className = `dataset-card${index === state.selected ? " selected" : ""}`;
    card.type = "button";
    if (!entry.dataset) {
      card.textContent = `${entry.dataset_id || "dataset"} unavailable`;
      card.disabled = true;
      container.appendChild(card);
      return;
    }
    const dataset = entry.dataset;
    const quote = entry.quote;
    const budget = entry.budget || { count: 0 };
    card.innerHTML = `
      <div class="dataset-top">
        <span class="dataset-name">${entry.dataset_id}</span>
        <span class="dataset-price">${near(quote.price_yocto)} NEAR</span>
      </div>
      <div class="dataset-meta">
        <span>owner ${short(dataset.owner)}</span>
        <span>version ${dataset.version}</span>
        <span>${budget.count}/${dataset.budget_per_day} queries today</span>
        <span>reward ${near(dataset.reward_yocto)} NEAR</span>
      </div>
    `;
    card.addEventListener("click", () => {
      state.selected = index;
      renderDatasets();
      renderSelected();
    });
    container.appendChild(card);
  });
}

function renderSelected() {
  const entry = selectedDataset();
  const node = el("selected-dataset");
  const runButton = el("run");
  if (!entry?.dataset) {
    node.innerHTML = '<p class="muted">No dataset available.</p>';
    runButton.disabled = true;
    el("budget-pill").textContent = "budget —";
    return;
  }
  const dataset = entry.dataset;
  const quote = entry.quote;
  const budget = entry.budget || { count: 0 };
  node.innerHTML = `
    <h3>${entry.dataset_id} <span class="muted">· ${entry.computation_id}</span></h3>
    <p>Computation <span class="k">${quote.operation}</span></p>
    <p>Price <span class="k">${near(quote.price_yocto)} NEAR</span> · owner reward <span class="k">${near(quote.reward_yocto)} NEAR</span></p>
    <p>Owner <span class="k">${dataset.owner}</span></p>
    <p>Dataset hash <span class="k">${short(dataset.data_hash, 16, 10)}</span></p>
  `;
  el("budget-pill").textContent = `${budget.count}/${dataset.budget_per_day} today`;
  runButton.disabled = state.data?.paused || state.running;
}

function renderHistory() {
  const container = el("history");
  container.innerHTML = "";
  const queries = state.data?.recent_queries || [];
  if (!queries.length) {
    container.innerHTML = '<p class="muted">No queries yet.</p>';
    return;
  }
  queries
    .slice()
    .reverse()
    .forEach((query) => {
      const row = document.createElement("div");
      row.className = "history-row";
      row.innerHTML = `
        <span class="id">#${query.query_id ?? ""}</span>
        <span>${query.dataset_id} · ${query.computation_id}</span>
        <span class="status ${query.status}">${query.status}</span>
        <span class="when">block ${query.created_block}</span>
      `;
      container.appendChild(row);
    });
}

function renderResult(data) {
  const panel = el("result-panel");
  panel.classList.remove("hidden");
  const result = data.result;
  const rows = result?.results || [];
  const badge = el("proof-badge");
  badge.textContent = data.proof ? "PROVEN" : data.status === "failed" ? "FAILED" : "NOT PROVEN";
  badge.className = `pill ${data.proof ? "proof" : "danger"}`;

  const summary = el("result-summary");
  summary.innerHTML = "";
  if (rows.length) {
    rows.forEach((row) => {
      const stat = document.createElement("div");
      stat.className = "stat";
      stat.innerHTML = `
        <span>${row.country} growth</span>
        <strong>${row.growth_pct ?? "suppressed"}%</strong>
      `;
      summary.appendChild(stat);
    });
  } else {
    summary.innerHTML = '<p class="muted">No aggregate rows were released.</p>';
  }

  const table = el("result-table");
  table.innerHTML = "";
  if (rows.length) {
    const html = `
      <table>
        <thead>
          <tr><th>Country</th><th class="mono">Spend A</th><th class="mono">Spend B</th><th class="mono">Growth</th><th>Cohort A</th><th>Cohort B</th></tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `<tr>
                <td>${row.country}</td>
                <td class="mono">${row.spend_a ?? "—"}</td>
                <td class="mono">${row.spend_b ?? "—"}</td>
                <td class="mono">${row.growth_pct ?? "—"}%</td>
                <td>${row.cohort_a}</td>
                <td>${row.cohort_b}</td>
              </tr>`,
            )
            .join("")}
        </tbody>
      </table>
    `;
    table.innerHTML = html;
  }

  const meta = el("result-meta");
  meta.innerHTML = "";
  const items = [
    ["Query", `#${data.query_id}`],
    ["Request tx", data.tx_hash],
    ["Acceptance tx", data.accept_tx || data.refund_tx || "—"],
    ["Data owner", data.owner],
    ["Owner before", `${near(data.owner_before)} NEAR`],
    ["Owner after", `${near(data.owner_after)} NEAR`],
    ["Dataset hash", result?.dataset_sha256 || "—"],
  ];
  items.forEach(([label, value]) => {
    const item = document.createElement("div");
    item.className = "meta-item";
    const title = document.createElement("span");
    title.textContent = label;
    item.appendChild(title);
    if (label.includes("tx") && value && value !== "—") {
      item.appendChild(link(explorer(value), short(value, 14, 10)));
    } else {
      const code = document.createElement("code");
      code.textContent = value || "—";
      item.appendChild(code);
    }
    meta.appendChild(item);
  });

  el("proof-output").textContent = data.proof_output || "No attestation output.";
  el("result-title").textContent = `${data.dataset_id || selectedDataset()?.dataset_id || "dataset"} aggregate`;
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function refresh() {
  clearError();
  try {
    const response = await fetch("/api/state");
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "failed to load state");
    state.data = payload;
    if (state.selected >= payload.datasets.length) state.selected = 0;
    el("contract-link").href = `https://explorer.testnet.near.org/accounts/${payload.contract}`;
    el("contract-link").textContent = short(payload.contract, 12, 8);
    el("footer-meta").textContent = `contract ${short(payload.contract, 14, 10)} · agent ${short(payload.agent, 10, 6)}`;
    renderBanner();
    renderDatasets();
    renderSelected();
    renderHistory();
  } catch (error) {
    showError(String(error));
  }
}

async function runQuery() {
  const entry = selectedDataset();
  if (!entry?.dataset || state.running) return;
  state.running = true;
  el("run").disabled = true;
  clearError();
  resetTimeline();
  step("request", "active");

  try {
    const response = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_id: entry.dataset_id,
        computation_id: entry.computation_id,
      }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "query failed");

    step("request", "done");
    step("compute", payload.status === "failed" ? "fail" : "done");
    step("verify", payload.proof ? "done" : "fail");
    step("settle", payload.accept_tx ? "done" : payload.refund_tx ? "done" : null);

    renderResult(payload);
    await refresh();
    if (payload.status === "failed") {
      showError("The approved computation failed. The agent was refunded.");
    }
  } catch (error) {
    step("compute", "fail");
    showError(String(error));
  } finally {
    state.running = false;
    el("run").disabled = false;
  }
}

el("refresh").addEventListener("click", refresh);
el("run").addEventListener("click", runQuery);
refresh();
setInterval(refresh, 30000);
