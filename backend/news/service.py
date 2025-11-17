# External imports
from urllib.parse import quote
import requests
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

# Internal imports
from news.models import NewsArticle
from database import user_news_association_table, SessionLocal
from news.utils import AIUtility, ScrapingUtility


class NewsService:
    """Business logic for news retrieval, summarization and persistence."""

    def __init__(self, ai_utility: AIUtility):
        self.ai_utility = ai_utility

    def add_news(self, news_data):
        session = SessionLocal()
        try:
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
        finally:
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
