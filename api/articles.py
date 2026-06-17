from database import get_redis
from fastapi import APIRouter,HTTPException,Header
from db import db
from pydantic import BaseModel
from utils.jwt import decode as jwt_decode
import random,os

router = APIRouter()

class Article(BaseModel):
    title:str
    content:str
    tags:list[str] = []

# Post new article!
@router.post("/articles")
def post_articles(article:Article,authorization:str=Header(None)):
    token = authorization.split(" ")[1]
    payload = jwt_decode(token,os.getenv("JWT_SECRET","myblog_jwt_secret"))
    if not payload:
        raise HTTPException(status_code=401,detail="Invalid token")
    redis = get_redis()
    article_id = db.insert("INSERT INTO articles (title,content,author_id) VALUES (%s,%s,%s)", (article.title,article.content,payload["user_id"]))
    if article.tags:
        db.insert_many("INSERT INTO article_tags (article_id,tag) VALUES (%s,%s)", [(article_id,tag) for tag in article.tags])
        redis.sadd(f"article:{article_id}:tags",*article.tags)
        redis.expire(f"article:{article_id}:tags",300+random.randint(0,120))
    redis.hset(f"article:{article_id}",mapping={
        "title":article.title,
        "content":article.content
    })
    redis.expire(f"article:{article_id}",300+random.randint(0,120))
    redis.hset("article:latest",mapping={
        "title":article.title,
        "content":article.content
    })
    redis.expire("article:latest",300+random.randint(0,120))
    return {"message":"Successfully created article","article_id":article_id}


# Get details of an article
@router.get("/articles/{article_id}")
def get_articles(article_id:int):
    redis = get_redis()
    lock_key = f"lock:article:{article_id}"
    cache_key = f"article:{article_id}"

    # Check cache
    data = redis.hgetall(cache_key)
    if data:
        if "__NULL__" in data:
            raise HTTPException(status_code=404,detail="Article not found")
        tags = redis.smembers(f"article:{article_id}:tags")
        return {"title":data.get("title"), "content":data.get("content"), "tags":list(tags) if tags else []}

    # If cache is not hit, fetch from database
    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)
        if locked:
            try:
                article = db.fetch_one("SELECT title,content FROM articles WHERE id = %s", (article_id,))
                if article:
                    redis.hset(cache_key,mapping={
                        "title":article["title"],
                        "content":article["content"]
                    })
                    redis.expire(cache_key,300+random.randint(0,120))

                    # Fetch and cache tags
                    rows = db.fetch_all("SELECT tag FROM article_tags WHERE article_id = %s", (article_id,))
                    tag_list = [row["tag"] for row in rows] if rows else []
                    if tag_list:
                        redis.sadd(f"article:{article_id}:tags", *tag_list)
                        redis.expire(f"article:{article_id}:tags", 300+random.randint(0,120))

                    return {"title":article["title"], "content":article["content"], "tags":tag_list}
                else:
                    redis.hset(cache_key,mapping={
                        "__NULL__":"1"
                    })
                    redis.expire(cache_key,120+random.randint(0,60))
                    raise HTTPException(status_code=404,detail="Article not found")
            finally:
                redis.delete(lock_key)
        else:
            raise HTTPException(status_code=429,detail="Too many requests")

@router.get("/articles/{article_id}/tags")
def get_articles_tags(article_id:int):
    redis = get_redis()
    cache_key = f"article:{article_id}:tags"
    lock_key = f"lock:article:{article_id}:tags"

    tags = redis.smembers(cache_key)
    if tags:
        if "__NULL__" in tags:
            raise HTTPException(status_code=404,detail="Article not found")
        return {"tags":list(tags)}
    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)
        if locked:
            try:
                rows = db.fetch_all("SELECT tag FROM article_tags WHERE article_id = %s", (article_id,))
                if rows:
                    tags = [row["tag"] for row in rows]
                    redis.sadd(cache_key,*tags)
                    redis.expire(cache_key,300+random.randint(0,120))
                    return {"tags":list(tags)}
                else:
                    redis.sadd(cache_key,"__NULL__")
                    redis.expire(cache_key,120+random.randint(0,60))
                    raise HTTPException(status_code=404,detail="Article not found")
            finally:
                redis.delete(lock_key)
        
        else:
            raise HTTPException(status_code=429,detail="Too many requests")

# Get the latest article
@router.get("/article/latest")
def get_latest_articles():
    redis = get_redis()
    cache_key = "article:latest"
    lock_key = "lock:article:latest"

    data = redis.hgetall(cache_key)
    if data:
        if "__NULL__" in data:
            raise HTTPException(status_code=404,detail="Article not found")
        return {"title":data.get("title"), "content":data.get("content")}

    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)
        if locked:
            try:
                article = db.fetch_one("SELECT title,content FROM articles ORDER BY id DESC LIMIT 1")
                if article:
                    redis.hset(cache_key,mapping={
                        "title":article["title"],
                        "content":article["content"]
                    })
                    redis.expire(cache_key,300+random.randint(0,120))
                    return {"title":article["title"], "content":article["content"]}
                else:
                    redis.hset(cache_key,mapping={
                        "__NULL__":"1"
                    })
                    redis.expire(cache_key,120+random.randint(0,60))
                    raise HTTPException(status_code=404,detail="Article not found")
            finally:
                redis.delete(lock_key)
        else:
            raise HTTPException(status_code=429,detail="Too many requests")
