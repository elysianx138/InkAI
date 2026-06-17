from fastapi import APIRouter
from services.like_service import LikeService

router = APIRouter()
like_service = LikeService()


@router.post("/articles/{article_id}/likes")
def post_article_likes(article_id: int):
    likes = like_service.like_article(article_id)
    return {"message": "Success", "article_id": article_id, "likes": likes}


@router.get("/articles/{article_id}/likes")
def get_article_likes(article_id: int):
    likes = like_service.get_likes(article_id)
    return {"likes": likes}


@router.get("/articles/hot")
def get_hot_articles():
    result = like_service.get_hot_articles()
    return {"articles": result}
