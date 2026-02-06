"""
Web Scraper - Scrapes news from web pages using BeautifulSoup
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from newspaper import Article as NewspaperArticle

from .base_scraper import BaseScraper, NewsArticle
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WebScraper(BaseScraper):
    """Scraper for web pages using CSS selectors"""

    def __init__(
        self,
        name: str,
        url: str,
        selectors: Dict[str, str],
        category: str = "general",
        language: str = "en",
        priority: int = 1,
        max_articles: int = 10,
        fetch_full_content: bool = True,
        **kwargs
    ):
        """
        Initialize web scraper.

        Args:
            name: Source name
            url: Page URL to scrape
            selectors: CSS selectors for extracting data
                - articles: Selector for article containers
                - title: Selector for article title
                - link: Selector for article link
                - date: Selector for publication date (optional)
                - summary: Selector for summary (optional)
            category: News category
            language: Language code
            priority: Source priority
            max_articles: Maximum articles to fetch
            fetch_full_content: Whether to fetch full article content
        """
        super().__init__(name, **kwargs)
        self.url = url
        self.selectors = selectors
        self.category = category
        self.language = language
        self.priority = priority
        self.max_articles = max_articles
        self.fetch_full_content = fetch_full_content

        # Extract base URL for resolving relative links
        parsed = urlparse(url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"

    def scrape(self) -> List[NewsArticle]:
        """
        Scrape articles from web page.

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Scraping web page: {self.name}")
        articles = []

        try:
            # Fetch page content
            html_content = self.fetch_url(self.url)
            if not html_content:
                return articles

            # Parse HTML
            soup = BeautifulSoup(html_content, "lxml")

            # Find article containers
            article_selector = self.selectors.get("articles", "article")
            article_elements = soup.select(article_selector)

            if not article_elements:
                logger.warning(f"No articles found with selector '{article_selector}' on {self.name}")
                return articles

            # Process each article
            for element in article_elements[:self.max_articles]:
                article = self._parse_article(element)
                if article and self.validate_article(article):
                    articles.append(article)

            logger.info(f"Scraped {len(articles)} articles from {self.name}")

        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")

        return articles

    def _parse_article(self, element: BeautifulSoup) -> Optional[NewsArticle]:
        """
        Parse a single article element.

        Args:
            element: BeautifulSoup element containing article

        Returns:
            NewsArticle or None if parsing fails
        """
        try:
            # Extract title
            title = self._extract_text(element, self.selectors.get("title", "h2"))
            if not title:
                return None

            # Extract link
            link = self._extract_link(element, self.selectors.get("link", "a"))
            if not link:
                return None

            # Resolve relative URLs
            link = urljoin(self.base_url, link)

            # Extract summary
            summary = self._extract_text(element, self.selectors.get("summary", ".summary, .excerpt, p"))

            # Extract date
            date_text = self._extract_text(element, self.selectors.get("date", ".date, time"))
            published_at = self._parse_date(date_text) if date_text else None

            # Extract image
            image_url = self._extract_image(element)

            # Create article
            article = NewsArticle(
                title=title,
                url=link,
                source=self.name,
                category=self.category,
                language=self.language,
                summary=summary[:1000] if summary else "",
                published_at=published_at,
                image_url=image_url
            )

            # Fetch full content if enabled
            if self.fetch_full_content:
                full_content = self._fetch_full_content(link)
                if full_content:
                    article.content = full_content

            return article

        except Exception as e:
            logger.debug(f"Error parsing article element: {e}")
            return None

    def _extract_text(self, element: BeautifulSoup, selector: str) -> str:
        """Extract text content using CSS selector"""
        if not selector:
            return ""

        # Try multiple selectors separated by comma
        for sel in selector.split(","):
            sel = sel.strip()
            found = element.select_one(sel)
            if found:
                return self.clean_text(found.get_text())

        return ""

    def _extract_link(self, element: BeautifulSoup, selector: str) -> str:
        """Extract link URL using CSS selector"""
        if not selector:
            return ""

        # Try multiple selectors
        for sel in selector.split(","):
            sel = sel.strip()
            found = element.select_one(sel)
            if found:
                # Get href attribute
                href = found.get("href", "")
                if href:
                    return href

        return ""

    def _extract_image(self, element: BeautifulSoup) -> str:
        """Extract image URL from element"""
        # Try img tag
        img = element.select_one("img")
        if img:
            # Try different attributes
            for attr in ["src", "data-src", "data-lazy-src"]:
                src = img.get(attr, "")
                if src:
                    return urljoin(self.base_url, src)

        # Try figure/picture elements
        for tag in ["figure img", "picture source", "picture img"]:
            found = element.select_one(tag)
            if found:
                src = found.get("src", "") or found.get("srcset", "").split(",")[0].split()[0]
                if src:
                    return urljoin(self.base_url, src)

        return ""

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from text"""
        if not date_text:
            return None

        from dateutil import parser

        try:
            return parser.parse(date_text, fuzzy=True)
        except Exception:
            pass

        return None

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
