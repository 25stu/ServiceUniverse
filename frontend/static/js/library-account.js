const workspace = document.querySelector("[data-library-workspace]");

if (workspace) {
  const gatewayUrl = window.SERVICE_UNIVERSE?.gatewayUrl?.replace(/\/$/, "");
  const membershipForm = workspace.querySelector("[data-membership-form]");
  const cardType = workspace.querySelector("[data-card-type]");
  const mailingField = workspace.querySelector("[data-mailing-field]");
  const applicationMessage = workspace.querySelector("[data-application-message]");
  const membershipResult = workspace.querySelector("[data-membership-result]");
  const accountSearch = workspace.querySelector("[data-account-search]");
  const accountMessage = workspace.querySelector("[data-account-message]");
  const accountView = workspace.querySelector("[data-account-view]");
  const accountUpdate = workspace.querySelector("[data-account-update]");
  let currentAccountId = null;

  function requestId() {
    return window.crypto?.randomUUID?.() ?? `web-${Date.now()}`;
  }

  function setMessage(element, text, state = "error") {
    element.textContent = text;
    element.dataset.state = state;
    element.hidden = false;
  }

  function clearMessage(element) {
    element.textContent = "";
    element.hidden = true;
  }

  function formatStatus(value) {
    return String(value ?? "unknown").replaceAll("_", " ");
  }

  async function gatewayRequest(path, options = {}) {
    if (!gatewayUrl) throw new Error("Gateway is not configured.");
    const response = await fetch(`${gatewayUrl}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-Request-ID": requestId(),
        ...options.headers
      }
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok || !payload?.success) {
      throw new Error(payload?.error?.message ?? "The request could not be completed.");
    }
    return payload.data;
  }

  function formPayload(form) {
    return Object.fromEntries(new FormData(form).entries());
  }

  function showAccount(account) {
    currentAccountId = account.account_id;
    workspace.querySelector("[data-account-name]").textContent = account.full_name;
    workspace.querySelector("[data-account-id]").textContent = account.account_id;
    workspace.querySelector("[data-account-status]").textContent = formatStatus(account.status);
    workspace.querySelector("[data-account-card]").textContent = account.card.card_number;
    workspace.querySelector("[data-account-branch]").textContent = account.home_branch;
    workspace.querySelector("[data-account-loans]").textContent = String(account.borrowing.items_on_loan);
    workspace.querySelector("[data-account-access]").textContent = account.borrowing.borrowing_allowed
      ? "Available"
      : "Restricted";
    accountUpdate.elements.email.value = account.email;
    accountUpdate.elements.phone.value = account.phone;
    accountUpdate.elements.preferred_language.value = account.preferred_language;
    accountUpdate.elements.home_branch.value = account.home_branch;
    accountView.hidden = false;
  }

  function updateMailingAddress() {
    const needsAddress = cardType.value === "physical";
    mailingField.hidden = !needsAddress;
    mailingField.querySelector("textarea").required = needsAddress;
  }

  cardType.addEventListener("change", updateMailingAddress);
  updateMailingAddress();

  membershipForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage(applicationMessage);
    membershipResult.hidden = true;
    if (!membershipForm.reportValidity()) return;

    const button = membershipForm.querySelector("button[type='submit']");
    const payload = formPayload(membershipForm);
    payload.identity_verified = membershipForm.elements.identity_verified.checked;
    payload.terms_accepted = membershipForm.elements.terms_accepted.checked;
    payload.payment_confirmed = membershipForm.elements.payment_confirmed.checked;
    if (!payload.mailing_address) delete payload.mailing_address;
    button.disabled = true;
    button.textContent = "Creating membership…";

    try {
      const account = await gatewayRequest("/api/v1/library-memberships", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      workspace.querySelector("[data-confirmation-message]").textContent = account.confirmation_notification;
      workspace.querySelector("[data-created-account]").textContent = account.account_id;
      workspace.querySelector("[data-created-card]").textContent = account.card.card_number;
      workspace.querySelector("[data-created-status]").textContent = formatStatus(account.status);
      membershipResult.hidden = false;
      accountSearch.elements.account_id.value = account.account_id;
      showAccount(account);
      setMessage(applicationMessage, "Your membership is ready.", "success");
    } catch (error) {
      setMessage(applicationMessage, error.message);
    } finally {
      button.disabled = false;
      button.innerHTML = "Create membership <span aria-hidden='true'>→</span>";
    }
  });

  accountSearch.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage(accountMessage);
    accountView.hidden = true;
    if (!accountSearch.reportValidity()) return;

    const button = accountSearch.querySelector("button");
    const accountId = accountSearch.elements.account_id.value.trim();
    button.disabled = true;
    try {
      const account = await gatewayRequest(`/api/v1/library-accounts/${encodeURIComponent(accountId)}`);
      showAccount(account);
      setMessage(accountMessage, "Account found.", "success");
    } catch (error) {
      setMessage(accountMessage, error.message);
    } finally {
      button.disabled = false;
    }
  });

  accountUpdate.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage(accountMessage);
    if (!currentAccountId || !accountUpdate.reportValidity()) return;

    const button = accountUpdate.querySelector("button");
    button.disabled = true;
    try {
      const account = await gatewayRequest(
        `/api/v1/library-accounts/${encodeURIComponent(currentAccountId)}`,
        {method: "PATCH", body: JSON.stringify(formPayload(accountUpdate))}
      );
      showAccount(account);
      setMessage(accountMessage, "Account details updated.", "success");
    } catch (error) {
      setMessage(accountMessage, error.message);
    } finally {
      button.disabled = false;
    }
  });
}
