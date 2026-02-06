"""
Auto Scheduler for UPSC Current Affairs Video Generator

Schedule:
- 10:00 AM: Generate video + PDF notes
- 11:00 AM: Upload to YouTube

Usage:
    python scheduler_auto.py --generate-time 10:00 --upload-time 11:00
    python scheduler_auto.py --run-now  # Test immediately
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.utils.logger import setup_logger, get_logger
from main import VideoGenerationPipeline
from src.youtube.uploader import YouTubeUploader
from src.youtube.metadata import MetadataGenerator

# Global state file to track pending uploads
STATE_FILE = "data/scheduler_state.json"


class AutoScheduler:
    """
    Automated scheduler for UPSC video generation and YouTube upload.

    Workflow:
    1. Generate video at specified time (e.g., 10:00 AM)
    2. Save video details to state file
    3. Upload to YouTube at specified time (e.g., 11:00 AM)
    """

    def __init__(
        self,
        generate_time: str = "10:00",
        upload_time: str = "11:00",
        timezone: str = "Asia/Kolkata",
        language: str = "en"
    ):
        self.generate_time = generate_time
        self.upload_time = upload_time
        self.timezone = timezone
        self.language = language

        self.scheduler = BlockingScheduler(timezone=timezone)
        self.logger = get_logger("AutoScheduler")

        # Ensure state directory exists
        Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> Dict[str, Any]:
        """Load scheduler state"""
        try:
            if Path(STATE_FILE).exists():
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load state: {e}")
        return {"pending_upload": None}

    def _save_state(self, state: Dict[str, Any]):
        """Save scheduler state"""
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def generate_video_task(self):
        """Task: Generate UPSC video and PDF notes"""
        self.logger.info("="*50)
        self.logger.info("Starting video generation task")
        self.logger.info("="*50)

        try:
            # Run video generation pipeline
            pipeline = VideoGenerationPipeline()
            results = pipeline.run_sync(
                language=self.language,
                upload=False,  # Don't upload yet
                test_mode=False,
                scrape_fresh=True
            )

            if results["success"]:
                # Save video details for upload task
                video_data = {
                    "video_path": results["steps"].get("composition", {}).get("video_path", ""),
                    "thumbnail_path": results["steps"].get("thumbnail", {}).get("path", ""),
                    "pdf_path": results["steps"].get("composition", {}).get("pdf_notes_path", ""),
                    "headlines": results["steps"].get("scraping", {}).get("headlines", []),
                    "title": results["steps"].get("script", {}).get("title", ""),
                    "date": datetime.now().strftime("%B %d, %Y"),
                    "language": self.language,
                    "generated_at": datetime.now().isoformat(),
                    "duration": results["steps"].get("composition", {}).get("duration", 0)
                }

                state = self._load_state()
                state["pending_upload"] = video_data
                self._save_state(state)

                self.logger.info(f"Video generated successfully!")
                self.logger.info(f"  Path: {video_data['video_path']}")
                self.logger.info(f"  PDF Notes: {video_data['pdf_path']}")
                self.logger.info(f"  Duration: {video_data['duration']:.1f}s")
                self.logger.info(f"Scheduled for upload at {self.upload_time}")

            else:
                self.logger.error(f"Video generation failed: {results.get('errors', [])}")

        except Exception as e:
            self.logger.error(f"Video generation task failed: {e}")
            import traceback
            traceback.print_exc()

    def upload_video_task(self):
        """Task: Upload pending video to YouTube"""
        self.logger.info("="*50)
        self.logger.info("Starting YouTube upload task")
        self.logger.info("="*50)

        try:
            # Load pending video
            state = self._load_state()
            video_data = state.get("pending_upload")

            if not video_data:
                self.logger.warning("No pending video to upload")
                return

            video_path = video_data.get("video_path", "")
            if not video_path or not Path(video_path).exists():
                self.logger.error(f"Video file not found: {video_path}")
                return

            # Initialize uploader
            uploader = YouTubeUploader()

            # Prepare metadata
            headlines = video_data.get("headlines", [])
            date = video_data.get("date", datetime.now().strftime("%B %d, %Y"))
            pdf_path = video_data.get("pdf_path", "")

            # Generate optimized metadata
            metadata_gen = MetadataGenerator()
            metadata = metadata_gen.generate(
                headlines=headlines,
                date=date,
                language=video_data.get("language", "en")
            )

            # Add PDF notes link to description
            description = metadata["description"]
            if pdf_path and Path(pdf_path).exists():
                description += f"\n\n📚 PDF Notes: Available in pinned comment"

            # Upload video
            self.logger.info(f"Uploading: {metadata['title']}")

            result = uploader.upload(
                video_path=video_path,
                title=metadata["title"],
                description=description,
                tags=metadata["tags"],
                category_id=metadata["category_id"],
                privacy_status="public",
                thumbnail_path=video_data.get("thumbnail_path"),
                made_for_kids=False
            )

            if result.success:
                self.logger.info("="*50)
                self.logger.info("UPLOAD SUCCESSFUL!")
                self.logger.info(f"  Video ID: {result.video_id}")
                self.logger.info(f"  URL: {result.video_url}")
                self.logger.info("="*50)

                # Clear pending upload
                state["pending_upload"] = None
                state["last_upload"] = {
                    "video_id": result.video_id,
                    "url": result.video_url,
                    "title": result.title,
                    "uploaded_at": datetime.now().isoformat()
                }
                self._save_state(state)

            else:
                self.logger.error(f"Upload failed: {result.error}")

        except Exception as e:
            self.logger.error(f"Upload task failed: {e}")
            import traceback
            traceback.print_exc()

    def setup_schedule(self):
        """Setup the scheduled jobs"""
        # Parse times
        gen_hour, gen_minute = map(int, self.generate_time.split(":"))
        upload_hour, upload_minute = map(int, self.upload_time.split(":"))

        # Add video generation job
        self.scheduler.add_job(
            self.generate_video_task,
            CronTrigger(hour=gen_hour, minute=gen_minute, timezone=self.timezone),
            id="generate_video",
            name="Generate UPSC Video"
        )

        # Add upload job
        self.scheduler.add_job(
            self.upload_video_task,
            CronTrigger(hour=upload_hour, minute=upload_minute, timezone=self.timezone),
            id="upload_video",
            name="Upload to YouTube"
        )

        self.logger.info(f"Scheduled jobs:")
        self.logger.info(f"  Generate Video: {self.generate_time} ({self.timezone})")
        self.logger.info(f"  Upload Video:   {self.upload_time} ({self.timezone})")

    def run_now(self, skip_upload: bool = False):
        """Run the full workflow immediately"""
        self.logger.info("Running workflow immediately...")

        # Generate video
        self.generate_video_task()

        # Upload if requested
        if not skip_upload:
            self.logger.info("Waiting 30 seconds before upload...")
            import time
            time.sleep(30)
            self.upload_video_task()

    def start(self):
        """Start the scheduler"""
        self.setup_schedule()

        print("\n" + "="*60)
        print("  UPSC Current Affairs - Auto Scheduler")
        print("="*60)
        print(f"\n  Generate Time: {self.generate_time}")
        print(f"  Upload Time:   {self.upload_time}")
        print(f"  Timezone:      {self.timezone}")
        print(f"  Language:      {self.language}")
        print("\n  Press Ctrl+C to stop\n")
        print("="*60 + "\n")

        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            print("\nScheduler stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="UPSC Video Auto Scheduler - Generate at 10AM, Upload at 11AM"
    )

    parser.add_argument(
        "--generate-time",
        type=str,
        default="10:00",
        help="Time to generate video (HH:MM, default: 10:00)"
    )

    parser.add_argument(
        "--upload-time",
        type=str,
        default="11:00",
        help="Time to upload to YouTube (HH:MM, default: 11:00)"
    )

    parser.add_argument(
        "--timezone",
        type=str,
        default="Asia/Kolkata",
        help="Timezone (default: Asia/Kolkata for IST)"
    )

    parser.add_argument(
        "--language",
        type=str,
        default="en",
        choices=["en", "hi", "ta", "te"],
        help="Video language (default: en)"
    )

    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run full workflow immediately (generate + upload)"
    )

    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Run generation only (no upload)"
    )

    parser.add_argument(
        "--upload-pending",
        action="store_true",
        help="Upload any pending video from previous generation"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logger(log_level="INFO", log_file="logs/auto_scheduler.log")

    # Create scheduler
    scheduler = AutoScheduler(
        generate_time=args.generate_time,
        upload_time=args.upload_time,
        timezone=args.timezone,
        language=args.language
    )

    if args.run_now:
        scheduler.run_now(skip_upload=False)
    elif args.generate_only:
        scheduler.generate_video_task()
    elif args.upload_pending:
        scheduler.upload_video_task()
    else:
        scheduler.start()


if __name__ == "__main__":
    main()
