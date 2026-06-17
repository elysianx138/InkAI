import httpx
import os
from repositories.user_repo import UserRepo
from repositories.cache_repo import CacheRepo
from core.security import hash_password,verify_password,create_token
from core.exceptions import ConflictError,NotFoundError,UnauthorizeError

class AuthService:
    def __init__(self):
        self.user_repo = UserRepo()
        self.cache_repo = CacheRepo()

    def register(self,username:str,password:str,email:str) -> dict:
        # 查缓存
        cached = self.cache_repo.get_user(username)
        if cached:
            raise ConflictError("用户名已经存在")
        # 查数据库
        user = self.user_repo.find_by_username(username)
        if user:
            raise ConflictError("用户名已经存在")
        
        # 创建用户
        hashed = hash_password(password)
        user_id = self.user_repo.create_user(username,hashed,email)

        # 更新缓存
        self.cache_repo.set_user(username,{"username":username,"email":email,"password":hashed,"id":user_id})

        return {"username":username,"id":user_id}
    
    def login(self,username:str,password:str) -> dict:
        # 尝试缓存
        cached = self.cache_repo.get_user(username)
        if cached:
            if not verify_password(password,cached["password"]):
                raise NotFoundError("用户名或者密码错误")
            token = create_token(int(cached["id"]),cached["username"])
            return {"username":cached["username"],"token":token}
        # 尝试数据库
        user = self.user_repo.find_by_username(username)
        if not user:
            self.cache_repo.set_user_null(username)
            raise NotFoundError("用户名或者密码错误")
        
        if not verify_password(password,user["userpassword"]):
            raise NotFoundError("用户名或者密码错误")
        
        # 尝试缓存
        self.cache_repo.set_user(username,{
            "username":user["username"],
            "password":user["userpassword"],
            "id":user["id"]
        })
        token = create_token(int(user["id"]),user["username"])
        return {"username":user["username"],"token":token}

    def github_login(self, code: str) -> dict:
        """GitHub OAuth 登录：用 code 换 token → 查用户 → 落库 → 签发 JWT"""

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
            raise UnauthorizeError("获取 GitHub access_token 失败")

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
        user = self.user_repo.find_by_username(username)
        if not user:
            user_id = self.user_repo.create_user(username, "", f"github_{github_id}@github.com")
            user = {"id": user_id, "username": github_login}

        # 4. 签发 JWT
        token = create_token(int(user["id"]), user["username"])
        return {"username": user["username"], "token": token, "avatar": github_avatar}