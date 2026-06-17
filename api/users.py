from fastapi import APIRouter, Header
from services.auth_service import AuthService
from core.exceptions import UnauthorizeError
from core.security import decode_token
from models.user import UserLoginRequest
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()


@router.post("/signup")
def logup(user:UserLoginRequest):
    logger.info(f"{user.username}正在尝试注册")
    result = auth_service.register(user.username,user.userpassword,user.email)
    logger.info(f"用户注册成功:{user.username},id:{result['id']}")
    return {"message":"用户注册成功","id":result["id"]}
@router.post("/login")
def login(user:UserLoginRequest):
    logger.info(f"{user.username}正在尝试登录")
    result = auth_service.login(user.username,user.userpassword)
    logger.info(f"用户登录成功:{user.username},token:{result['token']}")
    return {"message":"用户登录成功","token":result["token"]}
    
@router.get("/me")
def get_me(authorization:str=Header(None)):
    if not authorization or " " not in authorization:
        raise UnauthorizeError()
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise UnauthorizeError()
    return {"username":payload.get("username"),"user_id":payload.get("user_id")}