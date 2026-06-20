from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from core.exceptions import AppException
from contextlib import asynccontextmanager
from config import CONFIG as config
from datetime import datetime
from api.users import router as users_router
from api.articles import router as articles_router
from api.likes import router as likes_router
from api.tags import router as tags_router
from api.auth import router as auth_router
from api.html_routes import router as html_router
import logging

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("="*60)
    logger.info("✔Start up successfully!")
    logger.info(f"🌏name:{config.name};version:{config.version};⏰Start time:{datetime.now()};")
    yield
    logger.info("="*60)
    logger.info("✔Shut down successfully!")

app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(articles_router)
app.include_router(likes_router)
app.include_router(tags_router)
app.include_router(auth_router)
app.include_router(html_router)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.middleware("http")
async def add_security_headers(request,call_next):
    response = await call_next(request)
    # Add security headers
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Clickjacking protection
    response.headers["X-Frame-Options"] = "DENY"
    # XXS Protection
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    # HTTPS Strict Transport Security
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response

@app.get("/")
def root():
    return FileResponse("frontend/index.html", media_type="text/html")

@app.exception_handler(AppException)
async def app_exception_handler(request:Request,exc:AppException):
    return JSONResponse(
        status_code = exc.status,
        content={
            "code":exc.code,
            "message":exc.message,
            "status":exc.status
        }
    )