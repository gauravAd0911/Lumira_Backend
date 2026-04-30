from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Product
from app.schemas.schemas import ProductOut

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


def _out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id, name=p.name, slug=p.slug, description=p.description,
        price=p.price, compare_price=p.compare_price, sku=p.sku,
        stock_qty=p.stock_qty, images=p.images or [],
        category=p.category.name if p.category else None,
    )


@router.get("", response_model=List[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Product).filter_by(is_active=True)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    return [_out(p) for p in q.offset(offset).limit(limit).all()]


@router.get("/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter_by(slug=slug, is_active=True).first()
    if not p:
        raise HTTPException(404, "Product not found.")
    return _out(p)