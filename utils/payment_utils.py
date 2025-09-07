import io
import qrcode
from fastapi.responses import StreamingResponse

def generate_upi_qr(upi_id: str, name: str, amount: float, txn_id: str):
    """
    Generate UPI QR code and deep link for payment.

    Args:
        upi_id (str): UPI ID of the payee (e.g., "merchant@upi")
        name (str): Name of the payee
        amount (float): Payment amount
        txn_id (str): Transaction ID for the payment

    Returns:
        tuple: (upi_url, qr_bytes) where upi_url is the UPI deep link and
               qr_bytes is the QR code image bytes
    """
    # Create UPI payment URL
    upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&tn={txn_id}&cu=INR"

    # Generate QR code
    qr = qrcode.make(upi_url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    qr_bytes = buf.getvalue()

    return upi_url, qr_bytes
