from pydantic import BaseModel, Field


class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    userpassword: str = Field(..., min_length=6, max_length=100, description="密码")
    email: str = Field(default="", description="邮箱")


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    userpassword: str = Field(..., min_length=6, max_length=100, description="密码")
    email: str = Field(..., description="邮箱")
