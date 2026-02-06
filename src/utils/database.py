"""
Database utilities for tracking scraped articles and generated videos
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .logger import get_logger

logger = get_logger(__name__)
Base = declarative_base()


class Article(Base):
    """Model for storing scraped news articles"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    hash_id = Column(String(64), unique=True, nullable=False)  # SHA256 of URL
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    source = Column(String(100), nullable=False)
    category = Column(String(50))
    language = Column(String(10), default="en")
    summary = Column(Text)
    content = Column(Text)
    published_at = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_used = Column(Boolean, default=False)
    used_in_video = Column(String(100))  # Video ID if used


class GeneratedVideo(Base):
    """Model for tracking generated videos"""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    video_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(500))
    language = Column(String(10))
    duration = Column(Float)
    article_count = Column(Integer)
    article_ids = Column(Text)  # Comma-separated article IDs
    script_path = Column(String(500))
    audio_path = Column(String(500))
    video_path = Column(String(500))
    thumbnail_path = Column(String(500))
    youtube_id = Column(String(50))
    youtube_url = Column(String(200))
    upload_status = Column(String(20), default="pending")  # pending, uploaded, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime)


class ScrapingLog(Base):
    """Model for tracking scraping runs"""
    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True)
    source = Column(String(100))
    articles_found = Column(Integer, default=0)
    articles_new = Column(Integer, default=0)
    articles_duplicate = Column(Integer, default=0)
    errors = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20), default="running")  # running, completed, failed


class Database:
    """Database manager for the application"""

    def __init__(self, db_path: str = "data/news_tracker.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Create engine and session
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at: {db_path}")

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    @staticmethod
    def generate_hash(url: str) -> str:
        """Generate SHA256 hash of URL for deduplication"""
        return hashlib.sha256(url.encode()).hexdigest()

    def article_exists(self, url: str) -> bool:
        """Check if article already exists in database"""
        hash_id = self.generate_hash(url)
        with self.get_session() as session:
            exists = session.query(Article).filter_by(hash_id=hash_id).first() is not None
        return exists

    def add_article(self, article_data: Dict[str, Any]) -> Optional[Article]:
        """
        Add a new article to the database.

        Args:
            article_data: Dictionary with article fields

        Returns:
            Article object if added, None if duplicate
        """
        url = article_data.get("url", "")
        hash_id = self.generate_hash(url)

        with self.get_session() as session:
            # Check for duplicate
            if session.query(Article).filter_by(hash_id=hash_id).first():
                logger.debug(f"Duplicate article skipped: {url[:50]}...")
                return None

            # Create new article
            article = Article(
                hash_id=hash_id,
                title=article_data.get("title", ""),
                url=url,
                source=article_data.get("source", ""),
                category=article_data.get("category", ""),
                language=article_data.get("language", "en"),
                summary=article_data.get("summary", ""),
                content=article_data.get("content", ""),
                published_at=article_data.get("published_at")
            )

            session.add(article)
            session.commit()
            session.refresh(article)

            logger.debug(f"Article added: {article.title[:50]}...")
            return article

    def get_unused_articles(
        self,
        language: str = None,
        category: str = None,
        limit: int = 20,
        max_age_hours: int = 48
    ) -> List[Article]:
        """
        Get articles that haven't been used in videos yet.

        Args:
            language: Filter by language
            category: Filter by category
            limit: Maximum number of articles
            max_age_hours: Maximum age of articles in hours

        Returns:
            List of Article objects
        """
        from datetime import timedelta

        with self.get_session() as session:
            query = session.query(Article).filter(
                Article.is_used == False,
                Article.scraped_at >= datetime.utcnow() - timedelta(hours=max_age_hours)
            )

            if language:
                query = query.filter(Article.language == language)

            if category:
                query = query.filter(Article.category == category)

            articles = query.order_by(Article.published_at.desc()).limit(limit).all()

            # Detach from session to use outside
            return [self._detach_article(a) for a in articles]

    def _detach_article(self, article: Article) -> Article:
        """Create a detached copy of article"""
        return Article(
            id=article.id,
            hash_id=article.hash_id,
            title=article.title,
            url=article.url,
            source=article.source,
            category=article.category,
            language=article.language,
            summary=article.summary,
            content=article.content,
            published_at=article.published_at,
            scraped_at=article.scraped_at,
            is_used=article.is_used,
            used_in_video=article.used_in_video
        )

    def mark_articles_used(self, article_ids: List[int], video_id: str) -> None:
        """Mark articles as used in a video"""
        with self.get_session() as session:
            session.query(Article).filter(
                Article.id.in_(article_ids)
            ).update(
                {Article.is_used: True, Article.used_in_video: video_id},
                synchronize_session=False
            )
            session.commit()
            logger.info(f"Marked {len(article_ids)} articles as used in video: {video_id}")

    def add_video(self, video_data: Dict[str, Any]) -> GeneratedVideo:
        """Add a new video record"""
        with self.get_session() as session:
            video = GeneratedVideo(**video_data)
            session.add(video)
            session.commit()
            session.refresh(video)
            logger.info(f"Video record added: {video.video_id}")
            return video

    def update_video_status(
        self,
        video_id: str,
        status: str,
        youtube_id: str = None,
        youtube_url: str = None
    ) -> None:
        """Update video upload status"""
        with self.get_session() as session:
            video = session.query(GeneratedVideo).filter_by(video_id=video_id).first()
            if video:
                video.upload_status = status
                if youtube_id:
                    video.youtube_id = youtube_id
                if youtube_url:
                    video.youtube_url = youtube_url
                if status == "uploaded":
                    video.uploaded_at = datetime.utcnow()
                session.commit()
                logger.info(f"Video {video_id} status updated to: {status}")

    def log_scraping(
        self,
        source: str,
        articles_found: int = 0,
        articles_new: int = 0,
        articles_duplicate: int = 0,
        status: str = "completed",
        errors: str = None
    ) -> None:
        """Log a scraping run"""
        with self.get_session() as session:
            log = ScrapingLog(
                source=source,
                articles_found=articles_found,
                articles_new=articles_new,
                articles_duplicate=articles_duplicate,
                status=status,
                errors=errors,
                completed_at=datetime.utcnow() if status != "running" else None
            )
            session.add(log)
            session.commit()

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_session() as session:
            total_articles = session.query(Article).count()
            used_articles = session.query(Article).filter_by(is_used=True).count()
            total_videos = session.query(GeneratedVideo).count()
            uploaded_videos = session.query(GeneratedVideo).filter_by(upload_status="uploaded").count()

            return {
                "total_articles": total_articles,
                "used_articles": used_articles,
                "unused_articles": total_articles - used_articles,
                "total_videos": total_videos,
                "uploaded_videos": uploaded_videos,
                "pending_videos": total_videos - uploaded_videos
            }
