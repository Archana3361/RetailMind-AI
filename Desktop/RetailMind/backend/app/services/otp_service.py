import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from app.core.config import settings
from app.core.security import generate_otp, hash_otp, get_otp_expiry

logger = logging.getLogger(__name__)


async def create_otp_record(db, email: str, purpose: str) -> str:
    """
    Generate OTP, store hashed version, return plain OTP.
    Purpose: 'registration' | 'password_reset'
    """
    plain_otp = generate_otp()
    hashed = hash_otp(plain_otp)
    now = datetime.now(timezone.utc)

    # Invalidate any existing OTPs for this email+purpose
    await db.otp_verifications.delete_many({"email": email, "purpose": purpose})

    record = {
        "email": email.lower(),
        "purpose": purpose,
        "otp_hash": hashed,
        "attempts": 0,
        "is_used": False,
        "created_at": now,
        "expires_at": get_otp_expiry(),
        "last_sent_at": now,
    }
    await db.otp_verifications.insert_one(record)
    return plain_otp


async def can_resend_otp(db, email: str, purpose: str) -> tuple[bool, int]:
    """Returns (can_resend, seconds_remaining)."""
    record = await db.otp_verifications.find_one(
        {"email": email.lower(), "purpose": purpose}
    )
    if not record:
        return True, 0

    last_sent = record.get("last_sent_at")
    if not last_sent:
        return True, 0

    if last_sent.tzinfo is None:
        last_sent = last_sent.replace(tzinfo=timezone.utc)

    elapsed = (datetime.now(timezone.utc) - last_sent).total_seconds()
    cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS

    if elapsed < cooldown:
        return False, int(cooldown - elapsed)
    return True, 0


async def verify_otp_record(db, email: str, otp: str, purpose: str) -> tuple[bool, str]:
    """
    Returns (success, message).
    Increments attempt count. Marks as used on success.
    """
    from app.core.security import verify_otp

    record = await db.otp_verifications.find_one(
        {"email": email.lower(), "purpose": purpose}
    )

    if not record:
        return False, "No OTP found. Please request a new one."

    if record.get("is_used"):
        return False, "OTP has already been used. Please request a new one."

    expires_at = record.get("expires_at")
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            return False, "OTP has expired. Please request a new one."

    attempts = record.get("attempts", 0)
    if attempts >= settings.OTP_MAX_ATTEMPTS:
        return False, "Maximum verification attempts exceeded. Please request a new OTP."

    # Increment attempts
    await db.otp_verifications.update_one(
        {"_id": record["_id"]},
        {"$inc": {"attempts": 1}}
    )

    if not verify_otp(otp, record["otp_hash"]):
        remaining = settings.OTP_MAX_ATTEMPTS - attempts - 1
        return False, f"Invalid OTP. {remaining} attempt(s) remaining."

    # Mark as used
    await db.otp_verifications.update_one(
        {"_id": record["_id"]},
        {"$set": {"is_used": True}}
    )
    return True, "OTP verified successfully."


async def send_otp_email(email: str, otp: str, purpose: str, full_name: str = ""):
    """Send OTP via SMTP. Falls back to console log in dev mode."""
    subject_map = {
        "registration": "Verify your RetailMind AI account",
        "password_reset": "Reset your RetailMind AI password",
    }
    subject = subject_map.get(purpose, "Your RetailMind AI OTP")

    if purpose == "registration":
        body_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;border:1px solid #e5e7eb;border-radius:8px;">
          <h2 style="color:#1e293b;margin-bottom:4px;">Verify your account</h2>
          <p style="color:#64748b;margin-bottom:24px;">Hi {full_name or 'there'}, welcome to RetailMind AI. Use the code below to verify your account.</p>
          <div style="background:#f1f5f9;border-radius:6px;padding:24px;text-align:center;margin-bottom:24px;">
            <span style="font-size:36px;font-weight:700;letter-spacing:10px;color:#0f172a;">{otp}</span>
          </div>
          <p style="color:#94a3b8;font-size:13px;">This code expires in {settings.OTP_EXPIRE_MINUTES} minutes. Do not share it with anyone.</p>
        </div>
        """
    else:
        body_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;border:1px solid #e5e7eb;border-radius:8px;">
          <h2 style="color:#1e293b;margin-bottom:4px;">Reset your password</h2>
          <p style="color:#64748b;margin-bottom:24px;">Use the code below to reset your RetailMind AI password.</p>
          <div style="background:#f1f5f9;border-radius:6px;padding:24px;text-align:center;margin-bottom:24px;">
            <span style="font-size:36px;font-weight:700;letter-spacing:10px;color:#0f172a;">{otp}</span>
          </div>
          <p style="color:#94a3b8;font-size:13px;">This code expires in {settings.OTP_EXPIRE_MINUTES} minutes. If you did not request this, ignore this email.</p>
        </div>
        """

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        # Dev mode: print to console
        logger.warning(
            f"[DEV MODE] OTP for {email} ({purpose}): {otp}"
        )
        print(f"\n{'='*50}\n[OTP EMAIL - DEV MODE]\nTo: {email}\nSubject: {subject}\nOTP: {otp}\n{'='*50}\n")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>"
        msg["To"] = email
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, email, msg.as_string())
        logger.info(f"OTP email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        # Fall back to console log so development is not blocked
        print(f"\n[OTP FALLBACK] To: {email} | OTP: {otp}\n")
