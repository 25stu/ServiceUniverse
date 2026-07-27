const platformStatus = document.querySelector("[data-platform-status]");
const platformStatusLabel = document.querySelector("[data-platform-status-label]");

function setPlatformStatus(state, label) {
  if (!platformStatus || !platformStatusLabel) return;
  platformStatus.dataset.platformStatus = state;
  platformStatusLabel.textContent = label;
}

function updateServiceStatus(slug, state) {
  document.querySelectorAll(`[data-service-slug="${slug}"]`).forEach((element) => {
    element.dataset.serviceState = state;
    const label = element.querySelector("[data-service-status]");
    if (label) {
      label.textContent = state === "healthy" ? "Service online" : "Service unavailable";
    }
  });
}

async function loadPlatformHealth() {
  const gatewayUrl = window.SERVICE_UNIVERSE?.gatewayUrl;
  if (!gatewayUrl) {
    setPlatformStatus("unavailable", "Gateway not configured");
    return;
  }

  try {
    const response = await fetch(`${gatewayUrl}/api/v1/health`, {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) throw new Error(`Gateway returned ${response.status}`);

    const payload = await response.json();
    const state = payload.data?.overall_status ?? "degraded";
    setPlatformStatus(
      state,
      state === "healthy" ? "All services online" : "Some services unavailable"
    );

    Object.entries(payload.data?.services ?? {}).forEach(([slug, service]) => {
      updateServiceStatus(slug, service.status);
    });
  } catch {
    setPlatformStatus("unavailable", "Gateway unavailable");
  }
}

loadPlatformHealth();
