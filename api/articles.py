from fastapi import APIRouter, Header, HTTPException
from services.article_service import ArticleService
from core.security import decode_token
from models.article import ArticleCreateRequest
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
article_service = ArticleService()


@router.post("/articles")
def post_article(article: ArticleCreateRequest, authorization: str = Header(None)):
    if not authorization or " " not in authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    article_id = article_service.create_article(
        article.title, article.content, article.tags, payload["user_id"]
    )
    logger.info(f"Article created: id={article_id}, author={payload['username']}")
    return {"message": "Successfully created article", "article_id": article_id}


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
