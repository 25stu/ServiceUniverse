from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from services.water_billing.app.database import get_session
from services.water_billing.app.schemas import (
    BillDetailResponse,
    BillResponse,
    PaymentCreate,
    PaymentReceipt,
)
from services.water_billing.app.services.billing import (
    build_receipt_pdf,
    create_payment,
    get_bill_detail,
    get_payment,
    get_payment_for_bill,
    list_bills,
)

router = APIRouter(prefix="/api/v1", tags=["Water Billing"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/bills", response_model=list[BillResponse])
def read_bills(
    citizen_id: Annotated[str, Query(min_length=1, max_length=64)],
    session: SessionDependency,
) -> list[BillResponse]:
    return list_bills(session, citizen_id)


@router.get("/bills/{bill_id}", response_model=BillDetailResponse)
def read_bill(bill_id: str, session: SessionDependency) -> BillDetailResponse:
    return get_bill_detail(session, bill_id)


@router.get("/bills/{bill_id}/receipt", response_model=PaymentReceipt)
def read_bill_receipt(
    bill_id: str, session: SessionDependency
) -> PaymentReceipt:
    return get_payment_for_bill(session, bill_id)


@router.get("/bills/{bill_id}/receipt.pdf")
def download_bill_receipt(
    bill_id: str, session: SessionDependency
) -> Response:
    payment = get_payment_for_bill(session, bill_id)
    bill = get_bill_detail(session, bill_id)
    # PDF 是文件内容，直接用 Response 返回才能让浏览器按附件下载。
    return Response(
        content=build_receipt_pdf(payment, bill),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="water-payment-{payment.receipt_number}.pdf"'
            )
        },
    )


@router.post(
    "/payments",
    response_model=PaymentReceipt,
    status_code=status.HTTP_201_CREATED,
)
def pay_bill(
    request: PaymentCreate,
    session: SessionDependency,
) -> PaymentReceipt:
    # 具体的状态检查和数据库提交都放在业务层，路由只负责接收请求。
    return create_payment(session, request)


@router.get("/payments/{payment_id}", response_model=PaymentReceipt)
def read_payment(
    payment_id: str,
    session: SessionDependency,
) -> PaymentReceipt:
    return get_payment(session, payment_id)
