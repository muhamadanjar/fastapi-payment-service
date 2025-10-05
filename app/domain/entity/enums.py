from enum import Enum


class MethodType(str, Enum):
    VIRTUAL_ACCOUNT = "virtual_account"
    E_WALLET = "e_wallet"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    QRIS = "qris"
    RETAIL = "retail"

class GatewayType(str, Enum):
    MIDTRANS = "midtrans"
    XENDIT = "xendit"
    DOKU = "doku"
    NICEPAY = "nicepay"
    FASPAY = "faspay"

class AdminFeeType(str, Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"

class VoucherType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    REFERRAL = "referral"
    CASHBACK = "cashback"

class DiscountType(str, Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    SETTLEMENT = "settlement"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"

class ConditionType(str, Enum):
    MIN_AMOUNT = "min_amount"
    MAX_AMOUNT = "max_amount"
    PRODUCT_ID = "product_id"
    CATEGORY_ID = "category_id"
    USER_SEGMENT = "user_segment"
    PAYMENT_METHOD = "payment_method"

class OperatorType(str, Enum):
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN = "in"
    NOT_IN = "not_in"

class ChangedBy(str, Enum):
    SYSTEM = "system"
    USER = "user"
    GATEWAY = "gateway"
    ADMIN = "admin"

class RequestType(str, Enum):
    CREATE_PAYMENT = "create_payment"
    CHECK_STATUS = "check_status"
    CANCEL_PAYMENT = "cancel_payment"
    REFUND = "refund"

class CallbackType(str, Enum):
    PAYMENT_NOTIFICATION = "payment_notification"
    TRANSACTION_STATUS = "transaction_status"
    REFUND_NOTIFICATION = "refund_notification"
