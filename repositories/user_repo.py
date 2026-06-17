from db import db

class UserRepo:
    """用户数据访问层 --- 数据库"""

    def find_by_username(self,username:str) -> dict | None:
        return db.fetch_one(
            "SELECT id,username,userpassword,email FROM users WHERE username = %s",
            (username,)
        )
    
    def create_user(self,username:str,password:str,email:str) -> int:
        return db.insert(
            "INSERT INTO users (username,userpassword,email) VALUES (%s,%s,%s)",
            (username,password,email)
        )