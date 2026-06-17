from fastapi import APIRouter
import os,httpx

router = APIRouter()

@router.get("/auth/github/login")
def github_login():
    params={
        "client_id":os.getenv("GITHUB_CLIENT_ID",""),
        "redirect_uri":os.getenv("GITHUB_REDIRECT_URI",""),
        "scope":"read:user"
    }
    url = f"https://github.com/login/oauth/authorize?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&scope={params['scope']}"
    return {"url":url}

@router.get("/auth/github/callback")
def github_callback(code:str):
    response = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id":os.getenv("GITHUB_CLIENT_ID",""),
            "client_secret":os.getenv("GITHUB_CLIENT_SECRET",""),
            "code":code,
            "redirect_uri":os.getenv("GITHUB_REDIRECT_URI","")
        },
        headers={"Accept":"application/json"},
        timeout=30,
        verify=False
    )
    data =  response.json()
    access_token = data.get("access_token")
    
    user_response = httpx.get(
        "https://api.github.com/user",
        headers={"Authorization":f"Bearer {access_token}"},
        timeout=30,
        verify=False
    )
    user_data = user_response.json()
    return {"user":user_data}

