import random
from database import get_redis
from repositories.article_repo import ArticleRepo
from core.exceptions import NotFoundError, TooManyRequestsError


class ArticleService:
    """文章业务逻辑层 —— 缓存穿透保护 + 分布式锁"""

    def __init__(self):
        self.article_repo = ArticleRepo()

    # ========== 创建文章 ==========

    def create_article(self, title: str, content: str, tags: list[str], author_id: int) -> int:
        article_id = self.article_repo.create(title, content, author_id)

        if tags:
            self.article_repo.add_tags(article_id, tags)
            r = get_redis()
            r.sadd(f"article:{article_id}:tags", *tags)
            r.expire(f"article:{article_id}:tags", 300 + random.randint(0, 120))

        r = get_redis()
        r.hset(f"article:{article_id}", mapping={
            "title": title,
            "content": content
        })
        r.expire(f"article:{article_id}", 300 + random.randint(0, 120))

        r.hset("article:latest", mapping={
            "article_id": str(article_id),
            "title": title,
            "content": content
        })
        r.expire("article:latest", 300 + random.randint(0, 120))

        return article_id

    # ========== 获取单篇文章（缓存穿透保护） ==========

    def get_article(self, article_id: int) -> dict:
        redis = get_redis()
        cache_key = f"article:{article_id}"
        lock_key = f"lock:article:{article_id}"

        # 查缓存
        data = redis.hgetall(cache_key)
        if data:
            if "__NULL__" in data:
                raise NotFoundError("文章不存在")
            tags = redis.smembers(f"article:{article_id}:tags")
            return {
                "title": data.get("title"),
                "content": data.get("content"),
                "tags": list(tags) if tags else []
            }

        # 缓存未命中 → 分布式锁 + 查数据库
        if not redis.set(lock_key, "1", nx=True, ex=10):
            raise TooManyRequestsError("请求过于频繁")

        try:
            article = self.article_repo.find_by_id(article_id)
            if not article:
                redis.hset(cache_key, mapping={"__NULL__": "1"})
                redis.expire(cache_key, 120 + random.randint(0, 60))
                raise NotFoundError("文章不存在")

            redis.hset(cache_key, mapping={
                "title": article["title"],
                "content": article["content"]
            })
            redis.expire(cache_key, 300 + random.randint(0, 120))

            tags = self.article_repo.find_tags_by_article(article_id)
            if tags:
                r = get_redis()
                r.sadd(f"article:{article_id}:tags", *tags)
                r.expire(f"article:{article_id}:tags", 300 + random.randint(0, 120))

            return {"title": article["title"], "content": article["content"], "tags": tags}
        finally:
            redis.delete(lock_key)

    # ========== 获取文章标签 ==========

    def get_article_tags(self, article_id: int) -> list[str]:
        redis = get_redis()
        cache_key = f"article:{article_id}:tags"
        lock_key = f"lock:article:{article_id}:tags"

        tags = redis.smembers(cache_key)
        if tags:
            if "__NULL__" in tags:
                raise NotFoundError("文章不存在")
            return list(tags)

        if not redis.set(lock_key, "1", nx=True, ex=10):
            raise TooManyRequestsError()

        try:
            rows = self.article_repo.find_tags_by_article(article_id)
            if not rows:
                redis.sadd(cache_key, "__NULL__")
                redis.expire(cache_key, 120 + random.randint(0, 60))
                raise NotFoundError("文章不存在")

            redis.sadd(cache_key, *rows)
            redis.expire(cache_key, 300 + random.randint(0, 120))
            return rows
        finally:
            redis.delete(lock_key)

    # ========== 获取最新文章 ==========

    def get_latest_article(self) -> dict:
        redis = get_redis()
        cache_key = "article:latest"
        lock_key = "lock:article:latest"

        data = redis.hgetall(cache_key)
        if data:
            if "__NULL__" in data:
                raise NotFoundError("文章不存在")
            return {
                "article_id": data.get("article_id"),
                "title": data.get("title"),
                "content": data.get("content")
            }

        if not redis.set(lock_key, "1", nx=True, ex=10):
            raise TooManyRequestsError()

        try:
            article = self.article_repo.find_latest()
            if not article:
                redis.hset(cache_key, mapping={"__NULL__": "1"})
                redis.expire(cache_key, 120 + random.randint(0, 60))
                raise NotFoundError("文章不存在")

            redis.hset(cache_key, mapping={
                "article_id": article["id"],
                "title": article["title"],
                "content": article["content"]
            })
            redis.expire(cache_key, 300 + random.randint(0, 120))
            return {"article_id": article["id"], "title": article["title"], "content": article["content"]}
        finally:
            redis.delete(lock_key)

    # ========== 按标签搜索文章 ==========

    def get_hot_with_titles(self) -> list[dict]:
        """获取热门文章列表，附加标题"""
        hot = self.article_repo.find_hot(10)
        if not hot:
            return []
        ids = [item["id"] for item in hot]
        titles = self.article_repo.find_titles_by_ids(ids)
        return [
            {"article_id": item["id"], "title": titles.get(item["id"], f"文章#{item['id']}"), "likes": item["likes"]}
            for item in hot
        ]

    def get_articles_by_tag(self, tag: str) -> list[int]:
        redis = get_redis()
        cache_key = f"tags:{tag}"
        lock_key = f"lock:tags:{tag}"

        data = redis.smembers(cache_key)
        if data:
            if "__NULL__" in data:
                raise NotFoundError("标签不存在")
            return [int(aid) for aid in data]

        if not redis.set(lock_key, "1", nx=True, ex=10):
            raise TooManyRequestsError()

        try:
            article_ids = self.article_repo.find_articles_by_tag(tag)
            if not article_ids:
                redis.sadd(cache_key, "__NULL__")
                redis.expire(cache_key, 120 + random.randint(0, 60))
                raise NotFoundError("标签不存在")

            redis.sadd(cache_key, *article_ids)
            redis.expire(cache_key, 300 + random.randint(0, 120))
            return article_ids
        finally:
            redis.delete(lock_key)
