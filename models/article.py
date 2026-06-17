from pydantic import BaseModel, Field


class ArticleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="文章标题")
    content: str = Field(..., description="文章内容")
    tags: list[str] = Field(default=[], description="标签列表")
