"""
COP Types & Constants
=====================
Enums, dataclasses, and message templates for the COP module.
Extracted from cop_standalone.py for PearV2.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class COPOrderState(Enum):
    """
    COP order state machine.

    SELL flow:
        AWAITING_INFO → INFO_RECEIVED → LINK_SENT → AWAITING_PAYMENT
        → PAYMENT_RECEIVED → RELEASING → COMPLETED

    BUY flow:
        COLLECTING_BANK_INFO → PAYOUT_PENDING → PAYOUT_SENT
        → MARK_PAID_PENDING → COMPLETED

    Terminal states: COMPLETED, CANCELLED (no outgoing transitions).
    """
    NEW = "new"
    # SELL states
    AWAITING_INFO = "awaiting_info"
    INFO_RECEIVED = "info_received"
    GENERATING_LINK = "generating_link"
    LINK_SENT = "link_sent"
    LINK_EXPIRED = "link_expired"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_RECEIVED = "payment_received"
    RELEASING = "releasing"
    # BUY states
    COLLECTING_BANK_INFO = "collecting_bank_info"
    PAYOUT_PENDING = "payout_pending"
    PAYOUT_SENT = "payout_sent"
    MARK_PAID_PENDING = "mark_paid_pending"
    # Shared terminal/error states
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MANUAL_REVIEW = "manual_review"


@dataclass
class COPOrder:
    """A single COP P2P order being tracked."""
    binance_order_id: str
    binance_external_id: Optional[str] = None
    order_side: str = "SELL"  # "BUY" or "SELL"
    customer_name: Optional[str] = None
    customer_cc: Optional[str] = None
    customer_email: Optional[str] = None
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None
    amount_cop: Optional[str] = None
    amount_usdt: Optional[str] = None
    facilitapay_subject_id: Optional[str] = None
    facilitapay_tx_id: Optional[str] = None
    payment_url: Optional[str] = None
    state: COPOrderState = COPOrderState.NEW
    binance_buyer_name: Optional[str] = None
    created_at: Optional[datetime] = None
    link_expires_at: Optional[datetime] = None
    welcome_sent: bool = False
    chat_messages: list[str] = field(default_factory=list)
    # BUY order fields
    seller_account_number: Optional[str] = None
    seller_account_type: Optional[str] = None  # "savings" or "checking"
    seller_bank_account_id: Optional[str] = None  # FP registered bank account UUID
    facilitapay_payout_tx_id: Optional[str] = None
    payout_sent_at: Optional[datetime] = None
    mark_paid_at: Optional[datetime] = None
    mark_paid_retries: int = 0

    def is_link_expired(self) -> bool:
        if not self.link_expires_at:
            return False
        return datetime.utcnow() > self.link_expires_at

    @property
    def is_buy(self) -> bool:
        return self.order_side == "BUY"


@dataclass
class COPCustomerInfo:
    """Extracted customer information from chat messages."""
    name: Optional[str] = None
    cc: Optional[str] = None           # Cédula de ciudadanía
    email: Optional[str] = None
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None

    def is_complete(self) -> bool:
        return all([self.name, self.cc, self.email, self.bank_code])

    def missing_fields(self) -> list[str]:
        fields = []
        if not self.name:  fields.append("nombre completo")
        if not self.cc:    fields.append("cédula de ciudadanía")
        if not self.email:  fields.append("correo electrónico")
        if not self.bank_code: fields.append("nombre del banco")
        return fields


# FacilitaPay transaction statuses
class COPTransactionStatus(Enum):
    PENDING = "pending"
    IDENTIFIED = "identified"
    EXCHANGED = "exchanged"
    WIRED = "wired"
    CANCELED = "canceled"


@dataclass
class PSEPaymentResult:
    """Result of a PSE payment link generation."""
    success: bool
    transaction_id: Optional[str] = None
    payment_url: Optional[str] = None
    trazability_code: Optional[str] = None
    ticket_id: Optional[int] = None
    error: Optional[str] = None


# ============================================================================
# Chat message templates
# ============================================================================

MESSAGES: dict[str, str] = {
    # ── SELL flow messages (we sell USDT, buyer pays COP via PSE) ──
    "welcome": """¡Hola! Para procesar tu compra de {usdt} USDT necesito los siguientes datos:

- Nombre completo (como aparece en tu cédula)
- Cédula de ciudadanía
- Correo electrónico
- Nombre del banco (ej: Bancolombia, Nequi, Davivienda)

⚠️ Operamos ÚNICAMENTE a través de PSE. Te enviaré un enlace de pago PSE para completar tu compra.""",

    "pse_only": """Nuestro banco SOLO utiliza PSE para recibir pagos. Por favor sigue las instrucciones anteriores. Todo el proceso es 100%% automatizado, liberamos al INSTANTE y estamos en línea 24/7.""",

    "link_sent": """[OK] Abre este enlace y realiza el pago con PSE. Una vez completado, marca como "Pagado" en Binance y liberaremos tu USDT al instante:

{payment_url}

Enlace válido por 21 minutos.""",

    "missing_fields": "[!] Solo me falta: {fields}. Por favor envíalo para generar tu enlace de pago.",
    "invalid_cc": "[!] La cédula ingresada no es válida: {error}. Por favor verifica el número.",
    "cc_security_alert": "[!] Esta cédula está asociada a otra cuenta. Por favor contacta a soporte.",
    "link_expired_new": """Tu enlace anterior expiró. Aquí tienes uno nuevo:

{payment_url}

Enlace válido por 21 minutos.""",
    "system_error": "[!] Hubo un error procesando tu solicitud. Por favor intenta de nuevo en unos minutos.",
    "payment_unavailable": "[!] El sistema de pagos no está disponible temporalmente.",
    "payment_received": "[OK] ¡Pago recibido! Liberando tus {usdt} USDT...",
    "completed": "¡Listo! Tus {usdt} USDT han sido liberados. ¡Gracias por tu compra!",

    # ── BUY flow messages (we buy USDT, pay COP to seller) ──
    "buy_welcome": """¡Hola! Enviamos al instante usando automatización. Por favor escribe a continuación:

- Nombre completo
- Cédula de ciudadanía (CC)
- Nombre del banco (ej: Bancolombia, Nequi, Davivienda)
- Número de cuenta""",

    "buy_missing_fields": "[!] Solo me falta: {fields}. Por favor envíalo para procesar tu pago.",
    "buy_payout_sent": "[OK] Pago de {cop} COP enviado a tu cuenta. El dinero llegará en minutos. Por favor libera los USDT.",
    "buy_payout_processing": "[...] Procesando tu pago de {cop} COP. Te confirmaremos cuando esté enviado.",
}
