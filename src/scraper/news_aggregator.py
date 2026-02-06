"""
News Aggregator - Combines and manages multiple news sources
"""

import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

import yaml

from .base_scraper import NewsArticle
from .rss_scraper import RSSScraper
from .web_scraper import WebScraper
from src.utils.logger import get_logger
from src.utils.database import Database

logger = get_logger(__name__)


class NewsAggregator:
    """
    Aggregates news from multiple sources, handles deduplication,
    and manages the news pipeline.
    """

    def __init__(
        self,
        sources_config_path: str = "config/news_sources.yaml",
        database: Database = None,
        similarity_threshold: float = 0.8
    ):
        """
        Initialize news aggregator.

        Args:
            sources_config_path: Path to news sources configuration
            database: Database instance for tracking
            similarity_threshold: Threshold for duplicate detection (0-1)
        """
        self.sources_config_path = sources_config_path
        self.db = database or Database()
        self.similarity_threshold = similarity_threshold

        # Load configuration
        self.config = self._load_config()

        # Initialize scrapers
        self.scrapers = self._init_scrapers()

        logger.info(f"Initialized NewsAggregator with {len(self.scrapers)} scrapers")

    def _load_config(self) -> Dict[str, Any]:
        """Load news sources configuration"""
        config_path = Path(self.sources_config_path)

        if not config_path.exists():
            logger.error(f"Config file not found: {self.sources_config_path}")
            return {}

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _init_scrapers(self) -> List:
        """Initialize all scrapers from configuration"""
        scrapers = []

        # Get all source lists
        source_lists = [
            self.config.get("indian_sources", []),
            self.config.get("international_sources", []),
            self.config.get("category_sources", [])
        ]

        # Create scrapers for each source
        for sources in source_lists:
            for source in sources:
                if not source.get("enabled", True):
                    continue

                scraper = self._create_scraper(source)
                if scraper:
                    scrapers.append(scraper)

        return scrapers

    def _create_scraper(self, source: Dict[str, Any]):
        """Create appropriate scraper based on source type"""
        source_type = source.get("type", "rss")
        name = source.get("name", "Unknown")

        try:
            if source_type == "rss":
                return RSSScraper(
                    name=name,
                    url=source.get("url", ""),
                    category=source.get("category", "general"),
                    language=source.get("language", "en"),
                    priority=source.get("priority", 1),
                    max_articles=self.config.get("rules", {}).get("max_articles_per_source", 10)
                )

            elif source_type == "web":
                return WebScraper(
                    name=name,
                    url=source.get("url", ""),
                    selectors=source.get("selectors", {}),
                    category=source.get("category", "general"),
                    language=source.get("language", "en"),
                    priority=source.get("priority", 1),
                    max_articles=self.config.get("rules", {}).get("max_articles_per_source", 10)
                )

        except Exception as e:
            logger.error(f"Failed to create scraper for {name}: {e}")

        return None

    def scrape_all(self) -> List[NewsArticle]:
        """
        Scrape all configured news sources.

        Returns:
            List of deduplicated NewsArticle objects
        """
        all_articles = []
        stats = {
            "total_found": 0,
            "duplicates_removed": 0,
            "sources_succeeded": 0,
            "sources_failed": 0
        }

        logger.info(f"Starting scrape of {len(self.scrapers)} sources")

        for scraper in self.scrapers:
            try:
                articles = scraper.scrape()
                stats["total_found"] += len(articles)
                stats["sources_succeeded"] += 1

                # Add to collection
                all_articles.extend(articles)

                # Log scraping result
                self.db.log_scraping(
                    source=scraper.name,
                    articles_found=len(articles),
                    status="completed"
                )

            except Exception as e:
                stats["sources_failed"] += 1
                logger.error(f"Scraper {scraper.name} failed: {e}")

                self.db.log_scraping(
                    source=scraper.name,
                    status="failed",
                    errors=str(e)
                )

        # Deduplicate articles
        unique_articles = self._deduplicate(all_articles)
        stats["duplicates_removed"] = len(all_articles) - len(unique_articles)

        # Save to database
        saved_count = self._save_to_database(unique_articles)

        logger.info(
            f"Scraping complete: {stats['total_found']} found, "
            f"{stats['duplicates_removed']} duplicates, "
            f"{saved_count} saved to database"
        )

        return unique_articles

    def scrape_source(self, source_name: str) -> List[NewsArticle]:
        """
        Scrape a specific source by name.

        Args:
            source_name: Name of the source to scrape

        Returns:
            List of NewsArticle objects
        """
        for scraper in self.scrapers:
            if scraper.name.lower() == source_name.lower():
                articles = scraper.scrape()
                self._save_to_database(articles)
                return articles

        logger.warning(f"Source not found: {source_name}")
        return []

    def _deduplicate(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Remove duplicate articles based on URL and title similarity.

        Args:
            articles: List of articles to deduplicate

        Returns:
            Deduplicated list of articles
        """
        unique = []
        seen_urls = set()
        seen_titles = []

        for article in articles:
            # Check URL duplicate
            url_hash = hashlib.md5(article.url.encode()).hexdigest()
            if url_hash in seen_urls:
                continue

            # Check title similarity
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = SequenceMatcher(
                    None,
                    article.title.lower(),
                    seen_title.lower()
                ).ratio()

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(article)
                seen_urls.add(url_hash)
                seen_titles.append(article.title)

        return unique

    def _save_to_database(self, articles: List[NewsArticle]) -> int:
        """
        Save articles to database.

        Args:
            articles: List of articles to save

        Returns:
            Number of articles saved
        """
        saved_count = 0

        for article in articles:
            # Check if already exists
            if not self.db.article_exists(article.url):
                result = self.db.add_article(article.to_dict())
                if result:
                    saved_count += 1

        return saved_count

    def get_articles_for_video(
        self,
        language: str = "en",
        max_articles: int = 10,
        categories: List[str] = None,
        max_age_hours: int = 48
    ) -> List[NewsArticle]:
        """
        Get articles suitable for video generation.

        Args:
            language: Language filter
            max_articles: Maximum number of articles
            categories: List of categories to include
            max_age_hours: Maximum article age

        Returns:
            List of NewsArticle objects
        """
        # Get from database
        db_articles = self.db.get_unused_articles(
            language=language,
            limit=max_articles * 2,  # Get more for filtering
            max_age_hours=max_age_hours
        )

        articles = []

        # Convert and filter
        for db_article in db_articles:
            if categories and db_article.category not in categories:
                continue

            article = NewsArticle(
                title=db_article.title,
                url=db_article.url,
                source=db_article.source,
                category=db_article.category,
                language=db_article.language,
                summary=db_article.summary,
                content=db_article.content,
                published_at=db_article.published_at
            )
            articles.append(article)

            if len(articles) >= max_articles:
                break

        # Sort by category weights from config
        category_weights = self.config.get("categories", {})
        articles.sort(
            key=lambda a: category_weights.get(a.category, {}).get("weight", 0.5),
            reverse=True
        )

        logger.info(f"Retrieved {len(articles)} articles for video generation")
        return articles

    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        return {
            "total_scrapers": len(self.scrapers),
            "active_scrapers": len([s for s in self.scrapers if s]),
            **self.db.get_statistics()
        }


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="News Aggregator CLI")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--source", type=str, help="Scrape specific source")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    # Initialize aggregator
    aggregator = NewsAggregator()

    if args.stats:
        stats = aggregator.get_statistics()
        print("\n=== News Aggregator Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

    elif args.source:
        articles = aggregator.scrape_source(args.source)
        print(f"\nScraped {len(articles)} articles from {args.source}")
        for article in articles[:5]:
            print(f"  - {article.title[:60]}...")

    elif args.test:
        print("\n=== Running Test Scrape ===")
        articles = aggregator.scrape_all()
        print(f"\nTotal articles scraped: {len(articles)}")
        print("\nSample articles:")
        for article in articles[:10]:
            print(f"  [{article.source}] {article.title[:50]}...")

    else:
        parser.print_help()
