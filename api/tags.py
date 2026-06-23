from fastapi import APIRouter

from services.article_service import ArticleService

router = APIRouter()
article_service = ArticleService()


@router.get("/articles")
def get_articles_by_tag(tag: str):
    article_ids = article_service.get_articles_by_tag(tag)
    return {"articles": article_ids}
