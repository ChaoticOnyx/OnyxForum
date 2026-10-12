from decimal import Decimal


OPERATION_NEW = "New"
OPERATION_PENDING_LINK = "PendingLink"
OPERATION_PROCESSING = "Processing"
OPERATION_PROCESSED = "Processed"
OPERATION_IGNORED = "Ignored"
OPERATION_ERROR = "Error"

OPERATION_STATUSES = (
    OPERATION_NEW,
    OPERATION_PENDING_LINK,
    OPERATION_PROCESSING,
    OPERATION_PROCESSED,
    OPERATION_IGNORED,
    OPERATION_ERROR,
)

OPERATION_DONATION = "Donation"
OPERATION_SUBSCRIPTION = "Subscription"
OPERATION_SUBSCRIPTION_RENEWAL = "SubscriptionRenewal"
OPERATION_SUBSCRIPTION_UPGRADE = "SubscriptionUpgrade"
OPERATION_GIFT_PURCHASE = "GiftPurchase"
OPERATION_SUBSCRIPTION_ENDED = "SubscriptionEnded"
OPERATION_PAYOUT = "Payout"
OPERATION_PAYOUT_ERROR = "PayoutError"
OPERATION_UNKNOWN = "Unknown"

POINTS_OPERATION_TYPES = (
    OPERATION_DONATION,
    OPERATION_SUBSCRIPTION,
    OPERATION_SUBSCRIPTION_RENEWAL,
    OPERATION_SUBSCRIPTION_UPGRADE,
)

EVENT_OPERATION_TYPES = {
    "donation_author": OPERATION_DONATION,
    "subscribe": OPERATION_SUBSCRIPTION,
    "recurrent": OPERATION_SUBSCRIPTION_RENEWAL,
    "up_subscription": OPERATION_SUBSCRIPTION_UPGRADE,
    "buy_gift": OPERATION_GIFT_PURCHASE,
    "unsubscribe": OPERATION_SUBSCRIPTION_ENDED,
    "payout": OPERATION_PAYOUT,
    "payout_error": OPERATION_PAYOUT_ERROR,
}

POINTS_EVENT_TYPES = frozenset((
    "donation_author",
    "subscribe",
    "recurrent",
    "up_subscription",
))
SUBSCRIPTION_EVENT_TYPES = frozenset((
    "subscribe",
    "recurrent",
    "up_subscription",
    "unsubscribe",
))

WEBHOOK_PENDING = "Pending"
WEBHOOK_DELIVERED = "Delivered"
WEBHOOK_FAILED = "Failed"

DISCORD_PENDING = "Pending"
DISCORD_PROCESSED = "Processed"
DISCORD_FAILED = "Failed"

ISSUE_INFO = "Info"
ISSUE_WARNING = "Warning"
ISSUE_CRITICAL = "Critical"

ZERO = Decimal("0")

WEBHOOK_EVENTS = (
    "boosty.operation.received",
    "boosty.donation.processed",
    "boosty.donation.pending_link",
    "boosty.operation.failed",
    "boosty.operation.ignored",
    "boosty.account.linked",
    "boosty.account.unlinked",
    "boosty.pending_donations.processed",
    "boosty.subscription.started",
    "boosty.subscription.changed",
    "boosty.subscription.ended",
    "boosty.discord.role.assigned",
    "boosty.discord.role.removed",
    "boosty.discord.role.error",
    "boosty.sync.failed",
    "boosty.integration.enabled",
    "boosty.integration.disabled",
    "boosty.reconciliation.failed",
)

LEGACY_MESSAGE_DEFAULTS = {
    "boosty_message_token": (
        "Здравствуйте, {boostyName}! Для привязки Boosty к форуму введите "
        "одноразовый код {token} на странице Donations / Boosty. Код действует до {expiresAt}."
    ),
    "boosty_message_link_success": "Аккаунт {boostyName} успешно связан с пользователем {user}.",
    "boosty_message_link_error": "Не удалось привязать аккаунт: код недействителен или уже использован.",
    "boosty_message_expired_token": "Срок действия кода привязки истёк.",
    "boosty_message_opyx_credited": "За поддержку на {amount} RUB начислено {opix} Opyx.",
    "boosty_message_link_required": "Для начисления Opyx требуется связать Boosty с форумом.",
}


MESSAGE_DEFAULTS = {
    "boosty_message_token": (
        "Здравствуйте, {boostyName}! Для привязки Boosty к форуму используйте одноразовый код: {token}\n"
        "Страница привязки: {linkUrl}\n"
        "Код действует до {expiresAt}."
    ),
    "boosty_message_link_success": "Boosty-аккаунт {boostyName} успешно привязан к форумному аккаунту {user}.",
    "boosty_message_link_error": (
        "Не удалось привязать Boosty-аккаунт: код недействителен или уже использован. "
        "Запросить новый код можно на странице {linkUrl}."
    ),
    "boosty_message_expired_token": (
        "Срок действия кода привязки истёк. Запросите новый код по адресу {linkUrl}, "
        "указав email вашего Boosty-аккаунта."
    ),
    "boosty_message_opyx_credited": "За поддержку на {amount} RUB начислено {opix} опиксов.",
    "boosty_message_processing_error": "Не удалось обработать операцию Boosty. Администратор уведомлён.",
    "boosty_message_link_required": "Для начисления опиксов привяжите Boosty к форуму: {linkUrl}",
}
