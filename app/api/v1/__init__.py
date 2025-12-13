"""API v1 routes"""
from fastapi import APIRouter
from app.api.v1 import (
    auth,
    auth_firebase,
    categories,
    wallets,
    transactions,
    budgets,
    objectives,
    recurring,
    payment_methods,
    associated_titles,
    sync,
    iap
)

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(auth_firebase.router, prefix="/auth", tags=["authentication"])

# Core resources
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(wallets.router, prefix="/wallets", tags=["wallets"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(payment_methods.router, prefix="/payment-methods", tags=["payment-methods"])

# Features
api_router.include_router(objectives.router, prefix="/objectives", tags=["objectives", "goals"])
api_router.include_router(recurring.router, prefix="/recurring", tags=["recurring"])
api_router.include_router(associated_titles.router, prefix="/associated-titles", tags=["smart-categorization"])

# Sync & IAP
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(iap.router, prefix="/iap", tags=["in-app-purchase"])
