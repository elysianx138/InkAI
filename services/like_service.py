import random
from database import get_redis
from repositories.article_repo import ArticleRepo
from core.exceptions import NotFoundError, TooManyRequestsError


# Lua 脚本：原子操作 —— 点赞数 + 热门榜 一步完成
LUA_LIKE_SCRIPT = """
    local likes = redis.call("INCR",KEYS[1])
    redis.call("ZINCRBY",KEYS[2],1,KEYS[3])
    return likes
"""


class LikeService:
    """点赞业务逻辑层"""

    def __init__(self):
        self.article_repo = ArticleRepo()

    def like_article(self, article_id: int) -> int:
        redis = get_redis()
        cache_key = f"article:{article_id}:likes"
        likes = redis.eval(LUA_LIKE_SCRIPT, 3, cache_key, "article:hot", str(article_id))
        self.article_repo.increment_likes(article_id)
        return int(likes)

    def get_likes(self, article_id: int) -> int:
        redis = get_redis()
        cache_key = f"article:{article_id}:likes"
        lock_key = f"lock:article:{article_id}:likes"

        data = redis.get(cache_key)
        if data is not None:
            if data == "__NULL__":
                raise NotFoundError("文章不存在")
            return int(data)

        if not redis.set(lock_key, "1", nx=True, ex=10):
            raise TooManyRequestsError()

        try:
            likes = self.article_repo.get_likes(article_id)
            if likes is not None:
                redis.setex(cache_key, 3600 + random.randint(0, 60), likes)
                return likes
            else:
                redis.setex(cache_key, 60, "__NULL__")
                raise NotFoundError("文章不存在")
        finally:
            redis.delete(lock_key)

    def get_hot_articles(self) -> list[dict]:
        redis = get_redis()
        cache_key = "hot:articles"
        lock_key = "lock:hot:articles"

        data = redis.zrevrange(cache_key, 0, 9, withscores=True)
        if data:
            return [{"article_id": int(aid), "likes": int(score)} for aid, score in data]

        if not redis.set(lock_key, "1", nx=True, ex=10):
            raise TooManyRequestsError()

        try:
            result = self.article_repo.find_hot(10)
            for item in result:
                redis.zadd(cache_key, {item["id"]: item["likes"]})
            redis.expire(cache_key, 300 + random.randint(0, 120))
            return [{"article_id": item["id"], "likes": item["likes"]} for item in result]
        finally:
            redis.delete(lock_key)
