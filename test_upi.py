#!/usr/bin/env python3
"""
Test script for UPI settings functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import Session, init_db
from models.upi_settings import UPISettings
from services.upi_services import create_upi_settings
from schemas.upi_settings import UPISettingsCreate
from utils.upi_config import get_upi_config

def test_upi_functionality():
    """Test UPI settings functionality"""
    print("Testing UPI Settings Functionality")
    print("=" * 40)

    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("   ✓ Database initialized")

    # Test creating UPI settings
    print("\n2. Creating UPI settings...")
    db = Session()
    try:
        upi_data = UPISettingsCreate(
            upi_id="admin@upi",
            merchant_name="Hostel Admin"
        )
        upi_settings = create_upi_settings(upi_data, db)
        print(f"   ✓ UPI settings created: {upi_settings.upi_id} - {upi_settings.merchant_name}")

        # Test getting UPI config
        print("\n3. Testing UPI config retrieval...")
        config = get_upi_config()
        print(f"   ✓ UPI Config: {config}")

        # Test payment QR generation
        print("\n4. Testing QR code generation...")
        from utils.payment_utils import generate_upi_qr
        upi_url, qr_bytes = generate_upi_qr(config["upi_id"], config["merchant_name"], 1000.00, "test_order_123")
        print(f"   ✓ UPI URL generated: {upi_url}")
        print(f"   ✓ QR Code size: {len(qr_bytes)} bytes")

        print("\n✅ All UPI functionality tests passed!")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        db.close()

    return True

if __name__ == "__main__":
    success = test_upi_functionality()
    sys.exit(0 if success else 1)
