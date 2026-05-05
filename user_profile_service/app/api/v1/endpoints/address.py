from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies.auth import get_db, get_current_user
from app.services import address_service
from app.schemas.address import AddressCreate
from app.schemas.common import APIResponse, ErrorDetail

router = APIRouter()


@router.get("/")
def get_addresses(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    addresses = address_service.get_addresses(db, user_id)
    return APIResponse(success=True, message="Addresses retrieved successfully", data=addresses)


@router.post("/")
def create_address(
    payload: AddressCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    address = address_service.create_address(db, user_id, payload.dict())
    return APIResponse(success=True, message="Address created successfully", data=address)


@router.patch("/{address_id}")
def update_address(
    address_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    try:
        address = address_service.update_address(db, user_id, address_id, payload)
        return APIResponse(success=True, message="Address updated successfully", data=address)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Address not found",
                "error": {
                    "code": "ADDRESS_NOT_FOUND",
                    "message": str(exc)
                }
            }
        ) from exc


@router.delete("/{address_id}")
def delete_address(
    address_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    try:
        result = address_service.delete_address(db, user_id, address_id)
        return APIResponse(success=True, message="Address deleted successfully", data=result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Address not found",
                "error": {
                    "code": "ADDRESS_NOT_FOUND",
                    "message": str(exc)
                }
            }
        ) from exc


@router.patch("/{address_id}/default")
def set_default(
    address_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    try:
        address = address_service.set_default_address(db, user_id, address_id)
        return APIResponse(success=True, message="Default address set successfully", data=address)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Address not found",
                "error": {
                    "code": "ADDRESS_NOT_FOUND",
                    "message": str(exc)
                }
            }
        ) from exc
