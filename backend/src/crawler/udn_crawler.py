"""UDN (United Daily News) crawler implementation."""

from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl
from sqlalchemy.orm import Session

from .crawler_base import NewsCrawlerBase, Headline, News
from news.models import NewsArticle


class UDNCrawler(NewsCrawlerBase):
    """UDN 新聞爬蟲"""

    news_website_url = "https://udn.com"
    news_website_news_child_urls = ["https://udn.com"]

    def get_headline(
        self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:
        """
        搜尋 UDN 新聞標題。

        :param search_term: 搜尋關鍵字
        :param page: 頁碼或頁碼範圍
        :return: 標題列表
        """
        headlines = []
        
        if isinstance(page, tuple):
            start_page, end_page = page
            page_range = range(start_page, end_page + 1)
        else:
            page_range = [page]

        for p in page_range:
            page_params = {
                "page": p,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=page_params)
            news_list = response.json()["lists"]
            
            for news_item in news_list:
                headlines.append(
                    Headline(
                        title=news_item["title"],
                        url=news_item["titleLink"]
                    )
                )

        return headlines

    def parse(self, url: AnyHttpUrl | str) -> News:
        """
        解析 UDN 新聞內容。

        :param url: 新聞網址
        :return: 新聞物件
        """
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
        content = " ".join(paragraphs)

        return News(
            title=title,
            url=url,
            time=time,
            content=content
        )

    @staticmethod
    def save(news: News, db: Session | None):
        """
        儲存新聞到資料庫。

        :param news: 新聞物件
        :param db: 資料庫 session
        """
        if db is None:
            return

        # 檢查是否已存在
        existing_news = db.query(NewsArticle).filter_by(url=str(news.url)).first()
        if existing_news:
            return

        # 建立新文章
        news_article = NewsArticle(
            url=str(news.url),
            title=news.title,
            time=news.time,
            content=news.content,
            summary="",
            reason=""
        )
        db.add(news_article)
        db.commit()

