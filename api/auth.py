from fastapi import APIRouter, HTTPException
from db import db
from core.security import create_token
import os
import httpx

router = APIRouter()


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
    """GitHub 回调：用 code 换 token → 查用户信息 → 落库 → 签发 JWT"""

    # 1. 用 code 换 access_token
    token_resp = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
            "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
            "code": code,
            "redirect_uri": os.getenv("GITHUB_REDIRECT_URI", ""),
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="获取 GitHub access_token 失败")

    # 2. 获取 GitHub 用户信息
    user_resp = httpx.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    user_data = user_resp.json()
    github_id = str(user_data.get("id"))
    github_login = user_data.get("login", "")
    github_avatar = user_data.get("avatar_url", "")

    # 3. 查找或创建本地用户
    username = f"github_{github_id}"
    user = db.fetch_one(
        "SELECT id, username FROM users WHERE username = %s",
        (username,)
    )
    if not user:
        user_id = db.insert(
            "INSERT INTO users (username, userpassword, email) VALUES (%s, %s, %s)",
            (username, "", f"github_{github_id}@github.com")
        )
        user = {"id": user_id, "username": github_login}

    # 4. 签发 JWT
    token = create_token(int(user["id"]), user["username"])
    return {
        "username": user["username"],
        "token": token,
        "avatar": github_avatar,
    }
