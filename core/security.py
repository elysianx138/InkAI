import bcrypt
import os
import time
from utils.jwt import encode as jwt_encode,decode as jwt_decode


# === bcrypt 密码加密 ===
def hash_password(password:str) -> str:
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()

# === bcrypt 密码验证 ===
def verify_password(password:str,hashed:str) -> bool:
    return bcrypt.checkpw(password.encode(),hashed.encode())


# === jwt 加密 ===
def create_token(user_id:int,username:str) -> str:
    secret = os.getenv("JWT_SECRET","myblog_jwt_secret")
    expire = int(os.getenv("JWT_TOKEN_EXPIRE",3600))
    payload = {
        "user_id":user_id,
        "username":username,
        "exp":time.time()+expire
    }
    return jwt_encode(payload,secret)


# === jwt 解密 ===
def decode_token(token:str) -> dict | None:
    secret = os.getenv("JWT_SECRET","myblog_jwt_secret")
    return jwt_decode(token,secret)
