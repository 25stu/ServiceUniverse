const waterWorkspace = document.querySelector("[data-water-billing]");

if (waterWorkspace) {
  const billForm = waterWorkspace.querySelector("[data-water-bill-form]");
  const citizenInput = waterWorkspace.querySelector("#citizen-id");
  const message = waterWorkspace.querySelector("[data-water-message]");
  const billsElement = waterWorkspace.querySelector("[data-water-bills]");
  const gatewayUrl = window.SERVICE_UNIVERSE?.gatewayUrl;

  function setMessage(text, state = "info") {
    message.textContent = text;
    message.dataset.state = state;
  }

  function formatMoney(amountMinor, currency) {
    return new Intl.NumberFormat("en-AU", {
      style: "currency",
      currency
    }).format(amountMinor / 100);
  }

  function createTextElement(tag, text, className) {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    return element;
  }

  function createLink(text, href, className) {
    const element = document.createElement("a");
    element.textContent = text;
    element.href = href;
    element.className = className;
    return element;
  }

  function renderBills(bills) {
    billsElement.replaceChildren();
    if (!bills.length) {
      billsElement.append(createTextElement("p", "No bills were found for this citizen ID."));
      return;
    }

    bills.forEach((bill) => {
      const card = document.createElement("article");
      card.className = "water-bill";
      const copy = document.createElement("div");
      copy.append(
        createTextElement("h3", bill.description),
        createTextElement(
          "p",
          `${bill.bill_id} · Account ${bill.account_reference} · Due ${bill.due_on}`,
          "water-bill-meta"
        )
      );

      const action = document.createElement("div");
      const status = createTextElement("div", bill.status, "water-bill-status");
      const amount = createTextElement(
        "p",
        formatMoney(bill.amount_minor, bill.currency),
        "water-bill-amount"
      );
      action.append(status, amount);
      const detailPath = "/services/water-billing/bills/" + encodeURIComponent(bill.bill_id);
      if (bill.status === "unpaid") {
        action.append(createLink("View bill", detailPath, "water-bill-link"));
      } else {
        action.append(
          createLink("View receipt", detailPath + "/receipt", "water-bill-link")
        );
      }
      card.append(copy, action);
      billsElement.append(card);
    });
  }

  async function request(path, options = {}) {
    if (!gatewayUrl) throw new Error("Gateway is not configured.");
    // 页面统一经 Gateway 请求，不直接连水费服务。
    const response = await fetch(`${gatewayUrl}${path}`, {
      headers: { Accept: "application/json", ...options.headers },
      ...options
    });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      throw new Error(payload.error?.message || "The request could not be completed.");
    }
    return payload.data;
  }

  async function loadBills() {
    const citizenId = citizenInput.value.trim();
    if (!citizenId) {
      setMessage("Enter a citizen ID before searching.", "error");
      return;
    }
    setMessage("Loading bills…");
    try {
      // 查询条件编码后再拼到地址里，避免输入里的特殊字符影响请求。
      const bills = await request(`/api/v1/bills?citizen_id=${encodeURIComponent(citizenId)}`);
      renderBills(bills);
      setMessage(`${bills.length} bill${bills.length === 1 ? "" : "s"} retrieved.`);
    } catch (error) {
      billsElement.replaceChildren();
      setMessage(error.message, "error");
    }
  }

  billForm.addEventListener("submit", (event) => {
    event.preventDefault();
    loadBills();
  });

  loadBills();
}
