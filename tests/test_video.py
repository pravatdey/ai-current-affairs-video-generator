"""
Tests for Video Processing Module
"""

import pytest
from pathlib import Path
import tempfile

from src.video.thumbnail import ThumbnailGenerator
from src.video.effects import VideoEffects


class TestThumbnailGenerator:
    """Tests for Thumbnail Generator"""

    def test_generator_initialization(self):
        """Test generator initialization"""
        generator = ThumbnailGenerator()

        assert generator is not None
        assert generator.size == (1280, 720)

    def test_thumbnail_generation(self):
        """Test generating a thumbnail"""
        generator = ThumbnailGenerator()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            result = generator.generate(
                output_path=output_path,
                title="Test Thumbnail",
                date="January 1, 2024"
            )

            assert result.success
            assert Path(output_path).exists()

            # Check image size
            from PIL import Image
            img = Image.open(output_path)
            assert img.size == (1280, 720)

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_generate_from_headlines(self):
        """Test generating from headlines"""
        generator = ThumbnailGenerator()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            headlines = [
                "Breaking News: Major Event",
                "Second Headline Here"
            ]

            result = generator.generate_from_headlines(
                output_path=output_path,
                headlines=headlines
            )

            assert result.success

        finally:
            Path(output_path).unlink(missing_ok=True)


class TestVideoEffects:
    """Tests for Video Effects"""

    def test_hex_to_rgb(self):
        """Test hex to RGB conversion"""
        rgb = VideoEffects._hex_to_rgb("#ff0000")
        assert rgb == (255, 0, 0)

        rgb = VideoEffects._hex_to_rgb("#1a1a2e")
        assert rgb == (26, 26, 46)

    def test_hex_to_rgb_short(self):
        """Test short hex to RGB conversion"""
        rgb = VideoEffects._hex_to_rgb("#fff")
        assert rgb == (255, 255, 255)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
