"""
AI Current Affairs Video Generator - Main Pipeline

This is the main entry point for the video generation pipeline.
It orchestrates all components to:
1. Scrape news from multiple sources
2. Generate video scripts using LLM
3. Convert scripts to speech
4. Create avatar videos
5. Compose final video with effects
6. Generate thumbnails
7. Upload to YouTube
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger, get_logger
from src.utils.database import Database
from src.scraper import NewsAggregator
from src.script_generator import ScriptWriter
from src.tts import TTSManager
from src.avatar import AvatarGenerator
from src.video import VideoComposer, ThumbnailGenerator
from src.youtube import YouTubeUploader


class VideoGenerationPipeline:
    """
    Main pipeline for generating current affairs videos.

    Pipeline steps:
    1. Scrape news articles
    2. Generate video script
    3. Generate audio (TTS)
    4. Generate avatar video
    5. Compose final video
    6. Generate thumbnail
    7. Upload to YouTube (optional)
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize the pipeline.

        Args:
            config_path: Path to main configuration file
        """
        self.config = self._load_config(config_path)

        # Setup logging
        log_config = self.config.get("app", {})
        setup_logger(
            log_level=log_config.get("log_level", "INFO"),
            log_file="logs/pipeline.log"
        )
        self.logger = get_logger("Pipeline")

        # Initialize components
        self.db = Database(self.config.get("database", {}).get("path", "data/news_tracker.db"))
        self.scraper = NewsAggregator(database=self.db)
        self.script_writer = ScriptWriter(
            llm_provider=self.config.get("llm", {}).get("provider", "groq"),
            target_duration_minutes=self.config.get("video", {}).get("duration_max", 10)
        )
        self.tts_manager = TTSManager()
        self.avatar_generator = AvatarGenerator()
        self.video_composer = VideoComposer()
        self.thumbnail_generator = ThumbnailGenerator()
        self.youtube_uploader = YouTubeUploader()

        # Paths
        self.output_dir = Path(self.config.get("paths", {}).get("output", "output"))
        self.audio_dir = Path(self.config.get("paths", {}).get("audio", "output/audio"))
        self.video_dir = Path(self.config.get("paths", {}).get("videos", "output/videos"))
        self.thumbnail_dir = Path(self.config.get("paths", {}).get("thumbnails", "output/thumbnails"))

        # Ensure directories exist
        for dir_path in [self.output_dir, self.audio_dir, self.video_dir, self.thumbnail_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.logger.info("Pipeline initialized successfully")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            return {}

    async def run(
        self,
        language: str = "en",
        upload: bool = True,
        test_mode: bool = False,
        scrape_fresh: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete video generation pipeline.

        Args:
            language: Video language code
            upload: Whether to upload to YouTube
            test_mode: If True, uploads as private video
            scrape_fresh: Whether to scrape fresh news

        Returns:
            Dictionary with pipeline results
        """
        video_id = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.logger.info(f"Starting pipeline: {video_id}")

        results = {
            "video_id": video_id,
            "success": False,
            "steps": {},
            "errors": []
        }

        # Will be set after video composition if PDF notes are generated
        pdf_notes_path = None

        try:
            # Step 1: Scrape news
            self.logger.info("Step 1: Scraping news...")
            if scrape_fresh:
                articles = self.scraper.scrape_all()
            else:
                articles = []

            # Get articles for video (4 articles for 15-min video)
            video_articles = self.scraper.get_articles_for_video(
                language=language,
                max_articles=4
            )

            if not video_articles:
                results["errors"].append("No articles available for video")
                self.logger.error("No articles found")
                return results

            results["steps"]["scraping"] = {
                "scraped": len(articles) if scrape_fresh else 0,
                "selected": len(video_articles)
            }
            self.logger.info(f"Selected {len(video_articles)} articles for video")

            # Step 2: Generate script
            self.logger.info("Step 2: Generating script...")
            script = self.script_writer.generate_script(
                articles=video_articles,
                language=self._get_language_name(language),
                date=datetime.now().strftime("%B %d, %Y")
            )

            script_path = self.output_dir / f"{video_id}_script.txt"
            self.script_writer.save_script(script, str(script_path))

            results["steps"]["script"] = {
                "word_count": script.word_count,
                "duration_estimate": script.total_duration,
                "path": str(script_path)
            }
            self.logger.info(f"Script generated: {script.word_count} words")

            # Step 3: Generate audio (TTS)
            self.logger.info("Step 3: Generating audio...")
            audio_path = self.audio_dir / f"{video_id}_audio.mp3"

            tts_result = await self.tts_manager.generate_audio(
                text=script.get_script_for_tts(),
                output_path=str(audio_path),
                language=language
            )

            if not tts_result.success:
                results["errors"].append(f"TTS failed: {tts_result.error}")
                self.logger.error(f"TTS failed: {tts_result.error}")
                return results

            results["steps"]["audio"] = {
                "duration": tts_result.duration,
                "path": str(audio_path),
                "voice": tts_result.voice.id
            }
            self.logger.info(f"Audio generated: {tts_result.duration:.1f}s")

            # Step 4: Generate avatar video
            self.logger.info("Step 4: Generating avatar video...")
            avatar_path = self.video_dir / f"{video_id}_avatar.mp4"

            avatar_result = self.avatar_generator.generate(
                audio_path=str(audio_path),
                output_path=str(avatar_path)
            )

            if not avatar_result.success:
                results["errors"].append(f"Avatar generation failed: {avatar_result.error}")
                self.logger.error(f"Avatar failed: {avatar_result.error}")
                return results

            results["steps"]["avatar"] = {
                "duration": avatar_result.duration,
                "path": str(avatar_path),
                "method": avatar_result.method
            }
            self.logger.info(f"Avatar video generated: {avatar_result.method}")

            # Step 5: Compose final video
            self.logger.info("Step 5: Composing final video...")
            final_video_path = self.video_dir / f"{video_id}_final.mp4"

            headlines = [a.title for a in video_articles]

            composition_result = self.video_composer.compose(
                avatar_video_path=str(avatar_path),
                output_path=str(final_video_path),
                headlines=headlines,
                title=script.title,
                date=script.date
            )

            if not composition_result.success:
                results["errors"].append(f"Video composition failed: {composition_result.error}")
                self.logger.error(f"Composition failed: {composition_result.error}")
                return results

            results["steps"]["composition"] = {
                "duration": composition_result.duration,
                "path": str(final_video_path),
                "resolution": composition_result.resolution,
                "pdf_notes": composition_result.pdf_notes_path or ""
            }
            self.logger.info(f"Video composed: {composition_result.duration:.1f}s")

            # Track PDF path for upload step
            pdf_notes_path = composition_result.pdf_notes_path
            if pdf_notes_path:
                self.logger.info(f"PDF study notes generated: {pdf_notes_path}")

            # Step 6: Generate thumbnail
            self.logger.info("Step 6: Generating thumbnail...")
            thumbnail_path = self.thumbnail_dir / f"{video_id}_thumbnail.png"

            thumbnail_result = self.thumbnail_generator.generate_from_headlines(
                output_path=str(thumbnail_path),
                headlines=headlines,
                date=script.date
            )

            results["steps"]["thumbnail"] = {
                "success": thumbnail_result.success,
                "path": str(thumbnail_path) if thumbnail_result.success else ""
            }

            # Step 7: Upload to YouTube (if enabled)
            if upload:
                self.logger.info("Step 7: Uploading to YouTube (with PDF study notes)...")
                sources = list(set([a.source for a in video_articles]))

                upload_result = self.youtube_uploader.upload_with_metadata(
                    video_path=str(final_video_path),
                    headlines=headlines,
                    sources=sources,
                    language=language,
                    date=script.date,
                    thumbnail_path=str(thumbnail_path) if thumbnail_result.success else None,
                    privacy_status="private" if test_mode else "public",
                    pdf_path=pdf_notes_path
                )

                results["steps"]["upload"] = {
                    "success": upload_result.success,
                    "video_id": upload_result.video_id,
                    "url": upload_result.video_url,
                    "pdf_notes": pdf_notes_path or "",
                    "error": upload_result.error
                }

                if upload_result.success:
                    self.logger.info(f"Uploaded to YouTube: {upload_result.video_url}")
                    if pdf_notes_path:
                        self.logger.info(f"PDF study notes linked in description: {pdf_notes_path}")

                    # Mark articles as used
                    article_ids = [a.id for a in video_articles if hasattr(a, 'id')]
                    if article_ids:
                        self.db.mark_articles_used(article_ids, video_id)
                else:
                    results["errors"].append(f"Upload failed: {upload_result.error}")
            else:
                results["steps"]["upload"] = {"skipped": True}

            results["success"] = True
            self.logger.info(f"Pipeline completed successfully: {video_id}")

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            results["errors"].append(str(e))

        return results

    def _get_language_name(self, code: str) -> str:
        """Get language name from code"""
        names = {
            "en": "English",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu"
        }
        return names.get(code, "English")

    def run_sync(self, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for run()"""
        return asyncio.run(self.run(**kwargs))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Current Affairs Video Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Generate and upload video
  python main.py --test             # Generate and upload as private (test)
  python main.py --no-upload        # Generate video without uploading
  python main.py --language hi      # Generate video in Hindi
  python main.py --no-scrape        # Use existing articles only
        """
    )

    parser.add_argument(
        "--language", "-l",
        type=str,
        default="en",
        choices=["en", "hi", "ta", "te"],
        help="Video language (default: en)"
    )

    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Don't upload to YouTube"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - upload as private video"
    )

    parser.add_argument(
        "--no-scrape",
        action="store_true",
        help="Don't scrape new articles, use existing"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/settings.yaml",
        help="Path to configuration file"
    )

    args = parser.parse_args()

    # Run pipeline
    print("\n" + "="*60)
    print("  AI Current Affairs Video Generator")
    print("="*60 + "\n")

    pipeline = VideoGenerationPipeline(config_path=args.config)

    results = pipeline.run_sync(
        language=args.language,
        upload=not args.no_upload,
        test_mode=args.test,
        scrape_fresh=not args.no_scrape
    )

    # Print results
    print("\n" + "="*60)
    print("  Pipeline Results")
    print("="*60 + "\n")

    if results["success"]:
        print("Status: SUCCESS\n")

        for step, info in results["steps"].items():
            print(f"{step.upper()}:")
            if isinstance(info, dict):
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {info}")
            print()

        if results["steps"].get("upload", {}).get("url"):
            print(f"\nVideo URL: {results['steps']['upload']['url']}")

        if results["steps"].get("composition", {}).get("pdf_notes"):
            print(f"PDF Notes: {results['steps']['composition']['pdf_notes']}")

    else:
        print("Status: FAILED\n")
        print("Errors:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("\n" + "="*60 + "\n")

    return 0 if results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
