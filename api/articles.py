import logging

from fastapi import APIRouter, Depends
from services.article_service import ArticleService
from models.article import ArticleCreateRequest
from core.rate_limit import rate_limit_id
from core.get_user_authorization import get_user_authorization


logger = logging.getLogger(__name__)
router = APIRouter()
article_service = ArticleService()


@router.post("/articles")
def post_article(article: ArticleCreateRequest, user = Depends(get_user_authorization)):
    rate_limit_id(key=f"limit:article:{user["user_id"]}", id=user["user_id"])
    article_id = article_service.create_article(
        article.title, article.content, article.tags, user["user_id"]
    )
    logger.info(f"Article created: id={article_id}, author={user['username']}")
    return {"message": "Successfully created article", "article_id": article_id}

@router.delete("/articles/{article_id}")
def delete_article(article_id: int, user = Depends(get_user_authorization)):
    article_service.delete_article(article_id, user["user_id"])
    return {"message": "Successfully deleted article", "article_id": article_id}


@router.get("/articles/{article_id}")
def get_article(article_id: int):
    result = article_service.get_article(article_id)
    return result


@router.get("/articles/{article_id}/tags")
def get_article_tags(article_id: int):
    tags = article_service.get_article_tags(article_id)
    return {"tags": tags}


@router.get("/article/latest")
def get_latest_article():
    result = article_service.get_latest_article()
    return result
