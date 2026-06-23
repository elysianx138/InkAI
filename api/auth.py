import os

from fastapi import APIRouter

from services.auth_service import AuthService


router = APIRouter()
auth_service = AuthService()


@router.get("/auth/github/login")
def github_login():
    """返回 GitHub OAuth 授权页 URL"""
    client_id = os.getenv("GITHUB_CLIENT_ID", "")
    redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "")
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}&redirect_uri={redirect_uri}&scope=read:user"
    )
    return {"url": url}


@router.get("/auth/github/callback")
def github_callback(code: str):
    """GitHub 回调：调用 service 完成登录"""
    result = auth_service.github_login(code)
    return result
