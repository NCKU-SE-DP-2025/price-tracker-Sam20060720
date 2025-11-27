"""Unit tests for the crawler base classes."""

import unittest
from unittest.mock import MagicMock, patch
from pydantic import AnyHttpUrl

from crawler.crawler_base import NewsCrawlerBase, News, Headline
from crawler.exceptions import DomainMismatchException


class MockNewsCrawler(NewsCrawlerBase):
    """Mock implementation of NewsCrawlerBase for testing."""

    news_website_url = "https://www.example.com"
    news_website_news_child_urls = ["https://news.example.com"]

    def get_headline(self, search_term: str, page: int | tuple[int, int]):
        return [Headline(title="Test Article", url="https://www.example.com/article")]

    def parse(self, url: AnyHttpUrl | str):
        return News(
            title="Test Article",
            url=url,
            time="2023-09-08T00:00:00",
            content="This is the content of the article."
        )

    @staticmethod
    def save(news: News, db=None):
        return True


class TestNewsCrawlerBase(unittest.TestCase):
    """Test cases for NewsCrawlerBase."""

    def setUp(self):
        """Set up test fixtures."""
        self.crawler = MockNewsCrawler()

    def test_is_valid_url_valid(self):
        """Test that valid URLs are correctly identified."""
        valid_url = "https://www.example.com/article"
        self.assertTrue(self.crawler._is_valid_url(valid_url))

    def test_is_valid_url_invalid(self):
        """Test that invalid URLs are correctly identified."""
        invalid_url = "https://www.invalid.com/article"
        self.assertFalse(self.crawler._is_valid_url(invalid_url))

    def test_is_valid_url_child(self):
        """Test that child URLs are correctly identified."""
        valid_child_url = "https://news.example.com/article"
        self.assertTrue(self.crawler._is_valid_url(valid_child_url))

    def test_is_valid_url_raises_domain_mismatch(self):
        """Test that validate_and_parse raises DomainMismatchException for invalid URLs."""
        invalid_url = "https://www.invalid.com/article"

        with self.assertRaises(DomainMismatchException):
            self.crawler.validate_and_parse(invalid_url)

    def test_get_headline(self):
        """Test the get_headline method."""
        headlines = self.crawler.get_headline(search_term="test", page=1)
        self.assertEqual(len(headlines), 1)
        self.assertEqual(headlines[0].title, "Test Article")
        self.assertEqual(headlines[0].url, "https://www.example.com/article")

    def test_parse(self):
        """Test the parse method."""
        news = self.crawler.parse("https://www.example.com/article")
        self.assertEqual(news.title, "Test Article")
        self.assertEqual(news.url, "https://www.example.com/article")
        self.assertEqual(news.time, "2023-09-08T00:00:00")
        self.assertEqual(news.content, "This is the content of the article.")

    @patch('crawler.crawler_base.Session')
    def test_save(self, mock_db_session):
        """Test the save method."""
        news = News(
            title="Test Article",
            url="https://www.example.com/article",
            time="2023-09-08T00:00:00",
            content="This is the content of the article."
        )
        result = self.crawler.save(news, mock_db_session)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()

