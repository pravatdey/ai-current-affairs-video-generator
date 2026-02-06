"""
Daily Scheduler for AI Current Affairs Video Generator

This script runs the video generation pipeline on a daily schedule.
It can be run as a service or in the background.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger, get_logger
from src.utils.scheduler import TaskScheduler
from main import VideoGenerationPipeline


def load_config(config_path: str = "config/settings.yaml") -> dict:
    """Load configuration"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Failed to load config: {e}")
        return {}


def generate_video_task(language: str = "en", upload: bool = True):
    """Task function for scheduled video generation"""
    logger = get_logger("ScheduledTask")

    try:
        logger.info(f"Starting scheduled video generation: language={language}")

        pipeline = VideoGenerationPipeline()
        results = pipeline.run_sync(
            language=language,
            upload=upload,
            test_mode=False,
            scrape_fresh=True
        )

        if results["success"]:
            logger.info(f"Scheduled video generated successfully")
            if results["steps"].get("upload", {}).get("url"):
                logger.info(f"Video URL: {results['steps']['upload']['url']}")
        else:
            logger.error(f"Scheduled video generation failed: {results['errors']}")

    except Exception as e:
        logger.error(f"Scheduled task failed: {e}")


def main():
    """Main entry point for scheduler"""
    parser = argparse.ArgumentParser(
        description="Daily Scheduler for Video Generation"
    )

    parser.add_argument(
        "--time",
        type=str,
        default="06:00",
        help="Time to run daily (HH:MM format, default: 06:00)"
    )

    parser.add_argument(
        "--timezone",
        type=str,
        default="Asia/Kolkata",
        help="Timezone (default: Asia/Kolkata)"
    )

    parser.add_argument(
        "--language",
        type=str,
        default="en",
        choices=["en", "hi", "ta", "te"],
        help="Video language"
    )

    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Don't upload to YouTube"
    )

    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run immediately, then continue with schedule"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once immediately and exit"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logger(log_level="INFO", log_file="logs/scheduler.log")
    logger = get_logger("Scheduler")

    print("\n" + "="*60)
    print("  AI Current Affairs - Daily Scheduler")
    print("="*60 + "\n")

    # Run once mode
    if args.once:
        print("Running video generation once...\n")
        generate_video_task(
            language=args.language,
            upload=not args.no_upload
        )
        return 0

    # Parse time
    try:
        hour, minute = map(int, args.time.split(":"))
    except ValueError:
        print(f"Invalid time format: {args.time}. Use HH:MM")
        return 1

    # Create scheduler
    scheduler = TaskScheduler(timezone=args.timezone, blocking=True)

    # Add daily job
    scheduler.add_daily_job(
        job_id="daily_video_generation",
        func=generate_video_task,
        hour=hour,
        minute=minute,
        language=args.language,
        upload=not args.no_upload
    )

    print(f"Scheduled daily video generation:")
    print(f"  Time: {args.time}")
    print(f"  Timezone: {args.timezone}")
    print(f"  Language: {args.language}")
    print(f"  Upload: {not args.no_upload}")
    print()

    # Run immediately if requested
    if args.run_now:
        print("Running immediately...\n")
        generate_video_task(
            language=args.language,
            upload=not args.no_upload
        )

    # Show next run time
    job_info = scheduler.get_job_info("daily_video_generation")
    if job_info:
        print(f"Next scheduled run: {job_info['next_run']}")

    print("\nScheduler is running. Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
