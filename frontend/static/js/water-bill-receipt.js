const receiptWorkspace = document.querySelector("[data-water-receipt-page]");

if (receiptWorkspace) {
  const billId = receiptWorkspace.dataset.billId;
  const message = receiptWorkspace.querySelector("[data-water-message]");
  const receipt = receiptWorkspace.querySelector("[data-water-receipt]");
  const details = receiptWorkspace.querySelector("[data-water-receipt-details]");
  const amount = receiptWorkspace.querySelector("[data-water-payment-amount]");
  const pdfLink = receiptWorkspace.querySelector("[data-water-pdf-download]");
  const gatewayUrl = window.SERVICE_UNIVERSE?.gatewayUrl;

  function setMessage(text, state = "info") {
    message.textContent = text;
    message.dataset.state = state;
  }

  function textElement(tag, text) {
    const element = document.createElement(tag);
    element.textContent = text;
    return element;
  }

  function money(amountMinor, currency) {
    return new Intl.NumberFormat("en-AU", {
      style: "currency",
      currency
    }).format(amountMinor / 100);
  }

  function addDetail(label, value) {
    details.append(textElement("dt", label), textElement("dd", value));
  }

  async function loadReceipt() {
    if (!gatewayUrl) {
      setMessage("Gateway is not configured.", "error");
      return;
    }
    try {
      const response = await fetch(
        gatewayUrl + "/api/v1/bills/" + encodeURIComponent(billId) + "/receipt",
        { headers: { Accept: "application/json" } }
      );
      const payload = await response.json();
      if (!response.ok || !payload.success) {
        throw new Error(payload.error?.message || "The receipt could not be loaded.");
      }
      const payment = payload.data;
      amount.textContent = money(payment.amount_minor, payment.currency);
      addDetail("Receipt number", payment.receipt_number);
      addDetail("Payment reference", payment.payment_id);
      addDetail("Bill reference", payment.bill_id);
      addDetail("Payment method", payment.payment_method.replace("_", " "));
      addDetail("Payment date", new Date(payment.paid_at).toLocaleString("en-AU"));
      // PDF 也走 Gateway 下载，浏览器不会直接访问内部水费服务地址。
      pdfLink.href = (
        gatewayUrl +
        "/api/v1/bills/" +
        encodeURIComponent(billId) +
        "/receipt.pdf"
      );
      receipt.hidden = false;
      setMessage("Receipt loaded.");
    } catch (error) {
      setMessage(error.message, "error");
    }
  }

  loadReceipt();
}
