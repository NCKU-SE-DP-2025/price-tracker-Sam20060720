# External imports
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import itertools

# Internal imports
from database import get_db
from auth.dependencies import get_current_user
from news.models import NewsArticle
from news.service import NewsService
from news.schemas import PromptRequest, NewsSummaryRequestSchema
from news.utils import ScrapingUtility

router = APIRouter(prefix="/api/v1/news", tags=["news"])

# Global variables
_news_service: NewsService = None
_ai_utility = None
_ID_COUNTER = itertools.count(start=1000000)


def set_news_dependencies(news_service: NewsService, ai_utility):
    """Set news service and ai utility (called from main.py)"""
    global _news_service, _ai_utility
    _news_service = news_service
    _ai_utility = ai_utility


@router.get("/news")
def read_news(db: Session = Depends(get_db)):
    """Get all news articles"""
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for n in news:
        upvotes, is_upvoted = _news_service.get_article_upvote_details(n.id, None, db)
        result.append(
            {**n.__dict__, "upvotes": upvotes, "is_upvoted": is_upvoted}
        )
    return result


@router.get("/user_news")
def read_user_news(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Get news articles with user upvote status"""
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, is_upvoted = _news_service.get_article_upvote_details(article.id, user.id, db)
        result.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": is_upvoted,
            }
        )
    return result


@router.post("/search_news")
async def search_news(request: PromptRequest):
    """Search news by prompt"""
    prompt = request.prompt
    news_list = []
    keywords = _ai_utility.extract_keywords(prompt)
    news_items = _news_service.get_news_info(keywords, is_initial=False)
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


@router.post("/news_summary")
async def news_summary(
    payload: NewsSummaryRequestSchema,
    user=Depends(get_current_user)
):
    """Generate news summary"""
    response = {}
    result = _ai_utility.summarize_news(f"{payload.content}")
    if result:
        response["summary"] = result.get("影響")
        response["reason"] = result.get("原因")
    return response


@router.post("/{article_id}/upvote")
def upvote_article(
    article_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Toggle upvote for article"""
    message = _news_service.toggle_upvote(article_id, user.id, db)
    return {"message": message}

