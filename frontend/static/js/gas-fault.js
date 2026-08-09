const gatewayUrl = window.SERVICE_UNIVERSE?.gatewayUrl?.replace(/\/$/, "");
const page = document.querySelector("[data-gas-page]")?.dataset.gasPage;
const citizenStorageKey = "serviceUniverseGasCitizenId";
const administratorRole = "gas_operator";
let currentReportId = null;

function setBusy(form, busy) {
  const button = form?.querySelector("button[type='submit']");
  if (!button) return;
  button.disabled = busy;
  button.setAttribute("aria-busy", String(busy));
}

function showMessage(elementId, state, title, detail = "") {
  const element = document.querySelector(`#${elementId}`);
  if (!element) return;
  element.hidden = false;
  element.dataset.state = state;
  element.replaceChildren();
  const heading = document.createElement("strong");
  heading.textContent = title;
  element.append(heading);
  if (detail) {
    const description = document.createElement("span");
    description.textContent = detail;
    element.append(description);
  }
}

function hideMessage(elementId) {
  const element = document.querySelector(`#${elementId}`);
  if (element) element.hidden = true;
}

function readable(value) {
  return String(value ?? "").replaceAll("_", " ");
}

function formatTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function actorHeaders() {
  if (page === "admin") return {"X-User-Role": administratorRole};
  const citizenId = sessionStorage.getItem(citizenStorageKey);
  return citizenId ? {"X-Citizen-ID": citizenId} : {};
}

async function gatewayRequest(path, options = {}) {
  if (!gatewayUrl) throw new Error("The Gateway is not configured.");
  let response;
  try {
    response = await fetch(`${gatewayUrl}${path}`, {
      ...options,
      headers: {
        "Accept": "application/json",
        ...actorHeaders(),
        ...(options.headers ?? {})
      }
    });
  } catch {
    throw new Error("The service could not be reached. Please try again shortly.");
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error?.message ?? "The request could not be completed.");
  }
  return payload.data;
}

function renderHistory(history) {
  const list = document.querySelector("#report-history");
  list.replaceChildren();
  history.forEach((event) => {
    const item = document.createElement("li");
    const marker = document.createElement("span");
    marker.className = "gas-history-marker";
    marker.setAttribute("aria-hidden", "true");
    const copy = document.createElement("div");
    const title = document.createElement("h4");
    title.textContent = event.activity;
    const metadata = document.createElement("p");
    metadata.textContent = `${formatTime(event.timestamp)} · ${event.resource}`;
    copy.append(title, metadata);
    if (event.note) {
      const note = document.createElement("p");
      note.textContent = event.note;
      copy.append(note);
    }
    item.append(marker, copy);
    list.append(item);
  });
}

function renderReport(report) {
  currentReportId = report.report_id;
  document.querySelector("#report-id").textContent = report.report_id;
  document.querySelector("#report-status").textContent = readable(report.status);
  document.querySelector("#report-updated").textContent = `Last updated ${formatTime(report.updated_at)}`;
  document.querySelector("#report-citizen").textContent = report.citizen_id;
  document.querySelector("#report-severity").textContent = readable(report.severity);
  document.querySelector("#report-address").textContent = report.address;
  document.querySelector("#report-description").textContent = report.description;
  renderHistory(report.history ?? []);
  document.querySelector("#gas-report").hidden = false;
  document.querySelector("[data-admin-only]")?.toggleAttribute("hidden", page !== "admin");
  const cancelAction = document.querySelector("[data-citizen-cancel]");
  if (cancelAction) {
    const cancellable = [
      "reported",
      "assigned",
      "inspection_in_progress",
      "repair_in_progress"
    ].includes(report.status);
    cancelAction.toggleAttribute("hidden", !cancellable);
  }
  document.querySelectorAll(".gas-record-item").forEach((item) => {
    item.setAttribute("aria-current", String(item.dataset.reportId === report.report_id));
  });
}

function renderReportList(reports) {
  const list = document.querySelector("#user-report-list, #admin-report-list");
  if (!list) return;
  list.replaceChildren();
  if (!reports.length) {
    const empty = document.createElement("p");
    empty.className = "gas-empty-state";
    empty.textContent = page === "admin"
      ? "No fault reports have been submitted."
      : "You have not submitted a gas fault report yet.";
    list.append(empty);
    return;
  }
  reports.forEach((report) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "gas-record-item";
    button.dataset.reportId = report.report_id;
    const copy = document.createElement("span");
    const number = document.createElement("strong");
    number.textContent = report.report_id;
    const address = document.createElement("small");
    address.textContent = `${report.address} · ${formatTime(report.created_at)}`;
    copy.append(number, address);
    const status = document.createElement("span");
    status.className = "gas-record-status";
    status.textContent = readable(report.status);
    button.append(copy, status);
    list.append(button);
  });
}

async function loadReports() {
  hideMessage("records-message");
  try {
    const reports = await gatewayRequest("/api/v1/fault-reports");
    renderReportList(reports);
  } catch (error) {
    showMessage("records-message", "error", "Reports unavailable", error.message);
  }
}

async function openReport(reportId) {
  try {
    const report = await gatewayRequest(
      `/api/v1/fault-reports/${encodeURIComponent(reportId)}`
    );
    renderReport(report);
    document.querySelector("#gas-report").scrollIntoView({behavior: "smooth", block: "start"});
  } catch (error) {
    showMessage("records-message", "error", "Report unavailable", error.message);
  }
}

document.querySelector("#citizen-entry-form")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const citizenId = new FormData(event.currentTarget).get("citizen_id").trim();
  sessionStorage.setItem(citizenStorageKey, citizenId);
  window.location.assign("/services/gas-fault/user");
});

document.querySelector("#admin-entry-button")?.addEventListener("click", () => {
  window.location.assign("/services/gas-fault/admin");
});

document.querySelectorAll("[data-change-role]").forEach((link) => {
  link.addEventListener("click", () => sessionStorage.removeItem(citizenStorageKey));
});

document.querySelector("#fault-report-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  hideMessage("report-message");
  setBusy(form, true);
  const values = Object.fromEntries(new FormData(form));
  values.citizen_id = sessionStorage.getItem(citizenStorageKey);
  try {
    const report = await gatewayRequest("/api/v1/fault-reports", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(values)
    });
    showMessage("report-message", "success", `Report ${report.report_id} was submitted.`, "Select it from your applications to follow the repair.");
    form.reset();
    await loadReports();
    await openReport(report.report_id);
  } catch (error) {
    showMessage("report-message", "error", "Report not submitted", error.message);
  } finally {
    setBusy(form, false);
  }
});

document.querySelector("#status-update-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!currentReportId) return;
  const form = event.currentTarget;
  hideMessage("status-message");
  setBusy(form, true);
  const values = Object.fromEntries(new FormData(form));
  if (!values.note) values.note = null;
  try {
    const report = await gatewayRequest(
      `/api/v1/fault-reports/${encodeURIComponent(currentReportId)}/status`,
      {method: "PATCH", headers: {"Content-Type": "application/json"}, body: JSON.stringify(values)}
    );
    renderReport(report);
    renderReportList(await gatewayRequest("/api/v1/fault-reports"));
    showMessage("status-message", "success", `Status updated to ${readable(report.status)}.`);
    form.reset();
  } catch (error) {
    showMessage("status-message", "error", "Status not updated", error.message);
  } finally {
    setBusy(form, false);
  }
});

document.querySelector("#cancel-report-button")?.addEventListener("click", async (event) => {
  if (!currentReportId) return;
  const confirmed = window.confirm(
    "Cancel this fault report? This action will be added to the case timeline."
  );
  if (!confirmed) return;
  const button = event.currentTarget;
  button.disabled = true;
  hideMessage("cancel-message");
  try {
    const report = await gatewayRequest(
      `/api/v1/fault-reports/${encodeURIComponent(currentReportId)}/cancel`,
      {method: "POST"}
    );
    renderReport(report);
    renderReportList(await gatewayRequest("/api/v1/fault-reports"));
    showMessage(
      "cancel-message",
      "success",
      "Application cancelled",
      "The cancellation now appears in the case timeline."
    );
  } catch (error) {
    showMessage("cancel-message", "error", "Application not cancelled", error.message);
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#user-report-list, #admin-report-list")?.addEventListener("click", (event) => {
  const item = event.target.closest("[data-report-id]");
  if (item) openReport(item.dataset.reportId);
});

document.querySelectorAll("[data-refresh-reports]").forEach((button) => {
  button.addEventListener("click", loadReports);
});

document.querySelector("[data-close-report]")?.addEventListener("click", () => {
  document.querySelector("#gas-report").hidden = true;
  currentReportId = null;
});

if (page === "user") {
  const citizenId = sessionStorage.getItem(citizenStorageKey);
  if (!citizenId) {
    window.location.replace("/services/gas-fault");
  } else {
    document.querySelector("[data-citizen-label]").textContent = citizenId;
    loadReports();
  }
} else if (page === "admin") {
  loadReports();
}
