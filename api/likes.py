from database import get_redis
from fastapi import APIRouter,HTTPException
from db import db
import random

router = APIRouter()

lua_script = """
    local likes = redis.call("INCR",KEYS[1])
    redis.call("ZINCRBY",KEYS[2],1,KEYS[3])
    return likes
    """

@router.post("/articles/{article_id}/likes")
def post_article_likes(article_id:int):
    redis = get_redis()
    cache_key = f"article:{article_id}:likes"

    likes = redis.eval(lua_script,3,cache_key,"article:hot",str(article_id))
    db.update("UPDATE articles SET likes = likes+1 WHERE id = %s",(article_id,))

    return {"message":"Success","article_id":article_id,"likes":int(likes)}
    
@router.get("/articles/{article_id}/likes")
def get_article_likes(article_id:int):
    redis = get_redis()
    cache_key = f"article:{article_id}:likes"
    lock_key = f"lock:article:{article_id}:likes"

    data = redis.get(cache_key)
    if data is not None:
        if data == "__NULL__":
            raise HTTPException(status_code=404,detail="Article not found")
        return {"likes":int(data)}
    
    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)
        if locked:
            try:
                likes = db.fetch_one("SELECT likes FROM articles WHERE id = %s",(article_id,))
                if likes:
                    redis.setex(cache_key,3600+random.randint(0,60),likes["likes"])
                    return {"likes":int(likes["likes"])}
                
                else:
                    redis.setex(cache_key,3600+random.randint(0,60),"__NULL__")
                    raise HTTPException(status_code=404,detail="Article not found")
            finally:
                redis.delete(lock_key)

        else:
            raise HTTPException(status_code=429,detail="Too many requests")


@router.get("/articles/hot")
def get_article_hot():
    redis = get_redis()
    cache_key = "hot:articles"
    lock_key = "lock:hot:articles"

    data = redis.zrevrange(cache_key,0,9,withscores=True)
    if data:
        result = [{"article_id":aid,"likes":int(score)} for aid,score in data]
        return {"articles":result,"source":"cache"}
    
    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)
        if locked:
            try:
                result = db.fetch_all("SELECT id,likes FROM articles ORDER BY likes DESC LIMIT 10")
                for item in result:
                    redis.zadd(cache_key,{item["id"]:item["likes"]})
                redis.expire(cache_key,300+random.randint(0,120))
                return {"articles":[{"article_id":item["id"],"likes":item["likes"]} for item in result],"source":"database"}

            finally:
                redis.delete(lock_key)

        else:
            raise HTTPException(status_code=429,detail="Too many requests")