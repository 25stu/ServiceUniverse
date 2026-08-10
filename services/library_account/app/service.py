from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import uuid4

from services.library_account.app.schemas import (
    AccountStatus,
    AccountUpdate,
    BorrowingSummary,
    CardType,
    LibraryAccount,
    MembershipApplication,
    MembershipCard,
    MembershipPayment,
    PaymentStatus,
    PreferredLanguage,
)


@dataclass(slots=True)
class LibraryDomainError(Exception):
    status_code: int
    code: str
    message: str
    details: dict[str, object] | None = None


class InMemoryAccountRepository:
    def __init__(self) -> None:
        self._accounts: dict[str, LibraryAccount] = {}
        self._account_ids_by_citizen: dict[str, str] = {}
        self._seed_restricted_account()

    def _seed_restricted_account(self) -> None:
        now = datetime.now(UTC)
        account = LibraryAccount(
            account_id="LIB-DEMO-RESTRICTED",
            citizen_id="CIT-RESTRICTED",
            full_name="Restricted Demo Account",
            date_of_birth=date(1990, 1, 1),
            email="restricted@example.invalid",
            phone="+61 400 000 000",
            preferred_language=PreferredLanguage.ENGLISH,
            home_branch="Central Library",
            mailing_address=None,
            status=AccountStatus.RESTRICTED,
            created_at=now,
            activated_at=now,
            card=MembershipCard(
                card_number="CARD-DEMO-RESTRICTED",
                card_type=CardType.DIGITAL,
                issued_at=now,
                delivery_status="issued",
            ),
            payment=MembershipPayment(
                amount_minor=0,
                status=PaymentStatus.NOT_REQUIRED,
                processed_at=now,
            ),
            borrowing=BorrowingSummary(borrowing_allowed=False),
            confirmation_notification="This demonstration account is restricted.",
        )
        self.save(account)

    def save(self, account: LibraryAccount) -> LibraryAccount:
        self._accounts[account.account_id] = account
        self._account_ids_by_citizen[account.citizen_id] = account.account_id
        return account

    def get(self, account_id: str) -> LibraryAccount | None:
        return self._accounts.get(account_id)

    def get_by_citizen(self, citizen_id: str) -> LibraryAccount | None:
        account_id = self._account_ids_by_citizen.get(citizen_id)
        return self._accounts.get(account_id) if account_id else None


class LibraryMembershipService:
    MEMBERSHIP_FEE_MINOR = 500

    def __init__(self, repository: InMemoryAccountRepository) -> None:
        self.repository = repository

    def create_membership(self, application: MembershipApplication) -> LibraryAccount:
        if not application.identity_verified:
            raise LibraryDomainError(
                400,
                "IDENTITY_NOT_VERIFIED",
                "Citizen identity must be verified before membership can be created.",
            )
        if not application.terms_accepted:
            raise LibraryDomainError(
                400,
                "TERMS_NOT_ACCEPTED",
                "Membership terms must be accepted before applying.",
            )

        existing = self.repository.get_by_citizen(application.citizen_id)
        if existing and existing.status in {
            AccountStatus.RESTRICTED,
            AccountStatus.SUSPENDED,
        }:
            raise LibraryDomainError(
                409,
                "ACCOUNT_RESTRICTED",
                (
                    "A restricted or suspended library account already exists "
                    "for this citizen."
                ),
                {"account_status": existing.status.value},
            )
        if existing:
            raise LibraryDomainError(
                409,
                "MEMBERSHIP_ALREADY_EXISTS",
                "A library membership already exists for this citizen.",
                {"account_id": existing.account_id},
            )

        if not application.payment_confirmed:
            raise LibraryDomainError(
                400,
                "PAYMENT_REQUIRED",
                "The simulated AUD 5.00 membership fee must be confirmed.",
                {"amount_minor": self.MEMBERSHIP_FEE_MINOR, "currency": "AUD"},
            )

        now = datetime.now(UTC)
        short_id = uuid4().hex[:12].upper()
        notification = (
            f"会员申请成功。已模拟支付澳元 5.00，您的账户 {short_id} 已激活。"
            if application.preferred_language is PreferredLanguage.CHINESE
            else (
                "Membership confirmed. The simulated AUD 5.00 payment was "
                f"accepted and your account {short_id} is active."
            )
        )
        account = LibraryAccount(
            account_id=f"LIB-{short_id}",
            citizen_id=application.citizen_id,
            full_name=application.full_name,
            date_of_birth=application.date_of_birth,
            email=application.email,
            phone=application.phone,
            preferred_language=application.preferred_language,
            home_branch=application.home_branch,
            mailing_address=application.mailing_address,
            status=AccountStatus.ACTIVE,
            created_at=now,
            activated_at=now,
            card=MembershipCard(
                card_number=f"CARD-{short_id}",
                card_type=application.card_type,
                issued_at=now,
                delivery_status=(
                    "ready_for_delivery"
                    if application.card_type is CardType.PHYSICAL
                    else "issued"
                ),
            ),
            payment=MembershipPayment(
                amount_minor=self.MEMBERSHIP_FEE_MINOR,
                status=PaymentStatus.PAID,
                processed_at=now,
                payment_reference=f"SIM-PAY-{short_id}",
            ),
            borrowing=BorrowingSummary(),
            confirmation_notification=notification,
        )
        return self.repository.save(account)

    def get_account(self, account_id: str) -> LibraryAccount:
        account = self.repository.get(account_id)
        if account is None:
            raise LibraryDomainError(
                404,
                "LIBRARY_ACCOUNT_NOT_FOUND",
                "The requested library account was not found.",
            )
        return account

    def update_account(self, account_id: str, update: AccountUpdate) -> LibraryAccount:
        account = self.get_account(account_id)
        if account.status is AccountStatus.RESTRICTED:
            raise LibraryDomainError(
                409,
                "ACCOUNT_RESTRICTED",
                "Restricted library accounts cannot be updated online.",
            )
        changes = update.model_dump(exclude_none=True)
        updated = account.model_copy(update=changes)
        return self.repository.save(updated)


membership_service = LibraryMembershipService(InMemoryAccountRepository())
