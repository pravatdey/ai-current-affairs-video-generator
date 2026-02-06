"""
RSS Feed Scraper - Scrapes news from RSS feeds
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from email.utils import parsedate_to_datetime

import feedparser
from newspaper import Article as NewspaperArticle

from .base_scraper import BaseScraper, NewsArticle
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RSSScraper(BaseScraper):
    """Scraper for RSS/Atom feeds"""

    def __init__(
        self,
        name: str,
        url: str,
        category: str = "general",
        language: str = "en",
        priority: int = 1,
        max_articles: int = 10,
        fetch_full_content: bool = True,
        **kwargs
    ):
        """
        Initialize RSS scraper.

        Args:
            name: Source name
            url: RSS feed URL
            category: News category
            language: Language code
            priority: Source priority (1 = highest)
            max_articles: Maximum articles to fetch
            fetch_full_content: Whether to fetch full article content
        """
        super().__init__(name, **kwargs)
        self.url = url
        self.category = category
        self.language = language
        self.priority = priority
        self.max_articles = max_articles
        self.fetch_full_content = fetch_full_content

    def scrape(self) -> List[NewsArticle]:
        """
        Scrape articles from RSS feed.

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Scraping RSS feed: {self.name}")
        articles = []

        try:
            # Parse RSS feed
            feed = feedparser.parse(self.url)

            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing issue for {self.name}: {feed.bozo_exception}")

            if not feed.entries:
                logger.warning(f"No entries found in feed: {self.name}")
                return articles

            # Process entries
            for entry in feed.entries[:self.max_articles]:
                article = self._parse_entry(entry)
                if article and self.validate_article(article):
                    articles.append(article)

            logger.info(f"Scraped {len(articles)} articles from {self.name}")

        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")

        return articles

    def _parse_entry(self, entry: Dict[str, Any]) -> Optional[NewsArticle]:
        """
        Parse a single RSS entry into NewsArticle.

        Args:
            entry: feedparser entry dict

        Returns:
            NewsArticle or None if parsing fails
        """
        try:
            # Extract basic info
            title = self.clean_text(entry.get("title", ""))
            url = entry.get("link", "")

            if not title or not url:
                return None

            # Extract summary
            summary = ""
            if "summary" in entry:
                summary = self.clean_text(entry.summary)
            elif "description" in entry:
                summary = self.clean_text(entry.description)

            # Remove HTML tags from summary
            summary = self._strip_html(summary)

            # Extract published date
            published_at = self._parse_date(entry)

            # Extract image URL
            image_url = self._extract_image(entry)

            # Extract author
            author = entry.get("author", "")

            # Create article
            article = NewsArticle(
                title=title,
                url=url,
                source=self.name,
                category=self.category,
                language=self.language,
                summary=summary[:1000] if summary else "",  # Limit summary length
                published_at=published_at,
                image_url=image_url,
                author=author
            )

            # Fetch full content if enabled
            if self.fetch_full_content:
                full_content = self._fetch_full_content(url)
                if full_content:
                    article.content = full_content

            return article

        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None

    def _parse_date(self, entry: Dict[str, Any]) -> Optional[datetime]:
        """Parse publication date from entry"""
        date_fields = ["published", "updated", "created"]

        for field in date_fields:
            if field in entry:
                try:
                    # feedparser provides parsed date tuple
                    parsed_field = f"{field}_parsed"
                    if parsed_field in entry and entry[parsed_field]:
                        from time import mktime
                        return datetime.fromtimestamp(mktime(entry[parsed_field]))
                except Exception:
                    pass

                # Try parsing string
                try:
                    return parsedate_to_datetime(entry[field])
                except Exception:
                    pass

        return None

    def _extract_image(self, entry: Dict[str, Any]) -> str:
        """Extract image URL from entry"""
        # Check media content
        if "media_content" in entry:
            for media in entry.media_content:
                if media.get("type", "").startswith("image/"):
                    return media.get("url", "")

        # Check media thumbnail
        if "media_thumbnail" in entry:
            for thumb in entry.media_thumbnail:
                return thumb.get("url", "")

        # Check enclosures
        if "enclosures" in entry:
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image/"):
                    return enc.get("url", "")

        return ""

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ""

        import re
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)

        # Decode HTML entities
        import html
        text = html.unescape(text)

        return self.clean_text(text)

    def _fetch_full_content(self, url: str) -> str:
        """
        Fetch full article content using newspaper3k.

        Args:
            url: Article URL

        Returns:
            Full article content
        """
        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()

            content = article.text
            if content:
                return self.clean_text(content)

        except Exception as e:
            logger.debug(f"Failed to fetch full content from {url}: {e}")

        return ""
