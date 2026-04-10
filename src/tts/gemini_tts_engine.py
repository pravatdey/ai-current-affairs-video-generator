"""
Google Gemini TTS Engine — Free, realistic text-to-speech

Uses Gemini 2.5 Flash Preview TTS via Google's genai SDK.
Genuinely free: no billing, no credit card, no charges.

Supports Hindi and 24+ languages with 30 studio-quality voices.
Requires GEMINI_API_KEY in .env (free: https://aistudio.google.com/apikey).
"""

import asyncio
import json
import os
import re
import wave
from pathlib import Path
from typing import List, Optional

try:
    import imageio_ffmpeg
    import pydub
    pydub.AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
    pydub.AudioSegment.ffprobe = imageio_ffmpeg.get_ffmpeg_exe().replace('ffmpeg', 'ffprobe')
except ImportError:
    pass

from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

from .base_tts import BaseTTS, TTSResult, TTSVoice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiTTSEngine(BaseTTS):
    """
    TTS engine powered by Google Gemini 2.5 Flash Preview TTS.
    Free tier, no billing, 30 voices, 24+ languages including Hindi.
    """

    MODEL = "gemini-2.5-flash-preview-tts"

    # Gemini TTS voices — all support multilingual including Hindi
    # Picked based on clarity and news-anchor suitability
    DEFAULT_VOICES = {
        "hi": "Kore",       # Clear, confident — good for Hindi news
        "en": "Orus",       # Clear male English
        "ta": "Kore",
        "te": "Kore",
        "bn": "Kore",
    }

    FEMALE_VOICES = {
        "hi": "Zephyr",     # Warm, expressive female
        "en": "Zephyr",
    }

    # All available Gemini TTS voices (for reference)
    ALL_VOICES = [
        "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda",
        "Orus", "Pegasus", "Proteus", "Perseus", "Iapetus",
        "Umbriel", "Algieba", "Autonoe", "Callirrhoe", "Dione",
        "Enceladus", "Erinome", "Gacrux", "Hyperion", "Juliet",
        "Laomedeia", "Mimas", "Narvi", "Oberon", "Pandora",
        "Polaris", "Pulcherrima", "Rasalgethi", "Sulafat",
    ]

    # Max input tokens for the model is 8192, but we chunk by characters
    # to be safe. ~3000 chars is well within limits.
    MAX_CHARS_PER_REQUEST = 3000

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_language: str = "hi",
        voice_name: Optional[str] = None,
        timeout: int = 120,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Get a free key at "
                "https://aistudio.google.com/apikey and add to .env"
            )

        self.default_language = default_language
        self.voice_name_override = voice_name
        self.timeout = timeout

        # Initialize the genai client
        from google import genai
        self.client = genai.Client(api_key=self.api_key)

        logger.info(
            f"Initialized GeminiTTSEngine: model={self.MODEL}, "
            f"language={default_language}"
        )

    # ------------------------------------------------------------------
    # Text pre-processing
    # ------------------------------------------------------------------
    def _preprocess_text(self, text: str) -> str:
        """Strip markdown/symbols that would be read literally."""
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
        text = re.sub(r'`([^`]*)`', r'\1', text)
        text = re.sub(r'^[\s]*[▸♦→•\-\*]+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\(GS\d[^)]*\)', '', text)
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'[✔✗✓✕→←↑↓■□●○◆◇★☆]', '', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks at sentence boundaries."""
        if len(text) <= self.MAX_CHARS_PER_REQUEST:
            return [text]

        chunks = []
        current = ""
        sentences = re.split(r'(?<=[.!?।])\s+', text)

        for sentence in sentences:
            if len(sentence) > self.MAX_CHARS_PER_REQUEST:
                if current:
                    chunks.append(current.strip())
                    current = ""
                words = sentence.split()
                buf = ""
                for word in words:
                    if len(buf) + len(word) + 1 > self.MAX_CHARS_PER_REQUEST:
                        chunks.append(buf.strip())
                        buf = word
                    else:
                        buf = f"{buf} {word}" if buf else word
                if buf:
                    current = buf
                continue

            if len(current) + len(sentence) + 1 <= self.MAX_CHARS_PER_REQUEST:
                current = f"{current} {sentence}" if current else sentence
            else:
                chunks.append(current.strip())
                current = sentence

        if current:
            chunks.append(current.strip())

        return [c for c in chunks if c]

    # ------------------------------------------------------------------
    # Audio post-processing
    # ------------------------------------------------------------------
    def _postprocess_audio(self, audio_path: str) -> None:
        try:
            audio = AudioSegment.from_file(audio_path)
            audio = audio.high_pass_filter(80)
            audio = audio.low_pass_filter(12000)
            try:
                audio = compress_dynamic_range(
                    audio, threshold=-18.0, ratio=2.0,
                    attack=10.0, release=100.0
                )
            except Exception:
                pass
            audio = normalize(audio, headroom=2.0)
            audio.export(audio_path, format="mp3", bitrate="192k",
                         parameters=["-q:a", "0"])
            logger.info(f"Audio post-processed: {audio_path}")
        except Exception as e:
            logger.warning(f"Audio post-processing skipped: {e}")

    # ------------------------------------------------------------------
    # Word-timing estimation for viseme lip-sync
    # ------------------------------------------------------------------
    def _estimate_word_timings(self, text: str, total_duration_s: float) -> list:
        words = [w for w in re.findall(r'\S+', text) if w]
        if not words or total_duration_s <= 0:
            return []

        weights = [len(w) + 1 for w in words]
        total_weight = sum(weights)
        boundaries = []
        cursor_us = 0.0
        total_us = total_duration_s * 1_000_000
        for word, weight in zip(words, weights):
            dur_us = total_us * (weight / total_weight)
            boundaries.append({
                "text": word,
                "offset_us": cursor_us,
                "duration_us": dur_us,
            })
            cursor_us += dur_us
        return boundaries

    # ------------------------------------------------------------------
    # Core: synthesize one chunk via Gemini
    # ------------------------------------------------------------------
    def _synthesize_chunk_sync(self, text: str, voice_name: str) -> bytes:
        """
        Call Gemini TTS for a single chunk. Returns raw PCM bytes (24kHz, mono, 16-bit).
        Runs synchronously — Gemini genai SDK is sync-only.
        """
        from google.genai import types

        max_retries = 3
        backoff = 3
        last_err = None

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.MODEL,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=voice_name
                                )
                            )
                        ),
                    ),
                )

                # Extract audio data from response
                audio_data = response.candidates[0].content.parts[0].inline_data.data
                if audio_data:
                    return audio_data

                logger.warning(
                    f"Gemini returned empty audio (attempt {attempt+1})"
                )

            except Exception as e:
                last_err = e
                logger.warning(f"Gemini TTS error (attempt {attempt+1}): {e}")

            import time
            time.sleep(backoff)
            backoff *= 2

        raise RuntimeError(
            f"Gemini TTS failed after {max_retries} retries: {last_err}"
        )

    def _pcm_to_wav_bytes(self, pcm_data: bytes) -> bytes:
        """Convert raw PCM bytes to WAV format in memory."""
        import io
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)        # mono
            wf.setsampwidth(2)        # 16-bit
            wf.setframerate(24000)    # 24kHz
            wf.writeframes(pcm_data)
        buf.seek(0)
        return buf.read()

    # ------------------------------------------------------------------
    # Main synthesize entry point
    # ------------------------------------------------------------------
    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
        language: str = None,
    ) -> TTSResult:
        """
        Synthesize text via Gemini TTS. Automatically chunks long text.
        """
        language = language or self.default_language
        voice_name = (
            voice
            or self.voice_name_override
            or self.DEFAULT_VOICES.get(language, "Kore")
        )

        cleaned_text = self._preprocess_text(text)
        if not cleaned_text:
            return TTSResult(
                audio_path="", duration=0, text=text,
                voice=self._voice_info(voice_name, language),
                success=False, error="Empty text after preprocessing",
            )

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        chunks = self._split_text(cleaned_text)
        logger.info(
            f"Gemini TTS: {len(chunks)} chunk(s), {len(cleaned_text)} chars, "
            f"voice={voice_name}, lang={language}"
        )

        try:
            # Gemini genai SDK is synchronous, run in executor to not block
            loop = asyncio.get_event_loop()
            merged = None

            for i, chunk_text in enumerate(chunks):
                logger.info(f"  Chunk {i+1}/{len(chunks)}: {len(chunk_text)} chars")

                pcm_bytes = await loop.run_in_executor(
                    None, self._synthesize_chunk_sync, chunk_text, voice_name
                )

                # Convert PCM → WAV → AudioSegment
                wav_bytes = self._pcm_to_wav_bytes(pcm_bytes)
                import io
                segment = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
                merged = segment if merged is None else merged + segment

            # Export as mp3
            merged.export(
                str(output_path), format="mp3", bitrate="192k",
                parameters=["-q:a", "0"]
            )

            # Post-process
            self._postprocess_audio(str(output_path))

            duration = len(merged) / 1000.0
            logger.info(f"Gemini TTS complete: {duration:.1f}s, voice={voice_name}")

            # Estimated word timings for viseme lip-sync
            word_boundaries = self._estimate_word_timings(cleaned_text, duration)
            word_timing_path = None
            if word_boundaries:
                word_timing_path = str(
                    Path(output_path).with_suffix('.wordtiming.json')
                )
                with open(word_timing_path, 'w', encoding='utf-8') as f:
                    json.dump(word_boundaries, f)
                logger.info(
                    f"Word timing saved: {len(word_boundaries)} words → {word_timing_path}"
                )

            return TTSResult(
                audio_path=str(output_path),
                duration=duration,
                text=text,
                voice=self._voice_info(voice_name, language),
                success=True,
                word_timing_path=word_timing_path,
            )

        except Exception as e:
            logger.error(f"Gemini TTS failed: {e}")
            return TTSResult(
                audio_path="", duration=0, text=text,
                voice=self._voice_info(voice_name, language),
                success=False, error=str(e),
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _voice_info(self, voice_name: str, language: str) -> TTSVoice:
        return TTSVoice(
            id=f"gemini:{self.MODEL}:{voice_name}",
            name=f"{voice_name} ({self.MODEL})",
            language=language,
            language_code=f"{language}-IN",
            gender="unknown",
            provider="gemini",
        )

    async def list_voices(self, language: str = None) -> List[TTSVoice]:
        languages = [language] if language else list(self.DEFAULT_VOICES.keys())
        voices = []
        for lang in languages:
            if lang in self.DEFAULT_VOICES:
                voices.append(self._voice_info(self.DEFAULT_VOICES[lang], lang))
            if lang in self.FEMALE_VOICES:
                voices.append(self._voice_info(self.FEMALE_VOICES[lang], lang))
        return voices

    def get_default_voice(self, language: str) -> str:
        return self.DEFAULT_VOICES.get(language, "Kore")
