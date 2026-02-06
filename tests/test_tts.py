"""
Tests for Text-to-Speech Module
"""

import pytest
import asyncio
from pathlib import Path
import tempfile

from src.tts.edge_tts_engine import EdgeTTSEngine
from src.tts.tts_manager import TTSManager


class TestEdgeTTSEngine:
    """Tests for Edge TTS Engine"""

    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = EdgeTTSEngine()

        assert engine is not None
        assert engine.default_voice is not None

    def test_get_default_voice(self):
        """Test getting default voice for language"""
        engine = EdgeTTSEngine()

        en_voice = engine.get_default_voice("en")
        hi_voice = engine.get_default_voice("hi")

        assert "en" in en_voice.lower()
        assert "hi" in hi_voice.lower()

    @pytest.mark.asyncio
    async def test_list_voices(self):
        """Test listing available voices"""
        engine = EdgeTTSEngine()

        voices = await engine.list_voices("en")

        assert len(voices) > 0
        assert all(v.language == "en" for v in voices)


class TestTTSManager:
    """Tests for TTS Manager"""

    def test_manager_initialization(self):
        """Test manager initialization"""
        manager = TTSManager()

        assert manager is not None
        assert manager.engine is not None

    def test_get_supported_languages(self):
        """Test getting supported languages"""
        manager = TTSManager()

        languages = manager.get_supported_languages()

        assert len(languages) > 0
        # English should always be supported
        codes = [lang["code"] for lang in languages]
        assert "en" in codes

    @pytest.mark.asyncio
    async def test_audio_generation(self):
        """Test generating audio"""
        manager = TTSManager()

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name

        try:
            result = await manager.generate_audio(
                text="Hello, this is a test.",
                output_path=output_path,
                language="en"
            )

            assert result.success
            assert Path(output_path).exists()
            assert result.duration > 0

        finally:
            Path(output_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
