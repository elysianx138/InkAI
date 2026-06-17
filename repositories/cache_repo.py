from database import get_redis
import random

class CacheRepo:
    """缓存访问层 --- 只读写 Redis"""

    def get_user(self,username:str) -> dict | None:
        """根据用户名获取用户信息"""
        redis = get_redis()
        data = redis.hgetall(f"user:{username}")
        if not data or "__NULL__" in data:
            return None
        return data
    
    def set_user(self,username:str,data:dict,ttl:int = 300):
        """设置用户信息"""
        redis = get_redis()
        redis.hset(f"user:{username}",mapping=data)
        redis.expire(f"user:{username}",ttl+random.randint(0,120))

    def set_user_null(self,username:str,ttl:int = 15):
        """设置用户信息为空"""
        redis = get_redis()
        redis.hset(f"user:{username}",mapping={"__NULL__":"1"})
        redis.expire(f"user:{username}",ttl+random.randint(0,20))