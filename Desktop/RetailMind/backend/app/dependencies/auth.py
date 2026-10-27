from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from app.core.security import decode_access_token
from app.core.database import get_database

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_database),
):
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    if not user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Account not verified.")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated.")

    return user


async def get_current_user_id(current_user=Depends(get_current_user)) -> str:
    return str(current_user["_id"])
