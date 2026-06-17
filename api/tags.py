from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from database import get_redis
from db import db
import random
router = APIRouter()

@router.get("/articles")
def get_articles_by_tag(tag:str):
    redis = get_redis()
    cache_key = f"tags:{tag}"
    lock_key = f"lock:tags:{tag}"

    data = redis.smembers(cache_key)
    if data:
        if "__NULL__" in data:
            raise HTTPException(status_code=404,detail="Tag not found")
        return {"articles":[int(aid) for aid in data],"source":"cache"}
    
    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)
        if locked:
            try:
                rows = db.fetch_all("SELECT article_id FROM article_tags WHERE tag = %s", (tag,))
                if rows:
                    article_ids = [row["article_id"] for row in rows]
                    redis.sadd(cache_key,*article_ids)
                    redis.expire(cache_key,300+random.randint(0,120))
                    return {"articles":list(article_ids),"source":"database"}
                else:
                    redis.sadd(cache_key,"__NULL__")
                    redis.expire(cache_key,120+random.randint(0,60))
                    raise HTTPException(status_code=404,detail="Tag not found")
            finally:
                redis.delete(lock_key)

        else:
            raise HTTPException(status_code=429,detail="Too many requests")
        