const billingGateway = window.SERVICE_UNIVERSE?.gatewayUrl;
const billingMessage = document.querySelector("[data-billing-message]");
const billingResult = document.querySelector("[data-billing-result]");
const createSessionForm = document.querySelector("[data-create-session]");
const findSessionForm = document.querySelector("[data-find-session]");
let selectedSession = null;

function setBillingMessage(message, state = "ready") {
  billingMessage.textContent = message;
  billingMessage.dataset.state = state;
}

async function billingRequest(path, options = {}) {
  const response = await fetch(`${billingGateway}${path}`, {
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    ...options
  });
  const payload = await response.json();
  if (!response.ok || !payload.success) {
    throw new Error(payload.error?.message ?? "The parking billing request failed.");
  }
  return payload.data;
}

function detail(label, value) {
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value ?? "—";
  return [term, description];
}

function renderSession(parkingSession) {
  selectedSession = parkingSession;
  billingResult.replaceChildren();
  const list = document.createElement("dl");
  [
    detail("Session", parkingSession.session_id),
    detail("Vehicle", parkingSession.vehicle_plate),
    detail("Status", parkingSession.status),
    detail("Payment", parkingSession.payment_status),
    detail("Duration", parkingSession.duration_minutes ? `${parkingSession.duration_minutes} minutes` : "Active"),
    detail("Amount", parkingSession.amount_minor == null ? "Not calculated" : `AUD ${(parkingSession.amount_minor / 100).toFixed(2)}`)
  ].forEach((pair) => list.append(...pair));
  billingResult.append(list);

  const actions = document.createElement("div");
  actions.className = "billing-actions";
  if (parkingSession.status === "active") {
    const endButton = document.createElement("button");
    endButton.type = "button";
    endButton.textContent = "End and calculate fee";
    endButton.addEventListener("click", endSelectedSession);
    actions.append(endButton);
  }
  if (parkingSession.status === "completed" && parkingSession.payment_status === "unpaid") {
    const payButton = document.createElement("button");
    payButton.type = "button";
    payButton.textContent = "Pay by card";
    payButton.addEventListener("click", paySelectedSession);
    actions.append(payButton);
  }
  billingResult.append(actions);
}

async function loadSession(sessionId) {
  const parkingSession = await billingRequest(`/api/v1/parking-sessions/${sessionId}`);
  renderSession(parkingSession);
  findSessionForm.elements.session_id.value = sessionId;
  return parkingSession;
}

async function endSelectedSession() {
  try {
    const parkingSession = await billingRequest(`/api/v1/parking-sessions/${selectedSession.session_id}/end`, {
      method: "POST",
      body: JSON.stringify({})
    });
    renderSession(parkingSession);
    setBillingMessage("Session ended and fee calculated.");
  } catch (error) {
    setBillingMessage(error.message, "error");
  }
}

async function paySelectedSession() {
  try {
    await billingRequest("/api/v1/parking-payments", {
      method: "POST",
      body: JSON.stringify({ session_id: selectedSession.session_id, payment_method: "card" })
    });
    await loadSession(selectedSession.session_id);
    setBillingMessage("Payment completed.");
  } catch (error) {
    setBillingMessage(error.message, "error");
  }
}

createSessionForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(createSessionForm);
  try {
    const parkingSession = await billingRequest("/api/v1/parking-sessions", {
      method: "POST",
      body: JSON.stringify({
        citizen_id: formData.get("citizen_id"),
        vehicle_plate: formData.get("vehicle_plate"),
        parking_lot_id: formData.get("parking_lot_id")
      })
    });
    renderSession(parkingSession);
    findSessionForm.elements.session_id.value = parkingSession.session_id;
    setBillingMessage("Parking session started. Save the session ID shown on the right.");
  } catch (error) {
    setBillingMessage(error.message, "error");
  }
});

findSessionForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const sessionId = new FormData(findSessionForm).get("session_id");
  try {
    await loadSession(sessionId);
    setBillingMessage("Parking session found.");
  } catch (error) {
    setBillingMessage(error.message, "error");
  }
});
