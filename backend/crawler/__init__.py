"""Crawler module for news websites."""

from .crawler_base import NewsCrawlerBase, Headline, News, NewsWithSummary
from .exceptions import DomainMismatchException

# 延遲導入 UDNCrawler 以避免循環導入
def _get_udn_crawler():
    from .udn_crawler import UDNCrawler
    return UDNCrawler

__all__ = [
    "NewsCrawlerBase",
    "Headline",
    "News",
    "NewsWithSummary",
    "DomainMismatchException",
    "UDNCrawler",
]

# 延遲導入，只有在需要時才導入
def __getattr__(name):
    if name == "UDNCrawler":
        return _get_udn_crawler()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

