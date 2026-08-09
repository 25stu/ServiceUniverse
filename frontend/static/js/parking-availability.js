const availabilityGateway = window.SERVICE_UNIVERSE?.gatewayUrl;
const parkingLotsContainer = document.querySelector("[data-parking-lots]");
const parkingMessage = document.querySelector("[data-parking-message]");
const refreshParkingButton = document.querySelector("[data-refresh-parking]");

function setParkingMessage(message, state = "ready") {
  if (!parkingMessage) return;
  parkingMessage.textContent = message;
  parkingMessage.dataset.state = state;
}

async function parkingRequest(path, options = {}) {
  const response = await fetch(`${availabilityGateway}${path}`, {
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    ...options
  });
  const payload = await response.json();
  if (!response.ok || !payload.success) {
    throw new Error(payload.error?.message ?? "The parking request failed.");
  }
  return payload.data;
}

function renderParkingLots(parkingLots) {
  parkingLotsContainer.replaceChildren();
  parkingLots.forEach((parkingLot) => {
    const article = document.createElement("article");
    article.className = "parking-card";

    const status = document.createElement("p");
    status.className = "eyebrow";
    status.textContent = parkingLot.availability_status;
    const heading = document.createElement("h3");
    heading.textContent = parkingLot.name;
    const address = document.createElement("address");
    address.textContent = parkingLot.address;
    const count = document.createElement("p");
    count.className = "space-count";
    count.textContent = parkingLot.available_spaces;
    const label = document.createElement("p");
    label.className = "space-label";
    label.textContent = `spaces available of ${parkingLot.total_spaces}`;

    const form = document.createElement("form");
    form.className = "availability-form";
    form.innerHTML = `
      <label class="visually-hidden" for="spaces-${parkingLot.lot_id}">Available spaces</label>
      <input id="spaces-${parkingLot.lot_id}" name="available_spaces" type="number" min="0" max="${parkingLot.total_spaces}" value="${parkingLot.available_spaces}" required>
      <button type="submit">Update</button>`;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await parkingRequest(`/api/v1/parking-lots/${parkingLot.lot_id}/availability`, {
          method: "PATCH",
          body: JSON.stringify({ available_spaces: Number(formData.get("available_spaces")) })
        });
        setParkingMessage(`${parkingLot.name} availability updated.`);
        await loadParkingLots();
      } catch (error) {
        setParkingMessage(error.message, "error");
      }
    });
    article.append(status, heading, address, count, label, form);
    parkingLotsContainer.append(article);
  });
}

async function loadParkingLots() {
  if (!availabilityGateway || !parkingLotsContainer) return;
  setParkingMessage("Loading parking availability…");
  try {
    const parkingLots = await parkingRequest("/api/v1/parking-lots");
    renderParkingLots(parkingLots);
    setParkingMessage(`Showing ${parkingLots.length} public parking lots.`);
  } catch (error) {
    setParkingMessage(error.message, "error");
  }
}

refreshParkingButton?.addEventListener("click", loadParkingLots);
loadParkingLots();
