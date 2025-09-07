from sqlalchemy.orm import Session
from models.upi_settings import UPISettings
from schemas.upi_settings import UPISettingsCreate, UPISettingsUpdate
from typing import List, Optional


def get_upi_settings(db: Session) -> Optional[UPISettings]:
    """Get the active UPI settings."""
    return db.query(UPISettings).filter(UPISettings.is_active == True).first()


def get_all_upi_settings(db: Session) -> List[UPISettings]:
    """Get all UPI settings."""
    return db.query(UPISettings).all()


def create_upi_settings(upi_data: UPISettingsCreate, db: Session) -> UPISettings:
    """Create new UPI settings."""
    # Deactivate all existing settings first
    db.query(UPISettings).update({"is_active": False})

    # Create new settings
    upi_settings = UPISettings(
        upi_id=upi_data.upi_id,
        merchant_name=upi_data.merchant_name,
        is_active=upi_data.is_active
    )
    db.add(upi_settings)
    db.commit()
    db.refresh(upi_settings)
    return upi_settings


def update_upi_settings(upi_id: int, upi_data: UPISettingsUpdate, db: Session) -> Optional[UPISettings]:
    """Update UPI settings by ID."""
    upi_settings = db.query(UPISettings).filter(UPISettings.id == upi_id).first()
    if not upi_settings:
        return None

    update_data = upi_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(upi_settings, field, value)

    db.commit()
    db.refresh(upi_settings)
    return upi_settings


def delete_upi_settings(upi_id: int, db: Session) -> bool:
    """Delete UPI settings by ID."""
    upi_settings = db.query(UPISettings).filter(UPISettings.id == upi_id).first()
    if not upi_settings:
        return False

    db.delete(upi_settings)
    db.commit()
    return True


def activate_upi_settings(upi_id: int, db: Session) -> Optional[UPISettings]:
    """Activate specific UPI settings and deactivate others."""
    # Deactivate all settings
    db.query(UPISettings).update({"is_active": False})

    # Activate the specified one
    upi_settings = db.query(UPISettings).filter(UPISettings.id == upi_id).first()
    if upi_settings:
        upi_settings.is_active = True
        db.commit()
        db.refresh(upi_settings)

    return upi_settings
