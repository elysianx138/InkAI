from db import db


class ArticleRepo:
    """文章数据访问层 —— 只操心 SQL"""

    def create(self, title: str, content: str, author_id: int) -> int:
        return db.insert(
            "INSERT INTO articles (title, content, author_id) VALUES (%s, %s, %s)",
            (title, content, author_id)
        )
    
    def delete_article_by_id(self, article_id: int):
        return db.delete(
            "DELETE FROM articles WHERE id = %s" ,
            (article_id,)
        )

    def find_by_id(self, article_id: int) -> dict | None:
        return db.fetch_one(
            "SELECT id, title, content, author_id, likes, created_at FROM articles WHERE id = %s",
            (article_id,)
        )

    def find_latest(self) -> dict | None:
        return db.fetch_one(
            "SELECT id, title, content FROM articles ORDER BY id DESC LIMIT 1"
        )

    def find_hot(self, limit: int = 10) -> list[dict]:
        return db.fetch_all(
            "SELECT id, likes FROM articles ORDER BY likes DESC LIMIT %s",
            (limit,)
        )

    def find_tags_by_article(self, article_id: int) -> list[str]:
        rows = db.fetch_all(
            "SELECT tag FROM article_tags WHERE article_id = %s",
            (article_id,)
        )
        return [row["tag"] for row in rows] if rows else []

    def find_articles_by_tag(self, tag: str) -> list[int]:
        rows = db.fetch_all(
            "SELECT article_id FROM article_tags WHERE tag = %s",
            (tag,)
        )
        return [row["article_id"] for row in rows] if rows else []

    def find_titles_by_ids(self, ids: list[int]) -> dict[int, str]:
        """批量查文章标题，返回 {id: title}"""
        if not ids:
            return {}
        placeholders = ",".join(["%s"] * len(ids))
        rows = db.fetch_all(
            f"SELECT id, title FROM articles WHERE id IN ({placeholders})",
            ids
        )
        return {row["id"]: row["title"] for row in rows} if rows else {}

    def add_tags(self, article_id: int, tags: list[str]):
        if tags:
            db.insert_many(
                "INSERT INTO article_tags (article_id, tag) VALUES (%s, %s)",
                [(article_id, tag) for tag in tags]
            )

    def increment_likes(self, article_id: int):
        db.update(
            "UPDATE articles SET likes = likes + 1 WHERE id = %s",
            (article_id,)
        )

    def get_likes(self, article_id: int) -> int | None:
        row = db.fetch_one(
            "SELECT likes FROM articles WHERE id = %s",
            (article_id,)
        )
        return row["likes"] if row else None
