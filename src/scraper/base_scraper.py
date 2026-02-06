"""
Base scraper class - Abstract interface for all scrapers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import random
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NewsArticle:
    """Data class representing a news article"""
    title: str
    url: str
    source: str
    category: str = ""
    language: str = "en"
    summary: str = ""
    content: str = ""
    published_at: Optional[datetime] = None
    image_url: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "language": self.language,
            "summary": self.summary,
            "content": self.content,
            "published_at": self.published_at,
        }


class BaseScraper(ABC):
    """Abstract base class for all news scrapers"""

    # Default user agents for rotation
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(
        self,
        name: str,
        timeout: int = 30,
        max_retries: int = 3,
        request_delay: float = 1.0,
        user_agents: List[str] = None
    ):
        """
        Initialize base scraper.

        Args:
            name: Scraper name for logging
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            request_delay: Delay between requests in seconds
            user_agents: List of user agents for rotation
        """
        self.name = name
        self.timeout = timeout
        self.max_retries = max_retries
        self.request_delay = request_delay
        self.user_agents = user_agents or self.DEFAULT_USER_AGENTS

        # Create session with retry logic
        self.session = self._create_session()

        logger.info(f"Initialized scraper: {name}")

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from URL with error handling.

        Args:
            url: URL to fetch

        Returns:
            Response content as string, or None if failed
        """
        try:
            # Add delay to be nice to servers
            time.sleep(self.request_delay)

            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.debug(f"Successfully fetched: {url[:50]}...")
            return response.text

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    @abstractmethod
    def scrape(self) -> List[NewsArticle]:
        """
        Scrape news articles from the source.

        Returns:
            List of NewsArticle objects
        """
        pass

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""

        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def validate_article(self, article: NewsArticle, min_content_length: int = 100) -> bool:
        """
        Validate if article meets minimum requirements.

        Args:
            article: NewsArticle to validate
            min_content_length: Minimum content length

        Returns:
            True if valid, False otherwise
        """
        if not article.title or len(article.title) < 10:
            return False

        if not article.url:
            return False

        # Check if content or summary exists with minimum length
        content_length = len(article.content) if article.content else 0
        summary_length = len(article.summary) if article.summary else 0

        if content_length < min_content_length and summary_length < min_content_length:
            return False

        return True
