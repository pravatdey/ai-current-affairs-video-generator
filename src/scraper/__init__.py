"""News Scraper Module - Scrapes news from multiple sources"""

from .base_scraper import BaseScraper
from .rss_scraper import RSSScraper
from .web_scraper import WebScraper
from .news_aggregator import NewsAggregator

__all__ = ["BaseScraper", "RSSScraper", "WebScraper", "NewsAggregator"]
