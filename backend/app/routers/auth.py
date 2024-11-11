from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import os
from ..utils.auth import get_current_user_jwt_from_token, get_current_user_jwt, get_current_user
from ..utils.db import get_db
from ..utils.crypto import encrypt_token
from ..models import User

router = APIRouter()

async def exchange_code_for_token(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://github.com/login/oauth/access_token',
            json={
                'client_id': os.getenv('GITHUB_CLIENT_ID'),
                'client_secret': os.getenv('GITHUB_CLIENT_SECRET'),
                'code': code
            },
            headers={'Accept': 'application/json'}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error getting GitHub token")

        return response.json()

@router.post("/auth/login")
async def get_user_profile(
    payload = Depends(get_current_user_jwt),
    user_email = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth0_id = payload.get("sub")
    result = await db.execute(select(User).where(User.auth0_id == auth0_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(auth0_id=auth0_id, email=user_email)
        db.add(user)
        await db.commit()
        await db.refresh(user)

@router.get("/auth/github/status")
async def get_github_auth_status(
    payload = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    auth0_id = payload.get("sub")
    result = await db.execute(select(User).where(User.auth0_id == auth0_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return { 'connected': user.github_token is not None }

@router.get("/auth/github")
async def github_auth(state: str):
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={os.getenv('GITHUB_CLIENT_ID')}"
        f"&scope=repo"
        f"&state={state}"
    )

@router.get("/auth/github/callback")
async def github_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    auth0_id = (await get_current_user_jwt_from_token(state)).get("sub")

    result = await db.execute(select(User).where(User.auth0_id == auth0_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token_response = await exchange_code_for_token(code)
    access_token = token_response.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")
    encrypted_token = encrypt_token(access_token)

    user.github_token = encrypted_token
    await db.commit()

    return RedirectResponse(url=f"{os.getenv('FRONTEND_URL')}/integrations")
