import logging
from fastapi import APIRouter, Request, Header, Form
from fastapi.responses import HTMLResponse
from services.auth_service import AuthService
from services.article_service import ArticleService
from services.like_service import LikeService
from core.security import decode_token
from core.exceptions import AppException, NotFoundError, TooManyRequestsError
from utils.rate_limit import rate_limit_ip

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hx")
auth_service = AuthService()
article_service = ArticleService()
like_service = LikeService()


# ─── 辅助函数 ─────────────────────────────────────────


def _get_user_id(authorization: str | None) -> int | None:
    """尝试解析 JWT，返回 user_id 或 None"""
    if not authorization:
        return None
    parts = authorization.split(" ")
    if len(parts) < 2 or not parts[1]:
        return None
    payload = decode_token(parts[1])
    return payload["user_id"] if payload else None


def _err_html(message: str, status: int = 400) -> HTMLResponse:
    return HTMLResponse(f'<div class="error-msg">{message}</div>', status_code=status)


def _success_html(message: str) -> str:
    return f'<div class="success-msg">{message}</div>'


# ─── 首页 ─────────────────────────────────────────────


@router.get("/home", response_class=HTMLResponse)
def home(request: Request, authorization: str = Header(None)):
    """首页：最新文章 + 热门文章 + 标签搜索"""
    _get_user_id(authorization)  # 仅用于后续可能的功能，暂不处理

    return """
    <div class="home-page">
        <section class="hero">
            <h1>InkAI</h1>
            <p class="tagline">AI 协作写作平台 · 用文字连接思想</p>
        </section>

        <div class="search-bar">
            <input type="text" name="tag" placeholder="搜索标签…"
                   hx-get="/hx/articles/tag" hx-target="#search-results" hx-trigger="keyup changed delay:500ms">
        </div>
        <div id="search-results"></div>

        <section class="latest-article-section">
            <h2>最新文章</h2>
            <div id="latest-article" hx-get="/hx/articles/latest" hx-trigger="load"></div>
        </section>

        <section class="hot-articles-section">
            <h2>热门文章</h2>
            <div id="hot-articles" hx-get="/hx/articles/hot" hx-trigger="load"></div>
        </section>
    </div>
    """


# ─── 最新文章 ─────────────────────────────────────────


@router.get("/articles/latest", response_class=HTMLResponse)
def latest_article(request: Request, authorization: str = Header(None)):
    user_id = _get_user_id(authorization)
    if not user_id:
        rate_limit_ip("limit:none_user", request, max_request=30, window=60)

    try:
        article = article_service.get_latest_article()
    except NotFoundError:
        return '<p class="empty">还没有文章，来写第一篇吧！</p>'
    except TooManyRequestsError:
        return _err_html("请求过于频繁", 429)

    article_id = article.get("article_id")
    title = article.get("title", "无标题")
    content = article.get("content", "")

    return f"""
    <div class="article-card"
         {'hx-get="/hx/articles/' + str(article_id) + '" hx-target="#content" style="cursor:pointer"' if article_id else ''}>
        <h3>{title}</h3>
        <p>{content[:200]}{'…' if len(content) > 200 else ''}</p>
    </div>
    """


# ─── 登录 ─────────────────────────────────────────────


@router.get("/login", response_class=HTMLResponse)
def login_form():
    return """
    <div class="auth-page">
        <h2>登录</h2>
        <form hx-post="/hx/login" hx-target="#auth-result">
            <label>用户名
                <input type="text" name="username" required minlength="2">
            </label>
            <label>密码
                <input type="password" name="userpassword" required minlength="6">
            </label>
            <button type="submit">登录</button>
        </form>
        <div id="auth-result"></div>
        <p class="auth-switch">还没有账号？
            <a href="#" hx-get="/hx/register" hx-target="#content">立即注册</a>
        </p>
    </div>
    """


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    userpassword: str = Form(...),
):
    try:
        rate_limit_ip("limit:login", request, max_request=3, window=60)
        result = auth_service.login(username, userpassword)

        # 返回 token 嵌入在隐藏 div 中，前端 JS 通过 afterSwap 读取并存入 localStorage
        return HTMLResponse(f"""
        <div id="__token__" data-token="{result['token']}"></div>
        {_success_html("登录成功！正在跳转…")}
        <div hx-get="/hx/home" hx-trigger="load delay:500ms" hx-target="#content" hx-push-url="/"></div>
        """)
    except AppException as e:
        return _err_html(e.message, e.status)
    except Exception:
        logger.exception("Login error")
        return _err_html("登录失败，请稍后重试")


# ─── 注册 ─────────────────────────────────────────────


@router.get("/register", response_class=HTMLResponse)
def register_form():
    return """
    <div class="auth-page">
        <h2>注册</h2>
        <form hx-post="/hx/register" hx-target="#auth-result">
            <label>用户名
                <input type="text" name="username" required minlength="2">
            </label>
            <label>密码
                <input type="password" name="userpassword" required minlength="6">
            </label>
            <label>邮箱
                <input type="email" name="email" required>
            </label>
            <button type="submit">注册</button>
        </form>
        <div id="auth-result"></div>
        <p class="auth-switch">已有账号？
            <a href="#" hx-get="/hx/login" hx-target="#content">去登录</a>
        </p>
    </div>
    """


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    username: str = Form(...),
    userpassword: str = Form(...),
    email: str = Form(""),
):
    try:
        rate_limit_ip("limit:register", request, max_request=5, window=60)
        auth_service.register(username, userpassword, email)
        return HTMLResponse(f"""
        {_success_html("注册成功！即将跳转登录…")}
        <div hx-get="/hx/login" hx-trigger="load delay:1000ms" hx-target="#content"></div>
        """)
    except AppException as e:
        return _err_html(e.message, e.status)
    except Exception:
        logger.exception("Register error")
        return _err_html("注册失败，请稍后重试")


# ─── 热门文章列表（片段） ─────────────────────────────


@router.get("/articles/hot", response_class=HTMLResponse)
def hot_articles():
    try:
        hot = article_service.get_hot_with_titles()
        if not hot:
            return '<p class="empty">暂无热门文章</p>'
        items = "".join(
            f'<div class="hot-item" hx-get="/hx/articles/{h["article_id"]}" hx-target="#content" style="cursor:pointer">'
            f'<span class="hot-title">{h["title"]}</span>'
            f'<span class="hot-likes">❤️ {h["likes"]}</span>'
            f'</div>'
            for h in hot
        )
        return f'<div class="hot-list">{items}</div>'
    except Exception:
        return '<p class="empty">暂无热门文章</p>'


# ─── 创建文章 ─────────────────────────────────────────


@router.get("/articles/create", response_class=HTMLResponse)
def create_article_form(authorization: str = Header(None)):
    user_id = _get_user_id(authorization)
    if not user_id:
        return _err_html("请先登录", 401)

    return """
    <div class="create-page">
        <h2>写文章</h2>
        <form hx-post="/hx/articles" hx-target="#create-result">
            <label>标题
                <input type="text" name="title" required maxlength="200">
            </label>
            <label>内容
                <textarea name="content" required rows="15"></textarea>
            </label>
            <label>标签（逗号分隔）
                <input type="text" name="tags" placeholder="例如: AI, Python, 随笔">
            </label>
            <button type="submit">发布</button>
        </form>
        <div id="create-result"></div>
    </div>
    """


@router.post("/articles", response_class=HTMLResponse)
def create_article_submit(
    authorization: str = Header(None),
    title: str = Form(...),
    content: str = Form(...),
    tags: str = Form(""),
):
    user_id = _get_user_id(authorization)
    if not user_id:
        return _err_html("请先登录", 401)

    try:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        article_id = article_service.create_article(title, content, tag_list, user_id)
        return HTMLResponse(f"""
        {_success_html("文章发布成功！")}
        <div hx-get="/hx/articles/{article_id}" hx-trigger="load delay:500ms"
             hx-target="#content" hx-push-url="/articles/{article_id}"></div>
        """)
    except AppException as e:
        return _err_html(e.message, e.status)
    except Exception:
        logger.exception("Create article error")
        return _err_html("发布失败，请稍后重试")


# ─── 搜索标签 ─────────────────────────────────────────


@router.get("/articles/tag", response_class=HTMLResponse)
def search_by_tag(tag: str, request: Request, authorization: str = Header(None)):
    if not tag.strip():
        return '<div id="search-results"></div>'

    user_id = _get_user_id(authorization)
    if not user_id:
        rate_limit_ip("limit:none_user", request, max_request=30, window=60)

    try:
        ids = article_service.get_articles_by_tag(tag.strip())
        titles = article_service.article_repo.find_titles_by_ids(ids)
        items = "".join(
            f'<div class="search-item" hx-get="/hx/articles/{aid}" hx-target="#content" style="cursor:pointer">'
            f'{titles.get(aid, f"文章#{aid}")}</div>'
            for aid in ids
        )
        return f"""
        <div id="search-results">
            <h4>标签「{tag.strip()}」下的文章</h4>
            {items if items else '<p class="empty">没有找到相关文章</p>'}
        </div>
        """
    except NotFoundError:
        return f"""
        <div id="search-results">
            <h4>标签「{tag.strip()}」下的文章</h4>
            <p class="empty">没有找到相关文章</p>
        </div>
        """
    except TooManyRequestsError as e:
        return _err_html(e.message, 429)


# ─── 文章详情 ─────────────────────────────────────────


@router.get("/articles/{article_id}", response_class=HTMLResponse)
def article_detail(article_id: int, request: Request, authorization: str = Header(None)):
    user_id = _get_user_id(authorization)
    if not user_id:
        rate_limit_ip("limit:none_user", request, max_request=30, window=60)

    try:
        article = article_service.get_article(article_id)
    except NotFoundError as e:
        return _err_html(e.message, 404)
    except TooManyRequestsError as e:
        return _err_html(e.message, 429)

    try:
        tags = article_service.get_article_tags(article_id)
    except (NotFoundError, TooManyRequestsError):
        tags = []

    try:
        likes = like_service.get_likes(article_id)
    except (NotFoundError, TooManyRequestsError):
        likes = 0

    tag_badges = "".join(f'<span class="tag-badge">{t}</span>' for t in tags)
    title = article.get("title", "")
    content = article.get("content", "")

    like_disabled = "disabled" if not user_id else ""
    like_btn_text = "❤️" if user_id else "🔒"

    return f"""
    <div class="article-detail">
        <a href="#" class="back-link" hx-get="/hx/home" hx-target="#content" hx-push-url="/">← 返回首页</a>
        <article>
            <h1>{title}</h1>
            <div class="article-meta">
                <div class="tags">{tag_badges}</div>
                <div class="likes" id="likes-{article_id}">
                    <button class="like-btn"
                            hx-post="/hx/articles/{article_id}/likes"
                            hx-target="#likes-{article_id}"
                            hx-swap="outerHTML"
                            {like_disabled}>
                        {like_btn_text} <span id="like-count">{likes}</span>
                    </button>
                    {'' if user_id else '<span class="login-hint">登录后可点赞</span>'}
                </div>
            </div>
            <div class="article-content">{content}</div>
        </article>
    </div>
    """


# ─── 点赞 ─────────────────────────────────────────────


@router.post("/articles/{article_id}/likes", response_class=HTMLResponse)
def like_article(article_id: int, authorization: str = Header(None)):
    user_id = _get_user_id(authorization)
    if not user_id:
        return _err_html("请先登录", 401)

    try:
        new_likes = like_service.like_article(article_id)
        return f"""
        <div class="likes" id="likes-{article_id}">
            <button class="like-btn liked"
                    hx-post="/hx/articles/{article_id}/likes"
                    hx-target="#likes-{article_id}"
                    hx-swap="outerHTML">
                ❤️ <span>{new_likes}</span>
            </button>
        </div>
        """
    except Exception:
        return _err_html("点赞失败，请稍后重试")


# ─── 退出 ─────────────────────────────────────────────


@router.post("/logout", response_class=HTMLResponse)
def logout():
    return HTMLResponse(f"""
    <div id="__logout__"></div>
    {_success_html("已退出登录")}
    <div hx-get="/hx/home" hx-trigger="load delay:500ms" hx-target="#content" hx-push-url="/"></div>
    """)
