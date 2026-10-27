from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.schemas.auth import (
    RegisterRequest, VerifyOTPRequest, ResendOTPRequest,
    LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
)
from app.services import auth_service
from app.dependencies.auth import get_current_user
from app.models.user import user_helper

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", summary="Register a new user account")
async def register(data: RegisterRequest, db=Depends(get_database)):
    return await auth_service.register_user(
        db, data.full_name, data.email, data.mobile, data.shop_name, data.password
    )


@router.post("/verify-otp", summary="Verify registration OTP")
async def verify_otp(data: VerifyOTPRequest, db=Depends(get_database)):
    return await auth_service.verify_registration_otp(db, data.email, data.otp)


@router.post("/resend-otp", summary="Resend OTP (registration or password reset)")
async def resend_otp(data: ResendOTPRequest, db=Depends(get_database)):
    return await auth_service.resend_otp(db, data.email, data.purpose)


@router.post("/login", summary="Login and receive JWT token")
async def login(data: LoginRequest, db=Depends(get_database)):
    return await auth_service.login_user(db, data.email, data.password)


@router.post("/forgot-password", summary="Initiate password reset")
async def forgot_password(data: ForgotPasswordRequest, db=Depends(get_database)):
    return await auth_service.initiate_password_reset(db, data.email)


@router.post("/verify-reset-otp", summary="Verify password reset OTP")
async def verify_reset_otp(data: VerifyOTPRequest, db=Depends(get_database)):
    return await auth_service.verify_reset_otp(db, data.email, data.otp)


@router.post("/reset-password", summary="Set new password after OTP verification")
async def reset_password(data: ResetPasswordRequest, db=Depends(get_database)):
    from app.core.security import decode_access_token
    # Verify the reset token issued by verify-reset-otp
    payload = decode_access_token(data.reset_token)
    if not payload or payload.get("purpose") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token. Please restart the password reset process."
        )
    if payload.get("sub") != data.email.lower().strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token does not match the provided email."
        )
    return await auth_service.reset_password(db, data.email, data.new_password)


@router.get("/me", summary="Get current authenticated user")
async def get_me(current_user=Depends(get_current_user)):
    return user_helper(current_user)
