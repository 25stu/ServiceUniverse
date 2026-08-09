const billDetailWorkspace = document.querySelector("[data-water-bill-detail]");

if (billDetailWorkspace) {
  const billId = billDetailWorkspace.dataset.billId;
  const content = billDetailWorkspace.querySelector("[data-water-bill-content]");
  const message = billDetailWorkspace.querySelector("[data-water-message]");
  const reference = billDetailWorkspace.querySelector("[data-water-bill-reference]");
  const gatewayUrl = window.SERVICE_UNIVERSE?.gatewayUrl;

  function setMessage(text, state = "info") {
    message.textContent = text;
    message.dataset.state = state;
  }

  function textElement(tag, text, className) {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    return element;
  }

  function money(amountMinor, currency) {
    return new Intl.NumberFormat("en-AU", {
      style: "currency",
      currency
    }).format(amountMinor / 100);
  }

  async function request(path, options = {}) {
    if (!gatewayUrl) throw new Error("Gateway is not configured.");
    // 详情页也只调用 Gateway，和账单列表页保持同一种调用方式。
    const response = await fetch(gatewayUrl + path, {
      headers: { Accept: "application/json", ...options.headers },
      ...options
    });
    const payload = await response.json();
    if (!response.ok || !payload.success) {
      throw new Error(payload.error?.message || "The request could not be completed.");
    }
    return payload.data;
  }

  function addDefinitionListRow(list, label, value) {
    list.append(textElement("dt", label), textElement("dd", value));
  }

  function addChargeRow(table, label, amount, isTotal = false) {
    const row = document.createElement("div");
    row.className = isTotal ? "water-charge-row water-charge-total" : "water-charge-row";
    row.append(textElement("span", label), textElement("strong", amount));
    table.append(row);
  }

  function renderBill(bill) {
    reference.textContent = bill.bill_id;
    const summary = document.createElement("section");
    summary.className = "water-statement-summary";
    summary.append(
      textElement("p", bill.customer_name, "water-statement-customer"),
      textElement("p", bill.service_address, "water-statement-address")
    );

    const accountGrid = document.createElement("dl");
    accountGrid.className = "water-statement-facts";
    addDefinitionListRow(accountGrid, "Account reference", bill.account_reference);
    addDefinitionListRow(accountGrid, "Meter number", bill.meter_number);
    addDefinitionListRow(
      accountGrid,
      "Billing period",
      bill.billing_period_start + " to " + bill.billing_period_end
    );
    addDefinitionListRow(accountGrid, "Payment due", bill.due_on);
    summary.append(accountGrid);

    const usage = document.createElement("section");
    usage.className = "water-statement-section";
    usage.append(textElement("h2", "Water usage"));
    const usageGrid = document.createElement("dl");
    usageGrid.className = "water-statement-facts";
    addDefinitionListRow(usageGrid, "Previous reading", String(bill.previous_meter_reading));
    addDefinitionListRow(usageGrid, "Current reading", String(bill.current_meter_reading));
    addDefinitionListRow(usageGrid, "Usage", bill.water_usage_kl + " kL");
    addDefinitionListRow(usageGrid, "Service", bill.description);
    usage.append(usageGrid);

    const charges = document.createElement("section");
    charges.className = "water-statement-section";
    charges.append(textElement("h2", "Charges"));
    const chargeTable = document.createElement("div");
    chargeTable.className = "water-charge-table";
    addChargeRow(
      chargeTable,
      "Fixed service charge",
      money(bill.fixed_charge_minor, bill.currency)
    );
    addChargeRow(
      chargeTable,
      "Water consumption",
      money(bill.consumption_charge_minor, bill.currency)
    );
    addChargeRow(chargeTable, "GST", money(bill.gst_minor, bill.currency));
    addChargeRow(chargeTable, "Total amount", money(bill.amount_minor, bill.currency), true);
    charges.append(chargeTable);

    const action = document.createElement("section");
    action.className = "water-payment-panel";
    const status = textElement(
      "p",
      bill.status === "paid" ? "This bill has been paid." : "Payment is due by " + bill.due_on,
      "water-payment-status"
    );
    action.append(status);
    if (bill.status === "unpaid") {
      const payButton = textElement("button", "Pay " + money(bill.amount_minor, bill.currency), "water-primary-action");
      payButton.type = "button";
      payButton.addEventListener("click", async () => {
        // 点完先禁用按钮，避免用户连续点击造成重复付款请求。
        payButton.disabled = true;
        setMessage("Processing payment…");
        try {
          const payment = await request("/api/v1/payments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // 当前页面没有支付方式选择，演示流程固定使用 card。
            body: JSON.stringify({ bill_id: bill.bill_id, payment_method: "card" })
          });
          window.location.assign(
            "/services/water-billing/bills/" +
              encodeURIComponent(payment.bill_id) +
              "/receipt"
          );
        } catch (error) {
          payButton.disabled = false;
          setMessage(error.message, "error");
        }
      });
      action.append(payButton);
    } else {
      const receiptLink = document.createElement("a");
      receiptLink.className = "water-secondary-action";
      receiptLink.href = (
        "/services/water-billing/bills/" +
        encodeURIComponent(bill.bill_id) +
        "/receipt"
      );
      receiptLink.textContent = "View payment receipt";
      action.append(receiptLink);
    }

    content.replaceChildren(summary, usage, charges, action);
  }

  async function loadBill() {
    try {
      const bill = await request("/api/v1/bills/" + encodeURIComponent(billId));
      renderBill(bill);
      setMessage("Bill details loaded.");
    } catch (error) {
      content.replaceChildren();
      setMessage(error.message, "error");
    }
  }

  loadBill();
}
