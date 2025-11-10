# External imports
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from passlib.context import CryptContext

# Internal imports
from database import SessionLocal
from config import JWT_SECRET
from auth.router import router as auth_router, set_auth_dependencies
from auth.service import AuthService
from news.router import router as news_router, set_news_dependencies
from news.service import NewsService
from news.utils import AIUtility
from price.router import router as price_router, set_price_dependencies
from price.service import PriceService
from news.models import NewsArticle

sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate services
ai_utility = AIUtility()
news_service = NewsService(ai_utility)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_service = AuthService(pwd_context=pwd_context, jwt_secret=JWT_SECRET)
price_service = PriceService()

# Set dependencies
set_auth_dependencies(auth_service, pwd_context)
set_news_dependencies(news_service, ai_utility)
set_price_dependencies(price_service)

# Register routers
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(price_router)


@app.on_event("startup")
def start_scheduler():
    """Initialize news data and start background scheduler"""
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        news_service.collect_and_store_news()
    db.close()
    background_scheduler.add_job(news_service.collect_and_store_news, "interval", minutes=100)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    """Shutdown background scheduler"""
    background_scheduler.shutdown()
