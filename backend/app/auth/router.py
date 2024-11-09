from fastapi import APIRouter, Depends, HTTPException
from .utils import JWTBearer

router = APIRouter()

@router.get("/protected")
async def protected_route(payload=Depends(JWTBearer())):
    """Example protected route that requires authentication"""
    return {"message": "This is a protected route", "user": payload.get("sub")}

@router.get("/user-profile")
async def get_user_profile(payload=Depends(JWTBearer())):
    """Get the user profile information from the token"""
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name")
    }
