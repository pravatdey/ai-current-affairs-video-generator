"""
Tests for News Scraper Module
"""

import pytest
from datetime import datetime

from src.scraper.base_scraper import NewsArticle
from src.scraper.rss_scraper import RSSScraper
from src.scraper.news_aggregator import NewsAggregator


class TestNewsArticle:
    """Tests for NewsArticle dataclass"""

    def test_article_creation(self):
        """Test creating a news article"""
        article = NewsArticle(
            title="Test Article",
            url="https://example.com/article",
            source="Test Source",
            category="test",
            language="en"
        )

        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.source == "Test Source"

    def test_article_to_dict(self):
        """Test converting article to dictionary"""
        article = NewsArticle(
            title="Test",
            url="https://example.com",
            source="Test",
            summary="Test summary"
        )

        data = article.to_dict()

        assert "title" in data
        assert "url" in data
        assert "summary" in data
        assert data["title"] == "Test"


class TestRSSScraper:
    """Tests for RSS Scraper"""

    def test_scraper_initialization(self):
        """Test scraper initialization"""
        scraper = RSSScraper(
            name="Test Feed",
            url="https://example.com/feed.xml",
            category="test"
        )

        assert scraper.name == "Test Feed"
        assert scraper.category == "test"

    def test_clean_text(self):
        """Test text cleaning"""
        scraper = RSSScraper(
            name="Test",
            url="https://example.com"
        )

        # Test whitespace normalization
        text = "  Multiple   spaces   here  "
        cleaned = scraper.clean_text(text)
        assert cleaned == "Multiple spaces here"


class TestNewsAggregator:
    """Tests for News Aggregator"""

    def test_aggregator_initialization(self):
        """Test aggregator initialization"""
        # This will use default config
        aggregator = NewsAggregator()

        assert aggregator is not None
        assert len(aggregator.scrapers) >= 0

    def test_get_statistics(self):
        """Test getting statistics"""
        aggregator = NewsAggregator()
        stats = aggregator.get_statistics()

        assert "total_scrapers" in stats
        assert "total_articles" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
