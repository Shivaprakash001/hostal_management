from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from schemas.upi_settings import UPISettingsCreate, UPISettingsUpdate, UPISettingsOut
from services.upi_services import (
    get_upi_settings, get_all_upi_settings, create_upi_settings,
    update_upi_settings, delete_upi_settings, activate_upi_settings
)
from models.models import User, UserRole
from utils.auth import get_current_user
from database.db import Session as DBSession

router = APIRouter(prefix="/upi", tags=["upi"])


def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


@router.get("/active", response_model=UPISettingsOut)
def get_active_upi_settings(db: Session = Depends(get_db)):
    """Get the currently active UPI settings."""
    upi_settings = get_upi_settings(db)
    if not upi_settings:
        raise HTTPException(status_code=404, detail="No active UPI settings found")
    return upi_settings


@router.get("/", response_model=List[UPISettingsOut])
def get_all_upi_settings_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all UPI settings (Admin only)."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return get_all_upi_settings(db)


@router.post("/", response_model=UPISettingsOut, status_code=status.HTTP_201_CREATED)
def create_upi_settings_route(
    upi_data: UPISettingsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new UPI settings (Admin only)."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        return create_upi_settings(upi_data, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating UPI settings: {str(e)}")


@router.put("/{upi_id}", response_model=UPISettingsOut)
def update_upi_settings_route(
    upi_id: int,
    upi_data: UPISettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update UPI settings (Admin only)."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    upi_settings = update_upi_settings(upi_id, upi_data, db)
    if not upi_settings:
        raise HTTPException(status_code=404, detail="UPI settings not found")

    return upi_settings


@router.delete("/{upi_id}")
def delete_upi_settings_route(
    upi_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete UPI settings (Admin only)."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    if not delete_upi_settings(upi_id, db):
        raise HTTPException(status_code=404, detail="UPI settings not found")

    return {"message": "UPI settings deleted successfully"}


@router.post("/{upi_id}/activate", response_model=UPISettingsOut)
def activate_upi_settings_route(
    upi_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate specific UPI settings (Admin only)."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    upi_settings = activate_upi_settings(upi_id, db)
    if not upi_settings:
        raise HTTPException(status_code=404, detail="UPI settings not found")

    return upi_settings
