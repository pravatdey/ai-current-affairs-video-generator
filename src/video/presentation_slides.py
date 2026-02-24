"""
Presentation Slides Generator - Creates timed presentation slides from script data
for use as video background behind the avatar.

Each news segment gets a professional slide showing:
- Topic title and number
- Key bullet points
- Important terms / abbreviations (as a table)
- Subject category and exam relevance tags
"""

import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import fadein, fadeout

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SlideContent:
    """Data for one presentation slide."""
    title: str
    subtitle: str                              # subject category
    bullet_points: List[str] = field(default_factory=list)
    important_terms: Dict[str, str] = field(default_factory=dict)
    exam_tag: str = ""                         # PRELIMS / MAINS / BOTH
    topic_number: int = 1
    start_time: float = 0.0
    duration: float = 10.0
    table_data: Optional[List[List[str]]] = None


class PresentationSlideGenerator:
    """
    Generates presentation-style slide images from script data.
    Slides are designed so the left ~35 % can be overlaid by the avatar
    while key content remains readable on the right.
    """

    # Color themes matching educational_effects.py
    THEMES = {
        'Polity': {'primary': (26, 54, 93), 'accent': (66, 153, 225), 'header': (20, 45, 80)},
        'Economy': {'primary': (34, 84, 61), 'accent': (104, 211, 145), 'header': (28, 70, 50)},
        'International Relations': {'primary': (68, 51, 122), 'accent': (183, 148, 244), 'header': (55, 40, 100)},
        'Environment': {'primary': (34, 84, 61), 'accent': (104, 211, 145), 'header': (28, 70, 50)},
        'Science & Technology': {'primary': (26, 54, 93), 'accent': (66, 153, 225), 'header': (20, 45, 80)},
        'Social Issues': {'primary': (124, 45, 18), 'accent': (251, 211, 141), 'header': (100, 35, 14)},
        'Security': {'primary': (120, 30, 30), 'accent': (230, 120, 120), 'header': (95, 22, 22)},
        'Geography': {'primary': (34, 84, 61), 'accent': (104, 211, 145), 'header': (28, 70, 50)},
        'History': {'primary': (124, 45, 18), 'accent': (251, 211, 141), 'header': (100, 35, 14)},
        'Current Affairs': {'primary': (26, 54, 93), 'accent': (66, 153, 225), 'header': (20, 45, 80)},
    }

    EXAM_TAG_COLORS = {
        'PRELIMS': (49, 130, 206),
        'MAINS': (128, 90, 213),
        'BOTH': (56, 161, 105),
    }

    def __init__(self, content_start_x_pct: float = 0.33):
        """
        Args:
            content_start_x_pct: Fraction of width where slide content starts
                                 (left of this is avatar territory).
        """
        self.content_start_x_pct = content_start_x_pct
        self._load_fonts()
        logger.info("PresentationSlideGenerator initialized")

    def _load_fonts(self):
        """Load fonts with fallback chain."""
        self.fonts = {}
        sizes = {
            'title': 42,
            'heading': 32,
            'body': 26,
            'small': 20,
            'tiny': 16,
            'tag': 18,
        }
        for name, size in sizes.items():
            self.fonts[name] = self._try_load_font(size)

    @staticmethod
    def _try_load_font(size: int) -> ImageFont.FreeTypeFont:
        for path in ["arial.ttf", "arialbd.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
        return ImageFont.load_default()

    # ── Public API ────────────────────────────────────────────────────────

    def generate_slides(
        self,
        script_data: Dict[str, Any],
        video_size: Tuple[int, int],
        total_duration: float
    ) -> List:
        """
        Generate all presentation slide clips from script_data.

        Returns a list of moviepy ImageClip objects, each with
        set_start / set_duration / fade applied.
        """
        segments = script_data.get('segments', [])
        news_segments = [s for s in segments if s.get('type') == 'news']

        if not news_segments:
            return []

        clips = []
        for i, segment in enumerate(news_segments):
            start = self._parse_timestamp(segment.get('timestamp', '00:00'))

            # Duration = gap until next segment (or until total_duration)
            if i + 1 < len(news_segments):
                next_start = self._parse_timestamp(news_segments[i + 1].get('timestamp', '00:00'))
                duration = max(next_start - start, 5.0)
            else:
                duration = max(total_duration - start, 5.0)

            slide = SlideContent(
                title=segment.get('article_title', 'Topic'),
                subtitle=segment.get('subject_category', 'Current Affairs'),
                bullet_points=segment.get('key_points', []),
                important_terms=segment.get('important_terms', {}),
                exam_tag=segment.get('exam_relevance', ''),
                topic_number=i + 1,
                start_time=start,
                duration=duration,
                table_data=self._extract_table_data(segment),
            )

            try:
                clip = self._slide_to_clip(slide, video_size)
                clips.append(clip)
            except Exception as e:
                logger.warning(f"Failed to create slide {i + 1}: {e}")

        logger.info(f"Generated {len(clips)} presentation slides")
        return clips

    # ── Internal ──────────────────────────────────────────────────────────

    def _slide_to_clip(self, slide: SlideContent, video_size: Tuple[int, int]):
        """Render one slide image and wrap as a timed ImageClip."""
        img = self._create_slide_image(slide, video_size)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            clip = ImageClip(f.name).set_duration(slide.duration)

        clip = clip.set_start(slide.start_time)
        clip = fadein(clip, 0.5)
        clip = fadeout(clip, 0.5)
        return clip

    def _create_slide_image(
        self,
        slide: SlideContent,
        video_size: Tuple[int, int]
    ) -> Image.Image:
        """Create a single presentation slide as a PIL image."""
        width, height = video_size
        colors = self.THEMES.get(slide.subtitle, self.THEMES['Current Affairs'])

        # Dark background
        img = Image.new('RGB', (width, height), (14, 18, 28))
        draw = ImageDraw.Draw(img)

        content_x = int(width * self.content_start_x_pct)
        padding = 25
        right_margin = 40

        # ── 1. Header bar (full width gradient) ─────────────────────────
        header_h = 90
        self._draw_header(draw, img, slide, width, header_h, colors)

        # ── 2. Left decorative area (where avatar will be) ──────────────
        # Subtle vertical accent line separating avatar area from content
        accent_x = content_x - 10
        draw.line([(accent_x, header_h + 10), (accent_x, height - 70)],
                  fill=colors['accent'], width=3)

        # Subtle gradient glow on left side
        for x in range(0, content_x - 15):
            alpha = int(12 * (1 - x / (content_x - 15)))
            draw.line([(x, header_h), (x, height - 60)],
                      fill=(colors['accent'][0], colors['accent'][1], colors['accent'][2]))

        # Re-draw background over the gradient (keep it very subtle)
        overlay = Image.new('RGBA', (content_x - 15, height - header_h - 60), (14, 18, 28, 220))
        img.paste(Image.alpha_composite(
            Image.new('RGBA', overlay.size, (14, 18, 28, 255)), overlay
        ).convert('RGB'), (0, header_h))

        draw = ImageDraw.Draw(img)

        # Re-draw accent line (might have been covered)
        draw.line([(accent_x, header_h + 10), (accent_x, height - 70)],
                  fill=colors['accent'], width=3)

        # ── 3. Bullet points ────────────────────────────────────────────
        y_cursor = header_h + 30

        if slide.bullet_points:
            # Section label
            draw.text((content_x + padding, y_cursor), "KEY POINTS",
                      fill=colors['accent'], font=self.fonts['tag'])
            y_cursor += 30

            # Underline
            draw.line([(content_x + padding, y_cursor),
                       (content_x + padding + 100, y_cursor)],
                      fill=colors['accent'], width=2)
            y_cursor += 15

            max_text_w = width - content_x - padding - right_margin
            for j, point in enumerate(slide.bullet_points[:5]):
                bullet_y = y_cursor + 5

                # Bullet dot
                dot_r = 5
                draw.ellipse([content_x + padding, bullet_y + 4,
                              content_x + padding + dot_r * 2, bullet_y + 4 + dot_r * 2],
                             fill=colors['accent'])

                # Text (with wrapping)
                text_x = content_x + padding + 20
                wrapped = self._wrap_text(point, max_text_w - 20,
                                          self.fonts['body'], draw)
                draw.text((text_x, bullet_y), wrapped,
                          fill=(230, 235, 245), font=self.fonts['body'])

                # Calculate height used
                lines = wrapped.count('\n') + 1
                y_cursor += lines * 32 + 12

        # ── 4. Table (important terms or structured data) ────────────────
        if slide.table_data and y_cursor < height - 200:
            y_cursor += 15
            y_cursor = self._draw_table(draw, slide.table_data, y_cursor,
                                        content_x + padding, width - right_margin,
                                        colors)
        elif slide.important_terms and y_cursor < height - 200:
            y_cursor += 15
            y_cursor = self._draw_terms(draw, slide.important_terms, y_cursor,
                                        content_x + padding, width - right_margin,
                                        colors)

        # ── 5. Footer bar ────────────────────────────────────────────────
        footer_h = 55
        footer_y = height - footer_h
        draw.rectangle([(0, footer_y), (width, height)],
                       fill=colors['header'])

        # Footer left: channel / branding
        draw.text((20, footer_y + 15), "UPSC Current Affairs",
                  fill=(200, 210, 230), font=self.fonts['small'])

        # Footer center: subject
        sub_text = slide.subtitle
        sub_bbox = draw.textbbox((0, 0), sub_text, font=self.fonts['small'])
        sub_w = sub_bbox[2] - sub_bbox[0]
        draw.text(((width - sub_w) // 2, footer_y + 15), sub_text,
                  fill=colors['accent'], font=self.fonts['small'])

        # Footer right: topic number
        topic_text = f"Topic {slide.topic_number}"
        t_bbox = draw.textbbox((0, 0), topic_text, font=self.fonts['small'])
        draw.text((width - (t_bbox[2] - t_bbox[0]) - 20, footer_y + 15),
                  topic_text, fill=(200, 210, 230), font=self.fonts['small'])

        # Top accent line on footer
        draw.line([(0, footer_y), (width, footer_y)],
                  fill=colors['accent'], width=3)

        return img

    # ── Drawing helpers ───────────────────────────────────────────────────

    def _draw_header(self, draw, img, slide, width, header_h, colors):
        """Draw the slide header bar with topic number, title, exam tag."""
        # Header background
        draw.rectangle([(0, 0), (width, header_h)], fill=colors['header'])

        # Bottom border
        draw.line([(0, header_h), (width, header_h)],
                  fill=colors['accent'], width=3)

        # Topic number badge
        badge_text = f"#{slide.topic_number}"
        badge_font = self.fonts['heading']
        badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = badge_bbox[2] - badge_bbox[0] + 24
        badge_h = badge_bbox[3] - badge_bbox[1] + 14

        badge_x = 20
        badge_y = (header_h - badge_h) // 2
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=8, fill=colors['accent']
        )
        draw.text((badge_x + 12, badge_y + 5), badge_text,
                  fill=(20, 25, 40), font=badge_font)

        # Title text
        title_x = badge_x + badge_w + 20
        max_title_w = width - title_x - 160  # leave room for exam tag
        title_text = self._truncate_text(slide.title, max_title_w,
                                         self.fonts['title'], draw)
        title_y = (header_h - 42) // 2
        draw.text((title_x, title_y), title_text,
                  fill=(240, 245, 255), font=self.fonts['title'])

        # Exam tag badge (right side)
        if slide.exam_tag:
            tag_color = self.EXAM_TAG_COLORS.get(slide.exam_tag, (100, 100, 100))
            tag_text = slide.exam_tag
            tag_font = self.fonts['tag']
            tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
            tag_w = tag_bbox[2] - tag_bbox[0] + 20
            tag_h = tag_bbox[3] - tag_bbox[1] + 10

            tag_x = width - tag_w - 20
            tag_y = (header_h - tag_h) // 2
            draw.rounded_rectangle(
                [tag_x, tag_y, tag_x + tag_w, tag_y + tag_h],
                radius=6, fill=tag_color
            )
            draw.text((tag_x + 10, tag_y + 4), tag_text,
                      fill=(255, 255, 255), font=tag_font)

    def _draw_table(self, draw, table_data, y_start, x_start, x_end,
                    colors) -> int:
        """Draw a simple table. Returns the y position after the table."""
        if not table_data or len(table_data) < 2:
            return y_start

        col_count = len(table_data[0])
        table_w = x_end - x_start
        col_w = table_w // col_count
        row_h = 36
        font = self.fonts['small']

        # Table label
        draw.text((x_start, y_start), "IMPORTANT DATA",
                  fill=colors['accent'], font=self.fonts['tag'])
        y_start += 28

        for row_idx, row in enumerate(table_data[:7]):  # max 7 rows
            y = y_start + row_idx * row_h

            # Header row background
            if row_idx == 0:
                draw.rectangle(
                    [x_start, y, x_end, y + row_h],
                    fill=colors['primary']
                )
            else:
                # Alternating row colors
                bg = (22, 28, 42) if row_idx % 2 == 0 else (18, 22, 35)
                draw.rectangle([x_start, y, x_end, y + row_h], fill=bg)

            # Row border
            draw.line([(x_start, y + row_h), (x_end, y + row_h)],
                      fill=(50, 60, 80), width=1)

            # Cell text
            for col_idx, cell in enumerate(row[:col_count]):
                cx = x_start + col_idx * col_w + 10
                text = str(cell)[:30]  # truncate long text
                text_color = colors['accent'] if row_idx == 0 else (210, 215, 230)
                draw.text((cx, y + 8), text, fill=text_color, font=font)

            # Column dividers
            for col_idx in range(1, col_count):
                div_x = x_start + col_idx * col_w
                draw.line([(div_x, y), (div_x, y + row_h)],
                          fill=(50, 60, 80), width=1)

        # Outer border
        total_h = len(table_data[:7]) * row_h
        draw.rectangle(
            [x_start, y_start, x_end, y_start + total_h],
            outline=colors['accent'], width=2
        )

        return y_start + total_h + 15

    def _draw_terms(self, draw, terms, y_start, x_start, x_end,
                    colors) -> int:
        """Draw important terms as a compact key-value section."""
        if not terms:
            return y_start

        draw.text((x_start, y_start), "KEY TERMS",
                  fill=colors['accent'], font=self.fonts['tag'])
        y_start += 28

        draw.line([(x_start, y_start), (x_start + 80, y_start)],
                  fill=colors['accent'], width=2)
        y_start += 8

        font = self.fonts['small']
        max_w = x_end - x_start

        for i, (term, definition) in enumerate(list(terms.items())[:5]):
            text = f"{term}: {definition}"
            text = self._truncate_text(text, max_w, font, draw)

            # Term in accent color, definition in white
            draw.text((x_start + 5, y_start), term + ":",
                      fill=colors['accent'], font=font)

            term_bbox = draw.textbbox((0, 0), term + ": ", font=font)
            term_w = term_bbox[2] - term_bbox[0]

            draw.text((x_start + 5 + term_w, y_start), definition,
                      fill=(210, 215, 230), font=font)

            y_start += 30

        return y_start + 10

    # ── Utilities ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_timestamp(ts: str) -> float:
        """Convert 'MM:SS' to seconds."""
        try:
            parts = ts.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return 0.0
        except (ValueError, AttributeError):
            return 0.0

    @staticmethod
    def _extract_table_data(segment: Dict[str, Any]) -> Optional[List[List[str]]]:
        """
        Extract table data from a segment.
        Uses important_terms as a two-column table if there are enough entries.
        """
        terms = segment.get('important_terms', {})
        if terms and len(terms) >= 2:
            rows = [["Term", "Definition"]]
            for term, defn in list(terms.items())[:6]:
                rows.append([str(term), str(defn)])
            return rows
        return None

    def _wrap_text(self, text: str, max_width: int,
                   font: ImageFont.FreeTypeFont,
                   draw: ImageDraw.ImageDraw) -> str:
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current = []

        for word in words:
            test = ' '.join(current + [word])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(' '.join(current))
                current = [word]

        if current:
            lines.append(' '.join(current))

        return '\n'.join(lines[:3])  # max 3 lines

    def _truncate_text(self, text: str, max_width: int,
                       font: ImageFont.FreeTypeFont,
                       draw: ImageDraw.ImageDraw) -> str:
        """Truncate text with ellipsis if it exceeds max_width."""
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return text

        while len(text) > 3:
            text = text[:-1]
            bbox = draw.textbbox((0, 0), text + "...", font=font)
            if bbox[2] - bbox[0] <= max_width:
                return text + "..."

        return text
