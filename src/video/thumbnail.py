"""
Thumbnail Generator - Creates YouTube thumbnails for videos
"""

from pathlib import Path
from typing import Tuple, Optional, List
from dataclasses import dataclass
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ThumbnailResult:
    """Result of thumbnail generation"""
    success: bool
    thumbnail_path: str
    resolution: Tuple[int, int]
    error: Optional[str] = None


class ThumbnailGenerator:
    """
    Generates attractive YouTube thumbnails for current affairs videos.

    Features:
    - Text overlay with wrapping
    - Gradient backgrounds
    - Frame extraction from video
    - Custom styling
    """

    # YouTube recommended thumbnail size
    DEFAULT_SIZE = (1280, 720)

    # Default fonts (fallback chain)
    FONT_FALLBACKS = [
        "Arial-Bold",
        "Arial",
        "DejaVuSans-Bold",
        "DejaVuSans",
        "FreeSansBold",
        "FreeSans"
    ]

    def __init__(
        self,
        size: Tuple[int, int] = None,
        font_path: str = None
    ):
        """
        Initialize thumbnail generator.

        Args:
            size: Thumbnail size (width, height)
            font_path: Path to custom font file
        """
        self.size = size or self.DEFAULT_SIZE
        self.font_path = font_path
        self.font = self._load_font()

        logger.info(f"ThumbnailGenerator initialized: {self.size[0]}x{self.size[1]}")

    def _load_font(self, size: int = 72) -> ImageFont.FreeTypeFont:
        """Load font with fallback"""
        # Try custom font path
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except Exception:
                pass

        # Try system fonts
        for font_name in self.FONT_FALLBACKS:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                continue

        # Fallback to default
        return ImageFont.load_default()

    def generate(
        self,
        output_path: str,
        title: str,
        date: str = None,
        background_image: str = None,
        video_path: str = None,
        style: str = "gradient"
    ) -> ThumbnailResult:
        """
        Generate thumbnail.

        Args:
            output_path: Path to save thumbnail
            title: Main title text
            date: Date text (optional)
            background_image: Path to background image
            video_path: Path to video (for frame extraction)
            style: Style preset ("gradient", "image", "video_frame")

        Returns:
            ThumbnailResult object
        """
        try:
            width, height = self.size

            # Create base image
            if style == "video_frame" and video_path:
                img = self._extract_video_frame(video_path)
            elif background_image and Path(background_image).exists():
                img = Image.open(background_image).resize(self.size)
            else:
                img = self._create_gradient_background()

            # Apply overlay effects
            img = self._apply_overlay(img)

            # Add text
            img = self._add_text(img, title, date)

            # Add branding elements
            img = self._add_branding(img)

            # Save
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            img.save(str(output_path), "PNG", quality=95)

            logger.info(f"Thumbnail generated: {output_path}")

            return ThumbnailResult(
                success=True,
                thumbnail_path=str(output_path),
                resolution=self.size
            )

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return ThumbnailResult(
                success=False,
                thumbnail_path="",
                resolution=self.size,
                error=str(e)
            )

    def _create_gradient_background(self) -> Image.Image:
        """Create a gradient background"""
        width, height = self.size

        # Create base image
        img = Image.new('RGB', self.size)
        draw = ImageDraw.Draw(img)

        # Gradient colors (dark blue to purple)
        color1 = (26, 26, 46)    # #1a1a2e
        color2 = (79, 37, 102)   # #4f2566

        # Draw gradient
        for y in range(height):
            r = int(color1[0] + (color2[0] - color1[0]) * y / height)
            g = int(color1[1] + (color2[1] - color1[1]) * y / height)
            b = int(color1[2] + (color2[2] - color1[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        return img

    def _extract_video_frame(self, video_path: str) -> Image.Image:
        """Extract a frame from video"""
        try:
            from moviepy.editor import VideoFileClip

            clip = VideoFileClip(video_path)
            # Get frame at 30% of video duration
            frame_time = clip.duration * 0.3
            frame = clip.get_frame(frame_time)
            clip.close()

            img = Image.fromarray(frame)
            return img.resize(self.size)

        except Exception as e:
            logger.warning(f"Failed to extract video frame: {e}")
            return self._create_gradient_background()

    def _apply_overlay(self, img: Image.Image) -> Image.Image:
        """Apply darkening overlay for better text visibility"""
        # Create dark overlay
        overlay = Image.new('RGBA', self.size, (0, 0, 0, 128))

        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Composite
        img = Image.alpha_composite(img, overlay)

        # Convert back to RGB
        return img.convert('RGB')

    def _add_text(
        self,
        img: Image.Image,
        title: str,
        date: str = None
    ) -> Image.Image:
        """Add title and date text to thumbnail"""
        draw = ImageDraw.Draw(img)
        width, height = self.size

        # Title font
        title_font_size = 72
        title_font = self._load_font(title_font_size)

        # Wrap title text
        max_chars = 25  # Characters per line
        wrapped_title = textwrap.fill(title, width=max_chars)
        lines = wrapped_title.split('\n')

        # Calculate text position
        total_text_height = len(lines) * (title_font_size + 10)
        y_start = (height - total_text_height) // 2 - 30

        # Draw title with outline
        for i, line in enumerate(lines):
            # Get text bounding box
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_start + i * (title_font_size + 10)

            # Draw outline
            outline_color = (0, 0, 0)
            for ox, oy in [(-3, -3), (-3, 3), (3, -3), (3, 3), (-3, 0), (3, 0), (0, -3), (0, 3)]:
                draw.text((x + ox, y + oy), line, font=title_font, fill=outline_color)

            # Draw text
            draw.text((x, y), line, font=title_font, fill=(255, 255, 255))

        # Draw date if provided
        if date:
            date_font = self._load_font(36)
            bbox = draw.textbbox((0, 0), date, font=date_font)
            date_width = bbox[2] - bbox[0]
            date_x = (width - date_width) // 2
            date_y = y_start + total_text_height + 30

            # Draw with outline
            for ox, oy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                draw.text((date_x + ox, date_y + oy), date, font=date_font, fill=(0, 0, 0))
            draw.text((date_x, date_y), date, font=date_font, fill=(255, 200, 100))

        return img

    def _add_branding(self, img: Image.Image) -> Image.Image:
        """Add branding elements"""
        draw = ImageDraw.Draw(img)
        width, height = self.size

        # Add "CURRENT AFFAIRS" badge
        badge_font = self._load_font(28)
        badge_text = "CURRENT AFFAIRS"

        # Badge background
        badge_padding = 15
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_width = bbox[2] - bbox[0] + badge_padding * 2
        badge_height = bbox[3] - bbox[1] + badge_padding * 2

        badge_x = 30
        badge_y = 30

        # Draw badge background
        draw.rectangle(
            [badge_x, badge_y, badge_x + badge_width, badge_y + badge_height],
            fill=(200, 30, 58)  # Red color
        )

        # Draw badge text
        draw.text(
            (badge_x + badge_padding, badge_y + badge_padding - 5),
            badge_text,
            font=badge_font,
            fill=(255, 255, 255)
        )

        # Add "LIVE" indicator (optional visual element)
        live_x = width - 100
        live_y = 30

        # Draw circle
        draw.ellipse(
            [live_x, live_y + 5, live_x + 15, live_y + 20],
            fill=(255, 0, 0)
        )

        # Draw "LIVE" text
        live_font = self._load_font(24)
        draw.text(
            (live_x + 22, live_y),
            "DAILY",
            font=live_font,
            fill=(255, 255, 255)
        )

        return img

    def generate_from_headlines(
        self,
        output_path: str,
        headlines: List[str],
        date: str = None
    ) -> ThumbnailResult:
        """
        Generate thumbnail from list of headlines.
        Uses the first headline as the main title.

        Args:
            output_path: Path to save thumbnail
            headlines: List of headlines
            date: Date text

        Returns:
            ThumbnailResult object
        """
        if not headlines:
            title = "Today's Top News"
        else:
            # Use first headline, truncate if too long
            title = headlines[0]
            if len(title) > 60:
                title = title[:57] + "..."

        return self.generate(
            output_path=output_path,
            title=title,
            date=date
        )


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Thumbnail Generator CLI")
    parser.add_argument("--title", type=str, default="Breaking News Today", help="Thumbnail title")
    parser.add_argument("--date", type=str, help="Date text")
    parser.add_argument("--output", type=str, default="output/thumbnail.png", help="Output path")
    parser.add_argument("--background", type=str, help="Background image path")
    parser.add_argument("--video", type=str, help="Video path for frame extraction")

    args = parser.parse_args()

    generator = ThumbnailGenerator()

    style = "gradient"
    if args.video:
        style = "video_frame"
    elif args.background:
        style = "image"

    result = generator.generate(
        output_path=args.output,
        title=args.title,
        date=args.date,
        background_image=args.background,
        video_path=args.video,
        style=style
    )

    if result.success:
        print(f"\nSuccess! Thumbnail saved to: {result.thumbnail_path}")
        print(f"Resolution: {result.resolution[0]}x{result.resolution[1]}")
    else:
        print(f"\nError: {result.error}")
