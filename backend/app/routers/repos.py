from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..utils.auth import get_current_user_jwt
from ..utils.db import get_db
from ..utils.crypto import decrypt_token
from ..models import User, UserRepository
import aiohttp
from typing import List
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

router = APIRouter()

class Repository(BaseModel):
    id: int
    name: str
    description: str = None
    private: bool
    stars: int
    html_url: str

class SaveRepositoriesRequest(BaseModel):
    repositories: List[Repository]

@router.get("/api/github/repositories")
async def get_github_repositories(
    payload=Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    auth0_id = payload.get('sub')
    result = await db.execute(
        select(User).options(selectinload(User.repositories)).where(User.auth0_id == auth0_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.github_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub not connected")

    encrypted_token = user.github_token
    access_token = decrypt_token(encrypted_token)

    headers = {'Authorization': f'token {access_token}', 'Accept': 'application/vnd.github.v3+json'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get('https://api.github.com/user/repos?per_page=100') as response:
            if response.status != 200:
                detail = await response.text()
                raise HTTPException(status_code=response.status, detail=f"GitHub API error: {detail}")
            repos = await response.json()
            selected_repo_ids = {repo.repo_id for repo in user.repositories}
            formatted_repos = []
            for repo in repos:
                formatted_repos.append({
                    'id': repo['id'],
                    'name': repo['name'],
                    'description': repo['description'],
                    'private': repo['private'],
                    'stars': repo['stargazers_count'],
                    'html_url': repo['html_url'],
                    'enabled': repo['id'] in selected_repo_ids
                })
            return formatted_repos

@router.post("/api/github/save-repositories")
async def save_github_repositories(
    data: SaveRepositoriesRequest,
    payload=Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    auth0_id = payload.get('sub')
    result = await db.execute(select(User).where(User.auth0_id == auth0_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.execute(
        UserRepository.__table__.delete().where(UserRepository.user_id == user.id)
    )

    repositories = []
    for repo in data.repositories:
        user_repo = UserRepository(
            user_id=user.id,
            repo_id=repo.id,
            repo_name=repo.name
        )
        repositories.append(user_repo)

    db.add_all(repositories)
    await db.commit()
    return {"message": "Repositories saved successfully"}
