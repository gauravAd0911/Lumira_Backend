"""Cart API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Cart, CartItem, Product
from app.schemas.schemas import (
    AddCartItemRequest,
    ApiEnvelope,
    CartResponse,
    MessageResponse,
    UpdateCartItemRequest,
)

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])


DEFAULT_USER_ID = "guest_user"
USER_ID_HEADER = "X-User-Id"

ERROR_PRODUCT_NOT_FOUND = "Product not found."
ERROR_NOT_ENOUGH_STOCK = "Not enough stock."
ERROR_ITEM_NOT_FOUND = "Item not found in cart."

MESSAGE_CART_ALREADY_EMPTY = "Cart already empty."
MESSAGE_CART_CLEARED = "Cart cleared successfully."

DbSession = Annotated[Session, Depends(get_db)]


def get_active_user_id(
    x_user_id: Annotated[str, Header(alias=USER_ID_HEADER)] = DEFAULT_USER_ID,
) -> str:
    """Return active user id from header with a safe fallback."""
    value = x_user_id.strip()
    return value or DEFAULT_USER_ID


UserId = Annotated[str, Depends(get_active_user_id)]


def _success(message: str, data):
    return ApiEnvelope(success=True, message=message, data=data, error=None)


def _cart_payload(cart: CartResponse) -> dict:
    return {
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "product": {
                    "id": str(item.product.id),
                    "name": item.product.name,
                    "price": item.product.price,
                    "image_url": item.product.image_url,
                },
            }
            for item in cart.items
        ],
        "summary": {
            "subtotal": cart.total_price,
            "discount": 0,
            "shipping": 0,
            "tax": 0,
            "total": cart.total_price,
            "currency": "INR",
        },
    }


def _get_or_create_active_cart(db: Session, user_id: str) -> Cart:
    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.is_active.is_(True),
        )
        .first()
    )
    if cart is not None:
        return cart

    cart = Cart(user_id=user_id, is_active=True)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def _get_active_product(db: Session, product_id: int) -> Product:
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.is_active.is_(True),
        )
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_PRODUCT_NOT_FOUND)
    return product


def _get_cart_item(db: Session, cart_id: int, product_id: int) -> CartItem | None:
    return (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
        .first()
    )


@router.get("", response_model=ApiEnvelope, summary="Fetch the active cart")
def get_cart(db: DbSession, user_id: UserId) -> CartResponse:
    cart = _get_or_create_active_cart(db, user_id)
    response = CartResponse.from_orm_with_totals(cart)
    return _success("Cart fetched successfully.", _cart_payload(response))


@router.post("/items", response_model=ApiEnvelope, status_code=status.HTTP_201_CREATED, summary="Add a product to the cart")
def add_item(payload: AddCartItemRequest, db: DbSession, user_id: UserId) -> CartResponse:
    product = _get_active_product(db, payload.product_id)

    cart = _get_or_create_active_cart(db, user_id)
    item = _get_cart_item(db, cart.id, payload.product_id)
    next_quantity = payload.quantity if item is None else item.quantity + payload.quantity

    if product.stock < next_quantity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ERROR_NOT_ENOUGH_STOCK)

    if item is None:
        db.add(
            CartItem(
                cart_id=cart.id,
                product_id=payload.product_id,
                quantity=payload.quantity,
            )
        )
    else:
        item.quantity = next_quantity

    db.commit()
    db.refresh(cart)
    response = CartResponse.from_orm_with_totals(cart)
    return _success("Item added to cart successfully.", _cart_payload(response))


@router.patch("/items/{product_id}", response_model=ApiEnvelope, summary="Set the exact quantity for a cart item")
def update_item(product_id: int, payload: UpdateCartItemRequest, db: DbSession, user_id: UserId) -> CartResponse:
    product = _get_active_product(db, product_id)
    if product.stock < payload.quantity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ERROR_NOT_ENOUGH_STOCK)

    cart = _get_or_create_active_cart(db, user_id)
    item = _get_cart_item(db, cart.id, product_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_ITEM_NOT_FOUND)

    item.quantity = payload.quantity
    db.commit()
    db.refresh(cart)
    response = CartResponse.from_orm_with_totals(cart)
    return _success("Cart updated successfully.", _cart_payload(response))


@router.delete("/items/{product_id}", response_model=ApiEnvelope, summary="Remove a specific item")
def remove_item(product_id: int, db: DbSession, user_id: UserId) -> CartResponse:
    cart = _get_or_create_active_cart(db, user_id)
    item = _get_cart_item(db, cart.id, product_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_ITEM_NOT_FOUND)

    db.delete(item)
    db.commit()
    db.refresh(cart)
    response = CartResponse.from_orm_with_totals(cart)
    return _success("Item removed from cart successfully.", _cart_payload(response))


@router.delete("", response_model=ApiEnvelope, summary="Clear all items from the active cart")
def clear_cart(db: DbSession, user_id: UserId) -> MessageResponse:
    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.is_active.is_(True),
        )
        .first()
    )
    if cart is None:
        return _success(MESSAGE_CART_ALREADY_EMPTY, {"items": [], "summary": {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0, "currency": "INR"}})

    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    db.commit()
    return _success(MESSAGE_CART_CLEARED, {"items": [], "summary": {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0, "currency": "INR"}})

