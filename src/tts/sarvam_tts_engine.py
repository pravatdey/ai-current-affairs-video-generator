"""
Sarvam AI TTS Engine — Realistic Indian Hindi (and other Indic) voices

Uses Sarvam's `bulbul:v3` model via their REST API. Free tier on sarvam.ai
gives ~1000 requests/month, and v3 accepts up to 2500 chars per request,
which is ~5 requests per 15-min video → ~200 videos/month of headroom.

Requires SARVAM_API_KEY in .env (free key at https://dashboard.sarvam.ai/).
"""

import asyncio
import base64
import json
import os
import re
from pathlib import Path
from typing import List, Optional

import aiohttp

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


class SarvamTTSEngine(BaseTTS):
    """
    TTS engine powered by Sarvam AI's bulbul:v3 model.
    Realistic, Indian-native voices for Hindi, English-India, and 10+ Indic languages.
    """

    API_URL = "https://api.sarvam.ai/text-to-speech"
    MODEL = "bulbul:v3"
    MAX_CHARS_PER_REQUEST = 2500  # bulbul:v3 limit

    # Map short language code → Sarvam BCP-47 code
    LANGUAGE_MAP = {
        "hi": "hi-IN",
        "en": "en-IN",
        "ta": "ta-IN",
        "te": "te-IN",
        "bn": "bn-IN",
        "gu": "gu-IN",
        "kn": "kn-IN",
        "ml": "ml-IN",
        "mr": "mr-IN",
        "od": "od-IN",
        "pa": "pa-IN",
    }

    # Default male news-anchor voices per language (bulbul:v3 speakers)
    DEFAULT_SPEAKERS = {
        "hi": "aditya",    # Clear confident male Hindi news voice
        "en": "aditya",    # Works for Indian English too
        "ta": "aditya",
        "te": "aditya",
        "bn": "aditya",
    }

    # Female alternatives
    FEMALE_SPEAKERS = {
        "hi": "priya",
        "en": "priya",
        "ta": "priya",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_language: str = "hi",
        speaker: Optional[str] = None,
        pace: float = 1.0,
        temperature: float = 0.6,
        sample_rate: int = 24000,
        timeout: int = 120,
    ):
        """
        Args:
            api_key: Sarvam API key. Falls back to SARVAM_API_KEY env var.
            default_language: Default language code (e.g. "hi").
            speaker: Override the default speaker name for the language.
            pace: Speaking pace (0.5-2.0). 1.0 = normal, <1 = slower, >1 = faster.
            temperature: Voice randomness (0.01-2.0). Lower = more consistent.
            sample_rate: Output sample rate in Hz.
            timeout: HTTP request timeout (seconds).
        """
        self.api_key = api_key or os.getenv("SARVAM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SARVAM_API_KEY not set. Get a free key at "
                "https://dashboard.sarvam.ai/ and add it to .env as SARVAM_API_KEY=..."
            )

        self.default_language = default_language
        self.default_speaker_override = speaker
        self.default_pace = pace
        self.default_temperature = temperature
        self.sample_rate = sample_rate
        self.timeout = timeout

        logger.info(
            f"Initialized SarvamTTSEngine: model={self.MODEL}, "
            f"language={default_language}, pace={pace}"
        )

    # ------------------------------------------------------------------
    # Text pre-processing
    # ------------------------------------------------------------------
    def _preprocess_text(self, text: str) -> str:
        """Strip markdown/symbols that would be read literally."""
        # Remove markdown formatting
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
        text = re.sub(r'`([^`]*)`', r'\1', text)
        # Remove bullet symbols at line start
        text = re.sub(r'^[\s]*[▸♦→•\-\*]+\s*', '', text, flags=re.MULTILINE)
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove bracketed UPSC tags like (GS2 | Polity)
        text = re.sub(r'\(GS\d[^)]*\)', '', text)
        # Remove hashtags
        text = re.sub(r'#\w+', '', text)
        # Remove emoji-like symbols
        text = re.sub(r'[✔✗✓✕→←↑↓■□●○◆◇★☆]', '', text)
        # Collapse whitespace
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _split_for_sarvam(self, text: str) -> List[str]:
        """
        Split text into ≤ MAX_CHARS_PER_REQUEST chunks at sentence boundaries.
        Prefers to break on sentence endings, falls back to word boundaries.
        """
        if len(text) <= self.MAX_CHARS_PER_REQUEST:
            return [text]

        chunks = []
        current = ""
        # Split on sentence endings (Hindi ।, English . ! ?)
        sentences = re.split(r'(?<=[.!?।])\s+', text)

        for sentence in sentences:
            # If single sentence is itself too long, hard-split at max size
            if len(sentence) > self.MAX_CHARS_PER_REQUEST:
                if current:
                    chunks.append(current.strip())
                    current = ""
                # Split long sentence at word boundaries
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
    # Audio post-processing (matches Edge TTS engine for consistency)
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
    # Sarvam doesn't expose word boundaries, so we estimate proportionally.
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
    # Main synthesize entry point
    # ------------------------------------------------------------------
    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        rate: str = "+0%",    # accepted for API compatibility
        pitch: str = "+0Hz",  # accepted for API compatibility (v3 doesn't use pitch)
        volume: str = "+0%",  # accepted for API compatibility
        language: str = None,
    ) -> TTSResult:
        """
        Synthesize text via Sarvam API. Automatically chunks long text.

        Args:
            text: Text to synthesize.
            output_path: Destination mp3 path.
            voice: Optional explicit Sarvam speaker name (overrides default).
            language: Language code (e.g. "hi").
        """
        language = language or self.default_language
        sarvam_lang = self.LANGUAGE_MAP.get(language, "hi-IN")
        speaker = (
            voice
            or self.default_speaker_override
            or self.DEFAULT_SPEAKERS.get(language, "aditya")
        )

        cleaned_text = self._preprocess_text(text)
        if not cleaned_text:
            return TTSResult(
                audio_path="", duration=0, text=text,
                voice=self._voice_info(speaker, language),
                success=False, error="Empty text after preprocessing",
            )

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        chunks = self._split_for_sarvam(cleaned_text)
        logger.info(
            f"Sarvam TTS: {len(chunks)} chunk(s), {len(cleaned_text)} chars, "
            f"speaker={speaker}, lang={sarvam_lang}"
        )

        try:
            # Synthesize each chunk, collect audio bytes
            chunk_audios = []
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                for i, chunk_text in enumerate(chunks):
                    logger.info(
                        f"  Chunk {i+1}/{len(chunks)}: {len(chunk_text)} chars"
                    )
                    audio_bytes = await self._synthesize_chunk(
                        session, chunk_text, sarvam_lang, speaker
                    )
                    chunk_audios.append(audio_bytes)

            # Merge chunks via pydub
            merged = None
            for audio_bytes in chunk_audios:
                # Sarvam returns base64-encoded WAV by default
                segment = AudioSegment.from_file(
                    self._bytes_io(audio_bytes), format="wav"
                )
                merged = segment if merged is None else merged + segment

            # Export as mp3
            merged.export(
                str(output_path), format="mp3", bitrate="192k",
                parameters=["-q:a", "0"]
            )

            # Post-process (EQ + normalize)
            self._postprocess_audio(str(output_path))

            duration = len(merged) / 1000.0
            logger.info(
                f"Sarvam TTS complete: {duration:.1f}s, speaker={speaker}"
            )

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
                voice=self._voice_info(speaker, language),
                success=True,
                word_timing_path=word_timing_path,
            )

        except Exception as e:
            logger.error(f"Sarvam TTS failed: {e}")
            return TTSResult(
                audio_path="", duration=0, text=text,
                voice=self._voice_info(speaker, language),
                success=False, error=str(e),
            )

    async def _synthesize_chunk(
        self,
        session: aiohttp.ClientSession,
        text: str,
        target_language_code: str,
        speaker: str,
    ) -> bytes:
        """POST one chunk to Sarvam, return raw WAV bytes."""
        payload = {
            "text": text,
            "target_language_code": target_language_code,
            "model": self.MODEL,
            "speaker": speaker,
            "pace": self.default_pace,
            "temperature": self.default_temperature,
            "speech_sample_rate": self.sample_rate,
        }
        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": self.api_key,
        }

        max_retries = 3
        backoff = 3
        last_err = None

        for attempt in range(max_retries):
            try:
                async with session.post(
                    self.API_URL, json=payload, headers=headers
                ) as resp:
                    body_text = await resp.text()
                    if resp.status == 200:
                        data = json.loads(body_text)
                        # Sarvam returns {"audios": ["<base64 wav>", ...], "request_id": ...}
                        audios = data.get("audios", [])
                        if not audios:
                            raise RuntimeError(
                                f"Sarvam returned empty audios: {body_text[:200]}"
                            )
                        # Concatenate multiple base64 audio pieces if present
                        combined = b""
                        for b64 in audios:
                            combined += base64.b64decode(b64)
                        return combined

                    if resp.status == 429:
                        logger.warning(
                            f"Sarvam rate limit (attempt {attempt+1}), "
                            f"retrying in {backoff}s"
                        )
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    if resp.status >= 500:
                        logger.warning(
                            f"Sarvam {resp.status} (attempt {attempt+1}), "
                            f"retrying in {backoff}s: {body_text[:200]}"
                        )
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    # 4xx (non-429) — don't retry, surface error
                    raise RuntimeError(
                        f"Sarvam API returned {resp.status}: {body_text[:300]}"
                    )

            except asyncio.TimeoutError as e:
                last_err = e
                logger.warning(f"Sarvam timeout (attempt {attempt+1})")
                await asyncio.sleep(backoff)
                backoff *= 2
            except aiohttp.ClientError as e:
                last_err = e
                logger.warning(f"Sarvam client error: {e} (attempt {attempt+1})")
                await asyncio.sleep(backoff)
                backoff *= 2

        raise RuntimeError(
            f"Sarvam API failed after {max_retries} retries: {last_err}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _bytes_io(data: bytes):
        import io
        return io.BytesIO(data)

    def _voice_info(self, speaker: str, language: str) -> TTSVoice:
        return TTSVoice(
            id=f"sarvam:{self.MODEL}:{speaker}",
            name=f"{speaker} ({self.MODEL})",
            language=language,
            language_code=self.LANGUAGE_MAP.get(language, f"{language}-IN"),
            gender="unknown",
            provider="sarvam",
        )

    async def list_voices(self, language: str = None) -> List[TTSVoice]:
        languages = [language] if language else list(self.DEFAULT_SPEAKERS.keys())
        voices = []
        for lang in languages:
            if lang in self.DEFAULT_SPEAKERS:
                voices.append(self._voice_info(self.DEFAULT_SPEAKERS[lang], lang))
            if lang in self.FEMALE_SPEAKERS:
                voices.append(self._voice_info(self.FEMALE_SPEAKERS[lang], lang))
        return voices

    def get_default_voice(self, language: str) -> str:
        return self.DEFAULT_SPEAKERS.get(language, "aditya")
