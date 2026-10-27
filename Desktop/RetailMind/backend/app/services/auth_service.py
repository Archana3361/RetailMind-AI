from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import user_helper, new_user_document
from app.services.otp_service import create_otp_record, send_otp_email, verify_otp_record, can_resend_otp


async def register_user(db, full_name: str, email: str, mobile: str,
                        shop_name: str, password: str):
    email = email.lower().strip()

    existing = await db.users.find_one({"email": email})
    if existing:
        if existing.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists."
            )
        else:
            # Unverified: allow re-registration by deleting old record
            await db.users.delete_one({"email": email})

    hashed_pw = hash_password(password)
    user_doc = new_user_document(full_name, email, mobile, shop_name, hashed_pw)
    result = await db.users.insert_one(user_doc)

    otp = await create_otp_record(db, email, "registration")
    await send_otp_email(email, otp, "registration", full_name)

    return {"message": "Registration successful. Check your email for the OTP.", "email": email}


async def verify_registration_otp(db, email: str, otp: str):
    email = email.lower().strip()
    success, message = await verify_otp_record(db, email, otp, "registration")
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    await db.users.update_one(
        {"email": email},
        {"$set": {"is_verified": True, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Account verified successfully. You can now log in."}


async def resend_otp(db, email: str, purpose: str):
    email = email.lower().strip()

    if purpose == "registration":
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="Email not found.")
        if user.get("is_verified"):
            raise HTTPException(status_code=400, detail="Account is already verified.")

    can_resend, seconds = await can_resend_otp(db, email, purpose)
    if not can_resend:
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {seconds} seconds before requesting a new OTP."
        )

    user = await db.users.find_one({"email": email})
    full_name = user["full_name"] if user else ""
    otp = await create_otp_record(db, email, purpose)
    await send_otp_email(email, otp, purpose, full_name)
    return {"message": "OTP sent successfully."}


async def login_user(db, email: str, password: str):
    email = email.lower().strip()
    user = await db.users.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.get("is_verified"):
        raise HTTPException(
            status_code=403,
            detail="Account not verified. Please verify your email first."
        )

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    token = create_access_token({"sub": str(user["_id"]), "email": email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_helper(user)
    }


async def initiate_password_reset(db, email: str):
    email = email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        # Security: don't reveal if email exists
        return {"message": "If this email is registered, you will receive an OTP."}

    otp = await create_otp_record(db, email, "password_reset")
    await send_otp_email(email, otp, "password_reset", user.get("full_name", ""))
    return {"message": "If this email is registered, you will receive an OTP."}


async def verify_reset_otp(db, email: str, otp: str):
    email = email.lower().strip()
    success, message = await verify_otp_record(db, email, otp, "password_reset")
    if not success:
        raise HTTPException(status_code=400, detail=message)
    # Re-create a verified marker so reset can proceed
    # We reuse the same record marked as used — frontend will send email+otp+newpass together
    # So we issue a short-lived reset token instead
    reset_token = create_access_token({"sub": email, "purpose": "password_reset"}, )
    return {"message": "OTP verified.", "reset_token": reset_token}


async def reset_password(db, email: str, new_password: str):
    email = email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    hashed_pw = hash_password(new_password)
    await db.users.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed_pw, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Password reset successfully. You can now log in."}
