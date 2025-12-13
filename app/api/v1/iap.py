"""In-App Purchase verification endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.iap import (
    PurchaseVerifyRequest,
    PurchaseVerifyResponse,
    PurchaseRestoreRequest,
    PurchaseRestoreResponse,
    SubscriptionStatusResponse,
    IAPPlatform
)
from app.utils.time_utils import utc_now

router = APIRouter()

# Product durations
PRODUCT_DURATIONS = {
    "premium_monthly": timedelta(days=30),
    "premium_yearly": timedelta(days=365),
    "premium_lifetime": None,  # Never expires
}


async def verify_google_play_purchase(product_id: str, purchase_token: str) -> dict:
    """
    Verify a Google Play purchase using the Play Developer API.

    In production, you would:
    1. Use the Google Play Developer API to verify the purchase
    2. Check the purchase state and acknowledgement status
    3. Return purchase details

    For now, this is a placeholder that accepts all purchases.
    You'll need to implement the actual verification using google-api-python-client.
    """
    # TODO: Implement actual Google Play verification
    # from googleapiclient.discovery import build
    # service = build('androidpublisher', 'v3', credentials=credentials)
    # result = service.purchases().subscriptions().get(
    #     packageName='com.yourapp.package',
    #     subscriptionId=product_id,
    #     token=purchase_token
    # ).execute()

    # For development, accept all purchases
    return {
        "valid": True,
        "productId": product_id,
        "purchaseTime": utc_now().isoformat(),
    }


async def verify_app_store_purchase(receipt_data: str) -> dict:
    """
    Verify an App Store purchase using the App Store Server API.

    In production, you would:
    1. Send the receipt to Apple's verifyReceipt endpoint
    2. Validate the response
    3. Return purchase details

    For now, this is a placeholder.
    """
    # TODO: Implement actual App Store verification
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         'https://buy.itunes.apple.com/verifyReceipt',
    #         json={'receipt-data': receipt_data}
    #     )
    #     result = response.json()

    return {
        "valid": True,
        "productId": "premium_monthly",
        "purchaseTime": utc_now().isoformat(),
    }


@router.post("/verify", response_model=PurchaseVerifyResponse)
async def verify_purchase(
    purchase: PurchaseVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify a purchase from Google Play or App Store.
    Updates user subscription status if valid.
    """
    try:
        if purchase.platform == IAPPlatform.ANDROID:
            result = await verify_google_play_purchase(
                purchase.product_id,
                purchase.purchase_token
            )
        else:
            result = await verify_app_store_purchase(purchase.purchase_token)

        if not result.get("valid"):
            return PurchaseVerifyResponse(
                valid=False,
                message="Purchase verification failed"
            )

        # Update user subscription
        product_id = purchase.product_id
        duration = PRODUCT_DURATIONS.get(product_id)

        # Determine subscription tier from product ID
        tier = product_id  # e.g., "premium_monthly"

        # Calculate expiration
        expires_at = None
        if duration:
            expires_at = utc_now() + duration

        # Update user
        current_user.subscription_tier = tier
        current_user.subscription_expires_at = expires_at
        current_user.iap_product_id = product_id
        current_user.iap_purchase_token = purchase.purchase_token
        current_user.iap_order_id = purchase.order_id
        current_user.iap_platform = purchase.platform.value
        current_user.iap_purchased_at = utc_now()

        db.commit()

        return PurchaseVerifyResponse(
            valid=True,
            product_id=product_id,
            subscription_tier=tier,
            expires_at=expires_at,
            message="Subscription activated successfully"
        )

    except Exception as e:
        return PurchaseVerifyResponse(
            valid=False,
            message=f"Error verifying purchase: {str(e)}"
        )


@router.post("/restore", response_model=PurchaseRestoreResponse)
async def restore_purchases(
    restore_data: PurchaseRestoreRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restore purchases from the store.
    Verifies each purchase token and updates subscription status.
    """
    restored_count = 0
    active_subscription = None
    expires_at = None

    for token in restore_data.purchase_tokens:
        try:
            if restore_data.platform == IAPPlatform.ANDROID:
                result = await verify_google_play_purchase("", token)
            else:
                result = await verify_app_store_purchase(token)

            if result.get("valid"):
                restored_count += 1
                product_id = result.get("productId")

                if product_id:
                    duration = PRODUCT_DURATIONS.get(product_id)

                    # Keep the best subscription
                    if active_subscription is None or product_id == "premium_lifetime":
                        active_subscription = product_id

                        if duration:
                            expires_at = utc_now() + duration
                        else:
                            expires_at = None

        except Exception:
            continue

    # Update user if we found valid purchases
    if active_subscription:
        current_user.subscription_tier = active_subscription
        current_user.subscription_expires_at = expires_at
        current_user.iap_platform = restore_data.platform.value
        db.commit()

    return PurchaseRestoreResponse(
        restored_count=restored_count,
        active_subscription=active_subscription,
        expires_at=expires_at
    )


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user)
):
    """Get current subscription status"""
    days_remaining = None
    if current_user.subscription_expires_at:
        delta = current_user.subscription_expires_at - utc_now()
        days_remaining = max(0, delta.days)

    return SubscriptionStatusResponse(
        is_premium=current_user.is_premium,
        subscription_tier=current_user.subscription_tier,
        expires_at=current_user.subscription_expires_at,
        days_remaining=days_remaining
    )
