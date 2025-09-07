from database.db import Session
from models.upi_settings import UPISettings


def get_active_upi_config():
    """
    Get the active UPI configuration from database.
    Returns default values if no active configuration is found.
    """
    db = Session()
    try:
        upi_settings = db.query(UPISettings).filter(UPISettings.is_active == True).first()
        if upi_settings:
            return {
                "upi_id": upi_settings.upi_id,
                "merchant_name": upi_settings.merchant_name
            }
        else:
            # Return default values if no active UPI settings
            return {
                "upi_id": "admin@upi",  # Default UPI ID
                "merchant_name": "Hostel Admin"  # Default merchant name
            }
    finally:
        db.close()


def get_upi_config():
    """Alias for get_active_upi_config for backward compatibility."""
    return get_active_upi_config()
