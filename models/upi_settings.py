from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database.db import Base
from datetime import datetime


class UPISettings(Base):
    __tablename__ = "upi_settings"

    id = Column(Integer, primary_key=True, index=True)
    upi_id = Column(String(100), unique=True, nullable=False)  # e.g., "admin@upi"
    merchant_name = Column(String(100), nullable=False)  # e.g., "Hostel Admin"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
