"""
FACILITAPAY PYDANTIC MODELS
============================
Data models for FacilitaPay Colombia COP operations.
Covers: subjects (person/company), bank accounts, transactions (PSE pay-in + COP payout),
and webhook payloads. All field names match the FacilitaPay API exactly.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class FPDocumentType(str, Enum):
    """Colombian document types accepted by FacilitaPay."""
    CC = "cc"     # Cédula de Ciudadanía (natural citizens, 10 digits)
    CE = "ce"     # Cédula de Extranjería (foreign citizens, 6-9 digits)
    NIT = "nit"   # Tax ID for companies (10 digits)


class FPAccountType(str, Enum):
    """Bank account types. FacilitaPay uses Portuguese naming internally."""
    CHECKING = "conta-corrente"
    SAVINGS = "poupanca"
    SALARY = "salary"
    PAYMENT = "payment"


class FPTransactionStatus(str, Enum):
    """
    FacilitaPay transaction lifecycle statuses.
    
    Pay-In:  pending → identified → exchanged → wired
    Pay-Out: pending → identified → exchanged → wired
    Either can → canceled at any point.
    """
    PENDING = "pending"       # No payment received / insufficient balance
    IDENTIFIED = "identified" # Funds received (pay-in) or balance allocated (payout)
    EXCHANGED = "exchanged"   # Currency converted
    WIRED = "wired"           # Funds sent to destination (terminal)
    CANCELED = "canceled"     # Transaction reversed (terminal)


class FPSubjectStatus(str, Enum):
    """Subject (customer) verification status."""
    APPROVED = "approved"
    PENDING = "pending"
    REPROVED = "reproved"


class FPTransactionDirection(str, Enum):
    """Internal tracking of transaction direction."""
    PAYIN = "payin"
    PAYOUT = "payout"


# =============================================================================
# SUBJECT (PERSON / COMPANY)
# =============================================================================

class FPSubjectPerson(BaseModel):
    """
    Colombian person subject — maps to POST /subject/people response.
    
    Minimum required for PSE transactions:
    - document_number, document_type, social_name, fiscal_country
    - address_street, address_number, email, phone_area_code, phone_number
    """
    id: str                                    # UUID — subject_id
    social_name: str
    document_number: str
    document_type: FPDocumentType
    fiscal_country: str = "Colombia"
    status: FPSubjectStatus = FPSubjectStatus.PENDING
    clearance_level: int = 0
    required_clearance_level: int = 0
    email: str | None = None
    phone_area_code: str | None = None
    phone_number: str | None = None
    phone_country_code: str | None = None
    address_street: str | None = None
    address_number: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_postal_code: str | None = None
    address_country: str | None = None
    address_complement: str | None = None
    address_neighborhood: str | None = None
    birth_date: str | None = None
    net_monthly_average_income: str | None = None
    inserted_at: str | None = None
    updated_at: str | None = None
    references: list[Any] = Field(default_factory=list)
    documents: list[Any] = Field(default_factory=list)

    class Config:
        extra = "allow"  # FacilitaPay may add new fields


class FPSubjectCompany(BaseModel):
    """Colombian company subject — maps to POST /subject/companies response."""
    id: str
    social_name: str
    document_number: str                       # NIT (10 digits)
    document_type: FPDocumentType = FPDocumentType.NIT
    fiscal_country: str = "Colombia"
    status: FPSubjectStatus = FPSubjectStatus.PENDING
    clearance_level: int = 0
    inserted_at: str | None = None
    updated_at: str | None = None

    class Config:
        extra = "allow"


# =============================================================================
# BANK ACCOUNTS
# =============================================================================

class FPBankInfo(BaseModel):
    """Bank identification within FacilitaPay."""
    code: str                                  # e.g. "1007" for Bancolombia
    name: str                                  # e.g. "BANCOLOMBIA"
    id: str | None = None                      # FP bank UUID
    country: str = "COL"
    swift: str | None = None
    ispb: str | None = None

    class Config:
        extra = "allow"


class FPBankAccount(BaseModel):
    """
    Customer bank account — maps to POST /subject/:id/bank_accounts response.
    Used as the destination for COP payouts.
    """
    id: str                                    # UUID — bank_account_id (used in payouts)
    account_number: str
    branch_number: str | None = None
    account_type: str                          # "conta-corrente", "poupanca", etc.
    currency: str = "COP"
    owner_name: str
    owner_document_number: str | None = None
    owner_document_type: str | None = None
    branch_country: str = "COL"
    bank: FPBankInfo
    routing_number: str | None = None
    iban: str | None = None
    nickname: str | None = None

    class Config:
        extra = "allow"


class FPPseBankEntry(BaseModel):
    """Single bank from GET /bank_accounts/pse response."""
    name: str
    code: str


class FPPayoutBankEntry(BaseModel):
    """Single bank from GET /banks/cop response."""
    name: str
    code: str
    ach: bool = True


# =============================================================================
# TRANSACTIONS
# =============================================================================

class FPPseInfo(BaseModel):
    """PSE-specific fields present in PSE pay-in transaction responses."""
    payment_url: str | None = None             # One-time URL, 21-minute TTL
    bank_name: str | None = None
    ticket_id: int | None = None
    trazability_code: str | None = None
    creation_date: str | None = None
    payment_description: str | None = None
    financial_institution_code: str | None = None
    redirect_url: str | None = None

    class Config:
        extra = "allow"


class FPBankTransaction(BaseModel):
    """Bank transfer details embedded in transaction response."""
    id: str | None = None
    value: str | None = None
    movement_date: str | None = None
    currency: str | None = None
    exchange_currency: str | None = None
    exchange_rate: str | None = None
    exchange_rate_spot: str | None = None
    exchanged_value: str | None = None
    exchange_approved: bool = False
    wire_id: str | None = None
    source_name: str | None = None
    source_document_number: str | None = None
    source_document_type: str | None = None

    class Config:
        extra = "allow"


class FPTransaction(BaseModel):
    """
    FacilitaPay transaction — maps to POST/GET /transactions response.
    Used for both PSE pay-in and COP payout transactions.
    
    The `id` field is the primary reconciliation key. The `meta` field
    carries our `pear_order_id` for deterministic order matching.
    """
    id: str                                    # UUID — transaction_id
    status: FPTransactionStatus
    value: str                                 # Amount as string
    currency: str                              # "COP" or "USD"
    exchange_currency: str | None = None
    exchanged_value: str | None = None         # Converted amount in exchange_currency
    subject_id: str | None = None
    subject_is_receiver: bool | None = None

    # PSE pay-in specific
    from_pse: FPPseInfo | None = None

    # Source/destination accounts
    from_bank_account: FPBankAccount | dict | None = None
    to_bank_account: FPBankAccount | dict | None = None

    # Bank transfer (populated after processing)
    bank_transaction: FPBankTransaction | None = None

    # Source identity (from PSE payer or subject)
    source_name: str | None = None
    source_document_number: str | None = None
    source_document_type: str | None = None

    # Custom metadata
    meta: dict | None = None

    # Timestamps
    inserted_at: str | None = None

    # Processing flags
    cleared: bool = False
    for_exchange: bool = False
    exchange_under_request: bool = False
    estimated_value_until_exchange: bool = False

    # Card (unused for PSE/payout but present in response)
    from_credit_card: Any | None = None

    class Config:
        extra = "allow"

    @property
    def pear_order_id(self) -> str | None:
        """Extract pear_order_id from meta if present."""
        if self.meta:
            return self.meta.get("pear_order_id")
        return None


# =============================================================================
# WEBHOOK PAYLOADS
# =============================================================================

class FPWebhookPayload(BaseModel):
    """
    Base webhook notification payload.
    All webhooks have `type` and `secret` fields.
    """
    type: str                                  # "identified", "exchange_created", etc.
    secret: str | None = None                  # Shared secret for verification
    transaction_id: str | None = None          # Present for single-tx events
    transaction_ids: list[str] | None = None   # Present for batched events
    exchange_id: str | None = None             # Present for exchange_created
    wire_id: str | None = None                 # Present for wire_created
    checkout_id: str | None = None             # Present for card events

    class Config:
        extra = "allow"


class FPNotificationEnvelope(BaseModel):
    """Wraps the webhook payload as sent by FacilitaPay: {"notification": {...}}"""
    notification: FPWebhookPayload


class FPNotificationRecord(BaseModel):
    """
    Notification list item from GET /notifications response.
    Used for catching failed webhooks via polling.
    """
    id: str                                    # Notification UUID (dedup key + ACK key)
    url: str
    notification: dict                         # Raw notification payload
    inserted_at: str
    sent_at: str | None = None
    failed_at: str | None = None

    class Config:
        extra = "allow"
