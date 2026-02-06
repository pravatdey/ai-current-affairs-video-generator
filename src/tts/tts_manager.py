"""
TTS Manager - Orchestrates text-to-speech generation
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import yaml

from .edge_tts_engine import EdgeTTSEngine
from .base_tts import TTSResult, TTSVoice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TTSManager:
    """
    Manages TTS generation with support for multiple languages,
    voice selection, and audio post-processing.
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize TTS Manager.

        Args:
            config_path: Path to settings configuration
        """
        self.config = self._load_config(config_path)
        self.engine = EdgeTTSEngine()

        # Load language configurations
        self.languages = self._load_languages()

        logger.info(f"TTSManager initialized with {len(self.languages)} languages")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            return {}

    def _load_languages(self) -> Dict[str, Dict[str, Any]]:
        """Load language configurations"""
        languages = {}

        lang_config = self.config.get("languages", {}).get("supported", [])

        for lang in lang_config:
            code = lang.get("code", "")
            if code:
                languages[code] = {
                    "name": lang.get("name", code),
                    "voice": lang.get("tts_voice", ""),
                    "rate": lang.get("tts_rate", "+0%"),
                    "pitch": lang.get("tts_pitch", "+0Hz")
                }

        # Ensure English is always available
        if "en" not in languages:
            languages["en"] = {
                "name": "English",
                "voice": "en-US-GuyNeural",
                "rate": "+0%",
                "pitch": "+0Hz"
            }

        return languages

    async def generate_audio(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        voice: str = None,
        rate: str = None,
        pitch: str = None
    ) -> TTSResult:
        """
        Generate audio from text.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            language: Language code
            voice: Override voice ID
            rate: Override speaking rate
            pitch: Override pitch

        Returns:
            TTSResult object
        """
        # Get language settings
        lang_config = self.languages.get(language, self.languages["en"])

        voice = voice or lang_config.get("voice")
        rate = rate or lang_config.get("rate", "+0%")
        pitch = pitch or lang_config.get("pitch", "+0Hz")

        # Use long text synthesis for longer content
        if len(text) > 5000:
            result = await self.engine.synthesize_long_text(
                text=text,
                output_path=output_path,
                voice=voice,
                rate=rate,
                pitch=pitch
            )
        else:
            result = await self.engine.synthesize(
                text=text,
                output_path=output_path,
                voice=voice,
                rate=rate,
                pitch=pitch
            )

        return result

    def generate_audio_sync(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        voice: str = None,
        rate: str = None,
        pitch: str = None
    ) -> TTSResult:
        """
        Synchronous wrapper for audio generation.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            language: Language code
            voice: Override voice ID
            rate: Override speaking rate
            pitch: Override pitch

        Returns:
            TTSResult object
        """
        return asyncio.run(self.generate_audio(
            text=text,
            output_path=output_path,
            language=language,
            voice=voice,
            rate=rate,
            pitch=pitch
        ))

    async def generate_script_audio(
        self,
        script_text: str,
        output_dir: str,
        language: str = "en",
        video_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate audio for a complete video script.

        Args:
            script_text: Full script text
            output_dir: Directory to save audio files
            language: Language code
            video_id: Optional video ID for naming

        Returns:
            Dictionary with audio info
        """
        video_id = video_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"{video_id}_audio.mp3"

        result = await self.generate_audio(
            text=script_text,
            output_path=str(output_path),
            language=language
        )

        if result.success:
            logger.info(f"Generated script audio: {result.duration:.1f}s")
            return {
                "success": True,
                "audio_path": result.audio_path,
                "duration": result.duration,
                "voice": result.voice.id,
                "language": language
            }
        else:
            logger.error(f"Failed to generate script audio: {result.error}")
            return {
                "success": False,
                "error": result.error
            }

    async def list_available_voices(self, language: str = None) -> List[TTSVoice]:
        """
        List available voices.

        Args:
            language: Optional language filter

        Returns:
            List of TTSVoice objects
        """
        return await self.engine.list_voices(language)

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {"code": code, "name": config["name"]}
            for code, config in self.languages.items()
        ]

    async def test_voice(
        self,
        voice: str,
        output_path: str = None
    ) -> TTSResult:
        """
        Test a voice with sample text.

        Args:
            voice: Voice ID to test
            output_path: Optional output path

        Returns:
            TTSResult object
        """
        test_text = "Hello! This is a test of the text-to-speech system. Welcome to today's current affairs update."

        if not output_path:
            output_path = f"output/test_{voice.replace('-', '_')}.mp3"

        return await self.engine.synthesize(
            text=test_text,
            output_path=output_path,
            voice=voice
        )


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TTS Manager CLI")
    parser.add_argument("--test", action="store_true", help="Run TTS test")
    parser.add_argument("--lang", type=str, default="en", help="Language code")
    parser.add_argument("--text", type=str, help="Text to synthesize")
    parser.add_argument("--output", type=str, default="output/test_audio.mp3", help="Output path")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")

    args = parser.parse_args()

    manager = TTSManager()

    if args.list_voices:
        print(f"\n=== Available Voices for {args.lang} ===\n")
        voices = asyncio.run(manager.list_available_voices(args.lang))
        for voice in voices[:20]:  # Limit to 20
            print(f"  {voice.id}: {voice.name} ({voice.gender})")

    elif args.test or args.text:
        text = args.text or "Welcome to today's current affairs update. Let's look at the top stories making headlines."

        print(f"\n=== TTS Test ===")
        print(f"Language: {args.lang}")
        print(f"Text: {text[:50]}...")
        print(f"Output: {args.output}\n")

        result = manager.generate_audio_sync(
            text=text,
            output_path=args.output,
            language=args.lang
        )

        if result.success:
            print(f"Success! Audio saved to: {result.audio_path}")
            print(f"Duration: {result.duration:.1f} seconds")
            print(f"Voice: {result.voice.id}")
        else:
            print(f"Error: {result.error}")

    else:
        parser.print_help()
