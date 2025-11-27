"""Base classes for news crawlers."""

import abc
from pydantic import BaseModel, Field, AnyHttpUrl
from tldextract import tldextract
from sqlalchemy.orm import Session

from .exceptions import DomainMismatchException


class Headline(BaseModel):
    """新聞標題（標題和網址）"""

    title: str = Field(
        default=...,
        example="Title of the article",
        description="The title of the article"
    )
    url: AnyHttpUrl | str = Field(
        default=...,
        example="https://www.example.com",
        description="The URL of the article"
    )


class News(Headline):
    """新聞文章（標題、網址、時間、內容）"""

    time: str = Field(
        default=...,
        example="2021-10-01T00:00:00",
        description="The time the article was published"
    )
    content: str = Field(
        default=...,
        example="Content of the article",
        description="The content of the article"
    )


class NewsWithSummary(News):
    """新聞文章（含摘要和原因）"""

    summary: str = Field(
        default=...,
        example="Summary of the article",
        description="The summary of the article"
    )
    reason: str = Field(
        default=...,
        example="Reason of the article",
        description="The reason of the article"
    )


class NewsCrawlerBase(metaclass=abc.ABCMeta):
    """新聞爬蟲基底類別"""

    news_website_url: AnyHttpUrl | str
    news_website_news_child_urls: list[AnyHttpUrl | str]

    @abc.abstractmethod
    def get_headline(
            self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:
        """
        搜尋新聞標題。

        :param search_term: 搜尋關鍵字
        :param page: 頁碼（int）或頁碼範圍（tuple[int, int]）
        :return: 標題列表
        """
        return NotImplemented

    @abc.abstractmethod
    def parse(self, url: AnyHttpUrl | str) -> News:
        """
        解析新聞內容。

        :param url: 新聞文章網址
        :return: 新聞物件（包含標題、網址、時間、內容）
        """
        return NotImplemented

    def validate_and_parse(self, url: AnyHttpUrl | str) -> News:
        """
        驗證網址並解析新聞內容。

        :param url: 新聞文章網址
        :return: 新聞物件
        :raises DomainMismatchException: 網址不屬於允許的網域
        """
        if not self._is_valid_url(url):
            raise DomainMismatchException(url)
        return self.parse(url)

    @staticmethod
    @abc.abstractmethod
    def save(news: News, db: Session | None):
        """
        儲存新聞到資料庫。

        :param news: 新聞物件
        :param db: 資料庫 session
        """
        return NotImplemented

    def _is_valid_url(self, url: AnyHttpUrl | str) -> bool:
        """
        檢查網址是否屬於該新聞網站。

        :param url: 要檢查的網址
        :return: 是否有效
        """
        main_domain = tldextract.extract(self.news_website_url).registered_domain
        url_domain = tldextract.extract(url).registered_domain

        if url_domain == main_domain:
            return True
        return False

