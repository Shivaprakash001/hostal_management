from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UPISettingsBase(BaseModel):
    upi_id: str
    merchant_name: str
    is_active: Optional[bool] = True


class UPISettingsCreate(UPISettingsBase):
    pass


class UPISettingsUpdate(BaseModel):
    upi_id: Optional[str] = None
    merchant_name: Optional[str] = None
    is_active: Optional[bool] = None


class UPISettingsOut(UPISettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
