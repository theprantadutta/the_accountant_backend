"""Pydantic schemas"""
from app.schemas.auth import Token, TokenData
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    FirebaseAuthRequest,
    GoogleAuthRequest,
    LinkAccountRequest,
    AuthProvidersResponse
)
from app.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithSubcategories,
    CategoryListResponse
)
from app.schemas.wallet import (
    WalletBase,
    WalletCreate,
    WalletUpdate,
    WalletResponse,
    WalletListResponse
)
from app.schemas.payment_method import (
    PaymentMethodBase,
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodResponse,
    PaymentMethodListResponse
)
from app.schemas.transaction import (
    TransactionType,
    TransactionBase,
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    TransactionBulkCreate,
    TransactionFilter
)
from app.schemas.recurring import (
    RecurrenceType,
    RecurringConfigBase,
    RecurringConfigCreate,
    RecurringConfigUpdate,
    RecurringConfigResponse,
    RecurringConfigListResponse,
    RecurringTriggerResponse
)
from app.schemas.budget import (
    BudgetPeriod,
    BudgetBase,
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetWithProgress,
    BudgetListResponse
)
from app.schemas.objective import (
    ObjectiveType,
    ObjectiveBase,
    ObjectiveCreate,
    ObjectiveUpdate,
    ObjectiveResponse,
    ObjectiveWithProgress,
    ObjectiveListResponse,
    ObjectiveTransactionLink,
    ObjectiveTransactionResponse
)
from app.schemas.associated_title import (
    AssociatedTitleBase,
    AssociatedTitleCreate,
    AssociatedTitleUpdate,
    AssociatedTitleResponse,
    AssociatedTitleListResponse,
    CategorySuggestion
)
from app.schemas.sync import (
    SyncStatus,
    SyncChange,
    SyncPushRequest,
    SyncPushResponse,
    SyncPullRequest,
    SyncPullResponse,
    SyncStatusResponse,
    SyncConflict,
    SyncLogResponse
)
from app.schemas.iap import (
    IAPPlatform,
    IAPProductType,
    PurchaseVerifyRequest,
    PurchaseVerifyResponse,
    PurchaseRestoreRequest,
    PurchaseRestoreResponse,
    SubscriptionStatusResponse
)

__all__ = [
    # Auth
    "Token",
    "TokenData",
    # User
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "FirebaseAuthRequest",
    "GoogleAuthRequest",
    "LinkAccountRequest",
    "AuthProvidersResponse",
    # Category
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryWithSubcategories",
    "CategoryListResponse",
    # Wallet
    "WalletBase",
    "WalletCreate",
    "WalletUpdate",
    "WalletResponse",
    "WalletListResponse",
    # PaymentMethod
    "PaymentMethodBase",
    "PaymentMethodCreate",
    "PaymentMethodUpdate",
    "PaymentMethodResponse",
    "PaymentMethodListResponse",
    # Transaction
    "TransactionType",
    "TransactionBase",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionResponse",
    "TransactionListResponse",
    "TransactionBulkCreate",
    "TransactionFilter",
    # Recurring
    "RecurrenceType",
    "RecurringConfigBase",
    "RecurringConfigCreate",
    "RecurringConfigUpdate",
    "RecurringConfigResponse",
    "RecurringConfigListResponse",
    "RecurringTriggerResponse",
    # Budget
    "BudgetPeriod",
    "BudgetBase",
    "BudgetCreate",
    "BudgetUpdate",
    "BudgetResponse",
    "BudgetWithProgress",
    "BudgetListResponse",
    # Objective
    "ObjectiveType",
    "ObjectiveBase",
    "ObjectiveCreate",
    "ObjectiveUpdate",
    "ObjectiveResponse",
    "ObjectiveWithProgress",
    "ObjectiveListResponse",
    "ObjectiveTransactionLink",
    "ObjectiveTransactionResponse",
    # AssociatedTitle
    "AssociatedTitleBase",
    "AssociatedTitleCreate",
    "AssociatedTitleUpdate",
    "AssociatedTitleResponse",
    "AssociatedTitleListResponse",
    "CategorySuggestion",
    # Sync
    "SyncStatus",
    "SyncChange",
    "SyncPushRequest",
    "SyncPushResponse",
    "SyncPullRequest",
    "SyncPullResponse",
    "SyncStatusResponse",
    "SyncConflict",
    "SyncLogResponse",
    # IAP
    "IAPPlatform",
    "IAPProductType",
    "PurchaseVerifyRequest",
    "PurchaseVerifyResponse",
    "PurchaseRestoreRequest",
    "PurchaseRestoreResponse",
    "SubscriptionStatusResponse",
]
