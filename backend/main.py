import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
import os
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)

# from pydantic import BaseModel


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )


engine = create_engine("sqlite:///news_database.db", echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from openai import OpenAI


# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

#
# def extract_search_keywords(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content


from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session


JWT_SECRET = '1892dhianiandowqd0n'


class AIUtility:
    """Utility wrapper around OpenAI calls used in this app."""

    def __init__(self, api_key: str = "xxx"):
        self.client = OpenAI(api_key=api_key)

    def evaluate_relevance(self, title: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": title},
        ]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        return response.choices[0].message.content

    def extract_keywords(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
            },
            {"role": "user", "content": prompt},
        ]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        return response.choices[0].message.content

    def summarize_news(self, content: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
            },
            {"role": "user", "content": content},
        ]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        return json.loads(response.choices[0].message.content)


class ScrapingUtility:
    """Utility for HTTP fetching and HTML parsing of news articles."""

    @staticmethod
    def fetch_and_parse_article(url: str):
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.find("h1", class_="article-content__title").text
        time = soup.find("time", class_="article-content__time").text
        content_section = soup.find("section", class_="article-content__editor")
        paragraphs = [
            p.text
            for p in content_section.find_all("p")
            if p.text.strip() != "" and "▪" not in p.text
        ]
        return title, time, paragraphs


class NewsService:
    """Business logic for news retrieval, summarization and persistence."""

    def __init__(self, ai_utility: AIUtility):
        self.ai_utility = ai_utility

    def add_news(self, news_data):
        session = Session()
        session.add(
            NewsArticle(
                url=news_data["url"],
                title=news_data["title"],
                time=news_data["time"],
                content=" ".join(news_data["content"]),
                summary=news_data["summary"],
                reason=news_data["reason"],
            )
        )
        session.commit()
        session.close()

    def get_news_info(self, search_term, is_initial=False):
        all_news_data = []
        if is_initial:
            news_pages = []
            for p in range(1, 10):
                page_params = {
                    "page": p,
                    "id": f"search:{quote(search_term)}",
                    "channelId": 2,
                    "type": "searchword",
                }
                response = requests.get("https://udn.com/api/more", params=page_params)
                news_pages.append(response.json()["lists"])
            for news_list in news_pages:
                all_news_data.append(news_list)
        else:
            page_params = {
                "page": 1,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=page_params)
            all_news_data = response.json()["lists"]
        return all_news_data

    def collect_and_store_news(self, is_initial=False):
        news_data = self.get_news_info("價格", is_initial=is_initial)
        for news in news_data:
            title = news["title"]
            relevance = self.ai_utility.evaluate_relevance(title)
            if relevance == "high":
                title, time, paragraphs = ScrapingUtility.fetch_and_parse_article(
                    news["titleLink"]
                )
                detailed_news = {
                    "url": news["titleLink"],
                    "title": title,
                    "time": time,
                    "content": paragraphs,
                }
                result = self.ai_utility.summarize_news(" ".join(paragraphs))
                detailed_news["summary"] = result["影響"]
                detailed_news["reason"] = result["原因"]
                self.add_news(detailed_news)

    @staticmethod
    def get_article_upvote_details(article_id, user_id, db):
        upvote_count = (
            db.query(user_news_association_table)
            .filter_by(news_articles_id=article_id)
            .count()
        )
        is_upvoted = False
        if user_id:
            is_upvoted = (
                db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first()
                is not None
            )
        return upvote_count, is_upvoted

    @staticmethod
    def toggle_upvote(news_id, user_id, db):
        existing_upvote = db.execute(
            select(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == news_id,
                user_news_association_table.c.user_id == user_id,
            )
        ).scalar()

        if existing_upvote:
            delete_stmt = delete(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == news_id,
                user_news_association_table.c.user_id == user_id,
            )
            db.execute(delete_stmt)
            db.commit()
            return "Upvote removed"
        else:
            insert_stmt = insert(user_news_association_table).values(
                news_articles_id=news_id, user_id=user_id
            )
            db.execute(insert_stmt)
            db.commit()
            return "Article upvoted"

    @staticmethod
    def news_exists(article_id, db: Session):
        return db.query(NewsArticle).filter_by(id=article_id).first() is not None


class AuthService:
    """Authentication and token-related operations."""

    def __init__(self, pwd_context: CryptContext, jwt_secret: str):
        self.pwd_context = pwd_context
        self.jwt_secret = jwt_secret

    def verify_password(self, password, hashed_password):
        return self.pwd_context.verify(password, hashed_password)

    def verify_user_password(self, db, username, password):
        user = db.query(User).filter(User.username == username).first()
        if not self.verify_password(password, user.hashed_password):
            return False
        return user

    def create_access_token(self, data, expires_delta=None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm="HS256")
        return encoded_jwt

    def authenticate_user_token(self, token, db):
        payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        return db.query(User).filter(User.username == payload.get("sub")).first()


class PriceService:
    """Wrapper for price-related external APIs."""

    @staticmethod
    def get_necessities_prices(category=None, commodity=None):
        return requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category, "Name": commodity},
        ).json()


# Instantiate services
ai_utility = AIUtility()
news_service = NewsService(ai_utility)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_service = AuthService(pwd_context=pwd_context, jwt_secret=JWT_SECRET)
price_service = PriceService()


@app.on_event("startup")
def start_scheduler():
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        news_service.collect_and_store_news()
    db.close()
    background_scheduler.add_job(news_service.collect_and_store_news, "interval", minutes=100)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def session_opener():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()



def verify_password(password, hashed_password):
    return auth_service.verify_password(password, hashed_password)


def verify_user_password(db, username, password):
    return auth_service.verify_user_password(db, username, password)


def authenticate_user_token(
    token = Depends(oauth2_scheme),
    db = Depends(session_opener)
):
    return auth_service.authenticate_user_token(token, db)


def create_access_token(data, expires_delta=None):
    """create access token"""
    return auth_service.create_access_token(data, expires_delta)


@app.post("/api/v1/users/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(session_opener)
):
    """login"""
    user = verify_user_password(db, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

class UserAuthSchema(BaseModel):
    username: str
    password: str
@app.post("/api/v1/users/register")
def create_user(user: UserAuthSchema, db: Session = Depends(session_opener)):
    """create user"""
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/api/v1/users/me")
def read_users_me(user=Depends(authenticate_user_token)):
    return {"username": user.username}


_ID_COUNTER = itertools.count(start=1000000)


def get_article_upvote_details(article_id, user_id, db):
    upvote_count = (
        db.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    is_upvoted = False
    if user_id:
        is_upvoted = (
                db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first()
                is not None
        )
    return upvote_count, is_upvoted


@app.get("/api/v1/news/news")
def read_news(db=Depends(session_opener)):
    """
    read new

    :param db:
    :return:
    """
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for n in news:
        upvotes, is_upvoted = news_service.get_article_upvote_details(n.id, None, db)
        result.append(
            {**n.__dict__, "upvotes": upvotes, "is_upvoted": is_upvoted}
        )
    return result


@app.get(
    "/api/v1/news/user_news"
)
def read_user_news(
        db=Depends(session_opener),
        u=Depends(authenticate_user_token)
):
    """
    read user new

    :param db:
    :param u:
    :return:
    """
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, is_upvoted = news_service.get_article_upvote_details(article.id, u.id, db)
        result.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": is_upvoted,
            }
        )
    return result

class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/v1/news/search_news")
async def search_news(request: PromptRequest):
    prompt = request.prompt
    news_list = []
    keywords = ai_utility.extract_keywords(prompt)
    news_items = news_service.get_news_info(keywords, is_initial=False)
    for news in news_items:
        try:
            title, time, paragraphs = ScrapingUtility.fetch_and_parse_article(news["titleLink"])
            detailed_news = {
                "url": news["titleLink"],
                "title": title,
                "time": time,
                "content": paragraphs,
            }
            detailed_news["content"] = " ".join(detailed_news["content"])
            detailed_news["id"] = next(_ID_COUNTER)
            news_list.append(detailed_news)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

class NewsSummaryRequestSchema(BaseModel):
    content: str

@app.post("/api/v1/news/news_summary")
async def news_summary(
        payload: NewsSummaryRequestSchema, user=Depends(authenticate_user_token)
):
    response = {}
    result = ai_utility.summarize_news(f"{payload.content}")
    if result:
        response["summary"] = result.get("影響")
        response["reason"] = result.get("原因")
    return response


@app.post("/api/v1/news/{article_id}/upvote")
def upvote_article(
        article_id: int,
        db=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    message = news_service.toggle_upvote(article_id, user.id, db)
    return {"message": message}


def toggle_upvote(news_id, user_id, db):
    return news_service.toggle_upvote(news_id, user_id, db)


def news_exists(article_id, db: Session):
    return news_service.news_exists(article_id, db)


@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    return price_service.get_necessities_prices(category, commodity)

# Backward-compatible wrappers so prior function names continue to work
def add_news(news_data):
    return news_service.add_news(news_data)

def get_news_info(search_term, is_initial=False):
    return news_service.get_news_info(search_term, is_initial)

def get_news(is_initial=False):
    return news_service.collect_and_store_news(is_initial)
