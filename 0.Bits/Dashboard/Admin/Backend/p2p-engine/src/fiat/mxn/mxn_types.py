"""
MXN Types & Constants
=====================
Enums, dataclasses, and message templates for the MXN module.
Mirrors cop_types.py structure for consistency.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MXNOrderState(Enum):
    """
    MXN order state machine.

    SELL flow (we sell USDT, buyer pays MXN via SPEI):
        AWAITING_CURP → CURP_RECEIVED → GENERATING_CLABE
        → CLABE_SENT → AWAITING_PAYMENT → PAYMENT_RECEIVED
        → RELEASING → COMPLETED

    BUY flow (we buy USDT, pay MXN to seller via SPEI):
        COLLECTING_BANK_INFO → PAYOUT_PENDING → PAYOUT_SENT
        → MARK_PAID_PENDING → COMPLETED

    Terminal states: COMPLETED, CANCELLED (no outgoing transitions).
    """
    NEW = "new"
    # SELL states
    AWAITING_CURP = "awaiting_curp"
    CURP_RECEIVED = "curp_received"
    GENERATING_CLABE = "generating_clabe"
    CLABE_SENT = "clabe_sent"
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
class MXNOrder:
    """A single MXN P2P order being tracked."""
    binance_order_id: str
    binance_external_id: Optional[str] = None
    order_side: str = "SELL"  # "BUY" or "SELL"
    customer_name: Optional[str] = None
    customer_curp: Optional[str] = None
    customer_rfc: Optional[str] = None
    customer_clabe: Optional[str] = None  # BUY flow: seller's CLABE
    amount_mxn: Optional[str] = None
    amount_usdt: Optional[str] = None
    facilitapay_subject_id: Optional[str] = None
    facilitapay_tx_id: Optional[str] = None
    dynamic_clabe: Optional[str] = None  # SELL flow: generated CLABE for buyer
    state: MXNOrderState = MXNOrderState.NEW
    binance_buyer_name: Optional[str] = None
    created_at: Optional[datetime] = None
    welcome_sent: bool = False
    chat_messages: list[str] = field(default_factory=list)
    # BUY order fields
    seller_bank_account_id: Optional[str] = None  # FP registered bank account UUID
    facilitapay_payout_tx_id: Optional[str] = None
    payout_sent_at: Optional[datetime] = None
    mark_paid_at: Optional[datetime] = None
    mark_paid_retries: int = 0

    @property
    def is_buy(self) -> bool:
        return self.order_side == "BUY"


@dataclass
class MXNCustomerInfo:
    """Extracted customer information from chat messages."""
    name: Optional[str] = None
    curp: Optional[str] = None      # 18-char CURP
    rfc: Optional[str] = None       # 13-char RFC (optional)
    clabe: Optional[str] = None     # 18-digit CLABE (BUY flow)
    email: Optional[str] = None     # Email for FP registration

    def is_complete_for_sell(self) -> bool:
        """SELL: Need CURP + email (name comes from Binance)."""
        return bool(self.curp and self.email)

    def is_complete_for_buy(self) -> bool:
        """BUY: Need CURP + email + CLABE (name comes from Binance)."""
        return bool(self.curp and self.email and self.clabe)

    def missing_sell_fields(self) -> list[str]:
        fields = []
        if not self.curp: fields.append("CURP (18 caracteres)")
        if not self.email: fields.append("correo electrónico")
        return fields

    def missing_buy_fields(self) -> list[str]:
        fields = []
        if not self.curp: fields.append("CURP (18 caracteres)")
        if not self.email: fields.append("correo electrónico")
        if not self.clabe: fields.append("CLABE (18 dígitos)")
        return fields


# ============================================================================
# Chat message templates (Spanish — Mexico)
# ============================================================================

MESSAGES: dict[str, str] = {
    # ── SELL flow messages (we sell USDT, buyer pays MXN via SPEI) ──
    "welcome": """¡Hola! Para procesar tu compra de {usdt} USDT necesito los siguientes datos:

- CURP (18 caracteres)
- Correo electrónico

Te generaré una CLABE única para que realices tu pago por SPEI desde cualquier banco mexicano.

⚡ Operamos ÚNICAMENTE por SPEI. Todo el proceso es 100%% automatizado, liberamos al INSTANTE y estamos en línea 24/7.""",

    "clabe_sent": """[OK] Realiza una transferencia SPEI a esta CLABE:

{clabe}

Monto exacto: {amount} MXN
Concepto: {reference}

⚡ Una vez recibido tu pago, liberamos tus USDT al instante.
📌 Esta CLABE es única para esta transacción.""",

    "missing_fields": "[!] Solo me falta: {fields}. Por favor envíalos para generar tu referencia de pago.",

    "invalid_curp": "[!] El CURP ingresado no es válido. Debe tener 18 caracteres alfanuméricos (ejemplo: SOMH031031HSRTRR04). Por favor verifica.",

    "curp_security_alert": "[!] Este CURP está asociado a otra cuenta. Por favor contacta a soporte.",

    "payment_received": "[OK] ¡Pago recibido! Liberando tus {usdt} USDT...",

    "completed": "¡Listo! Tus {usdt} USDT han sido liberados. ¡Gracias por tu compra!",

    "system_error": "[!] Hubo un error procesando tu solicitud. Por favor intenta de nuevo en unos minutos.",

    # ── BUY flow messages (we buy USDT, pay MXN to seller via SPEI) ──
    "buy_welcome": """¡Hola! Enviamos al instante por SPEI usando automatización. Por favor escribe a continuación:

- CURP (18 caracteres)
- Correo electrónico
- CLABE interbancaria (18 dígitos)""",

    "buy_missing_fields": "[!] Solo me falta: {fields}. Por favor envíalo para procesar tu pago SPEI.",

    "buy_payout_sent": "[OK] Pago de {mxn} MXN enviado por SPEI a tu cuenta. El dinero llegará en segundos. Por favor libera los USDT.",

    "buy_payout_processing": "[...] Procesando tu pago de {mxn} MXN por SPEI. Te confirmaremos cuando esté enviado.",
}
