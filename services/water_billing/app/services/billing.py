from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.water_billing.app.models import Bill, Payment
from services.water_billing.app.schemas import BillDetailResponse, PaymentCreate


class WaterBillingError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def list_bills(session: Session, citizen_id: str) -> list[Bill]:
    return (
        session.query(Bill)
        .filter(Bill.citizen_id == citizen_id)
        .order_by(Bill.due_on.desc())
        .all()
    )


def get_bill(session: Session, bill_id: str) -> Bill:
    bill = session.get(Bill, bill_id)
    if bill is None:
        raise WaterBillingError(
            404,
            "BILL_NOT_FOUND",
            "The requested bill was not found.",
        )
    return bill


def get_bill_detail(session: Session, bill_id: str) -> BillDetailResponse:
    bill = get_bill(session, bill_id)
    # 这几条演示账单有固定的明细，方便前端展示不同的用水情况。
    detail_by_bill = {
        "BILL-1001": {
            "customer_name": "Alex Morgan",
            "service_address": "14 Harbour Street, Sydney NSW 2000",
            "meter_number": "WTR-2048-77",
            "billing_period_start": bill.issued_on.replace(month=4, day=1),
            "billing_period_end": bill.issued_on.replace(month=6, day=30),
            "previous_meter_reading": 18420,
            "current_meter_reading": 18572,
            "water_usage_kl": 152,
            "fixed_charge_minor": 2800,
            "consumption_charge_minor": 8723,
            "gst_minor": 1127,
        },
        "BILL-1002": {
            "customer_name": "Alex Morgan",
            "service_address": "14 Harbour Street, Sydney NSW 2000",
            "meter_number": "WTR-2048-77",
            "billing_period_start": bill.issued_on.replace(month=5, day=1),
            "billing_period_end": bill.issued_on.replace(month=5, day=31),
            "previous_meter_reading": 18420,
            "current_meter_reading": 18420,
            "water_usage_kl": 0,
            "fixed_charge_minor": 3455,
            "consumption_charge_minor": 0,
            "gst_minor": 345,
        },
        "BILL-2001": {
            "customer_name": "Jordan Lee",
            "service_address": "8 Market Lane, Parramatta NSW 2150",
            "meter_number": "WTR-8831-41",
            "billing_period_start": bill.issued_on.replace(month=4, day=1),
            "billing_period_end": bill.issued_on.replace(month=6, day=30),
            "previous_meter_reading": 8920,
            "current_meter_reading": 9031,
            "water_usage_kl": 111,
            "fixed_charge_minor": 2400,
            "consumption_charge_minor": 6168,
            "gst_minor": 857,
        },
    }
    profiles = {
        "CITIZEN-1001": (
            "Alex Morgan",
            "14 Harbour Street, Sydney NSW 2000",
            "WTR-2048-77",
            18420,
        ),
        "CITIZEN-2001": (
            "Jordan Lee",
            "8 Market Lane, Parramatta NSW 2150",
            "WTR-8831-41",
            8920,
        ),
        "CITIZEN-3001": (
            "Samira Patel",
            "22 Garden Avenue, Chatswood NSW 2067",
            "WTR-5190-18",
            12640,
        ),
    }
    # 其他预设账单共用市民的基本资料，避免账单详情页出现空信息。
    customer_name, service_address, meter_number, base_reading = profiles.get(
        bill.citizen_id,
        (
            "Water Billing Customer",
            "Address held by the Municipal Utilities Authority",
            bill.account_reference,
            0,
        ),
    )
    fixed_charge = 2800 if bill.citizen_id == "CITIZEN-1001" else 2400
    if "connection" in bill.description.lower():
        fixed_charge = 3455
    gst = bill.amount_minor // 11
    consumption_charge = max(0, bill.amount_minor - fixed_charge - gst)
    usage = consumption_charge // 55
    period_start = bill.issued_on.replace(
        month=max(1, bill.issued_on.month - 3),
        day=1,
    )
    # 没有单独写明细的账单，就按金额拼一份默认明细给演示页面使用。
    default_detail = {
        "customer_name": customer_name,
        "service_address": service_address,
        "meter_number": meter_number,
        "billing_period_start": period_start,
        "billing_period_end": bill.issued_on,
        "previous_meter_reading": base_reading,
        "current_meter_reading": base_reading + usage,
        "water_usage_kl": usage,
        "fixed_charge_minor": fixed_charge,
        "consumption_charge_minor": consumption_charge,
        "gst_minor": gst,
    }
    detail = detail_by_bill.get(bill.bill_id, default_detail)
    return BillDetailResponse(
        **{
            "bill_id": bill.bill_id,
            "citizen_id": bill.citizen_id,
            "account_reference": bill.account_reference,
            "description": bill.description,
            "issued_on": bill.issued_on,
            "due_on": bill.due_on,
            "amount_minor": bill.amount_minor,
            "currency": bill.currency,
            "status": bill.status,
            "paid_at": bill.paid_at,
        },
        **detail,
    )


def create_payment(session: Session, request: PaymentCreate) -> Payment:
    bill = get_bill(session, request.bill_id)
    # 已缴账单先直接拦住，不能在页面上重复付款。
    if bill.status != "unpaid":
        raise WaterBillingError(
            409,
            "BILL_ALREADY_PAID",
            "This bill has already been paid and cannot be paid again.",
        )

    paid_at = datetime.now(UTC)
    # 付款记录和账单状态会在同一次提交里一起更新，避免只改到其中一个。
    payment = Payment(
        payment_id=f"PAY-{uuid4().hex[:12].upper()}",
        bill_id=bill.bill_id,
        citizen_id=bill.citizen_id,
        amount_minor=bill.amount_minor,
        currency=bill.currency,
        payment_method=request.payment_method,
        status="completed",
        paid_at=paid_at,
        receipt_number=f"RCT-{uuid4().hex[:12].upper()}",
    )
    bill.status = "paid"
    bill.paid_at = paid_at
    session.add(payment)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        # 数据库也限制一张账单只能有一笔付款，用来防止两个请求刚好同时进来。
        raise WaterBillingError(
            409,
            "BILL_ALREADY_PAID",
            "This bill has already been paid and cannot be paid again.",
        ) from error
    session.refresh(payment)
    return payment


def get_payment(session: Session, payment_id: str) -> Payment:
    payment = session.get(Payment, payment_id)
    if payment is None:
        raise WaterBillingError(
            404,
            "PAYMENT_NOT_FOUND",
            "The requested payment receipt was not found.",
        )
    return payment


def get_payment_for_bill(session: Session, bill_id: str) -> Payment:
    get_bill(session, bill_id)
    payment = session.query(Payment).filter(Payment.bill_id == bill_id).one_or_none()
    if payment is None:
        raise WaterBillingError(
            404,
            "RECEIPT_NOT_FOUND",
            "No payment receipt is available for this bill.",
        )
    return payment


def build_receipt_pdf(payment: Payment, bill: BillDetailResponse) -> bytes:
    """Create a polished A4 receipt aligned with the citizen-facing receipt page."""

    # PDF 和网页回执都用同一份付款、账单数据，展示出来不会对不上。
    paper = HexColor("#F4F0E6")
    navy = HexColor("#152B3A")
    soft_ink = HexColor("#4C5E68")
    green = HexColor("#3D7563")
    line = HexColor("#B9B4A9")
    buffer = BytesIO()
    page_width, page_height = A4
    canvas = Canvas(buffer, pagesize=A4, pageCompression=1)

    canvas.setFillColor(paper)
    canvas.rect(0, 0, page_width, page_height, stroke=0, fill=1)
    canvas.setFillColor(navy)
    canvas.rect(0, page_height - 132, page_width, 132, stroke=0, fill=1)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(52, page_height - 48, "SERVICEUNIVERSE")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(
        page_width - 52, page_height - 48, "Municipal Utilities Authority"
    )
    canvas.setFont("Helvetica-Bold", 27)
    canvas.drawString(52, page_height - 93, "Payment receipt")

    canvas.setFillColor(soft_ink)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(52, page_height - 164, "PAYMENT COMPLETED")
    canvas.setFillColor(navy)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(52, page_height - 187, payment.receipt_number)
    canvas.setFillColor(green)
    canvas.roundRect(page_width - 176, page_height - 201, 124, 32, 16, stroke=0, fill=1)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(page_width - 114, page_height - 189, "PAID")

    canvas.setStrokeColor(line)
    canvas.line(52, page_height - 224, page_width - 52, page_height - 224)
    canvas.setFillColor(soft_ink)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(52, page_height - 247, "AMOUNT PAID")
    canvas.setFillColor(navy)
    canvas.setFont("Helvetica-Bold", 28)
    canvas.drawString(
        52,
        page_height - 280,
        f"{payment.currency} {payment.amount_minor / 100:.2f}",
    )
    canvas.setFillColor(soft_ink)
    canvas.setFont("Helvetica", 9)
    payment_method = payment.payment_method.replace("_", " ").title()
    canvas.drawString(52, page_height - 300, "Paid by " + payment_method)

    canvas.setFillColor(navy)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(52, page_height - 346, "Receipt details")
    paid_at = payment.paid_at.strftime("%d %b %Y, %H:%M UTC")
    receipt_rows = [
        ("Payment ID", payment.payment_id),
        ("Bill ID", payment.bill_id),
        ("Account", bill.account_reference),
        ("Customer", bill.customer_name),
        ("Paid at", paid_at),
    ]
    y = page_height - 374
    for label, value in receipt_rows:
        canvas.setFillColor(soft_ink)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(52, y, label.upper())
        canvas.setFillColor(navy)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(178, y, value)
        canvas.setStrokeColor(line)
        canvas.line(52, y - 12, page_width - 52, y - 12)
        y -= 31

    canvas.setFillColor(navy)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(52, y - 18, "Bill summary")
    canvas.setFillColor(soft_ink)
    canvas.setFont("Helvetica", 10)
    canvas.drawString(52, y - 42, bill.description)
    canvas.drawString(52, y - 59, bill.service_address)
    billing_period = (
        f"Billing period: {bill.billing_period_start:%d %b} - "
        f"{bill.billing_period_end:%d %b %Y}"
    )
    canvas.drawRightString(page_width - 52, y - 42, billing_period)
    canvas.setStrokeColor(line)
    canvas.line(52, y - 76, page_width - 52, y - 76)

    charge_rows = [
        ("Fixed service charge", bill.fixed_charge_minor),
        ("Water consumption", bill.consumption_charge_minor),
        ("GST", bill.gst_minor),
    ]
    row_y = y - 101
    for label, amount_minor in charge_rows:
        canvas.setFillColor(soft_ink)
        canvas.setFont("Helvetica", 9)
        canvas.drawString(52, row_y, label)
        canvas.drawRightString(page_width - 52, row_y, f"AUD {amount_minor / 100:.2f}")
        row_y -= 20
    canvas.setStrokeColor(navy)
    canvas.line(52, row_y + 5, page_width - 52, row_y + 5)
    canvas.setFillColor(navy)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(52, row_y - 15, "TOTAL PAID")
    canvas.drawRightString(
        page_width - 52, row_y - 15, f"AUD {payment.amount_minor / 100:.2f}"
    )

    canvas.setStrokeColor(line)
    canvas.line(52, 80, page_width - 52, 80)
    canvas.setFillColor(soft_ink)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(52, 61, "Keep this receipt for your records.")
    canvas.drawRightString(page_width - 52, 61, "ServiceUniverse - Water Billing")
    canvas.save()
    return buffer.getvalue()
