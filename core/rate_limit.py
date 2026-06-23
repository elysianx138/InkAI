from fastapi import Request
from database import get_redis
from core.exceptions import TooManyRequestsError

def rate_limit_ip(key:str,request:Request,max_request:int=5,window:int=60):
    """
    通过用户ip对用户账号注册以及登录进行限流
    ======================
    通过获取用户ip
    如果用户在限流时间内达到限流次数,抛出TooManyRequestsError
    """
    redis = get_redis()
    ip = request.client.host
    cache_key = f"{key}:{ip}"
    count = redis.incr(cache_key)
    
    if count == 1:
        redis.expire(cache_key,window)
    if count > max_request:
        raise TooManyRequestsError()

def rate_limit_id(user_id:int,key:str,max_request:int=10,window:int=360):
    """
    通过用户id对用户操作进行限流
    以防止垃圾内容的过多产生
    ======================
    通过获取用户id
    如果用户在限流时间内达到限流次数,抛出TooManyRequestsError
    """
    redis = get_redis()

    cache_key = f"{key}:{user_id}"
    count = redis.incr(cache_key)

    if count == 1:
        redis.expire(cache_key,window)
    if count > max_request:
        raise TooManyRequestsError()

        