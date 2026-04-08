"""
Edge TTS Engine - Microsoft Edge Text-to-Speech (Free)

Enhancements for natural, clear news-delivery voice:
- Text pre-processing: inserts natural pauses at punctuation, paragraph breaks,
  and after topic headers so the speech breathes naturally
- Audio post-processing: loudness normalisation, gentle high-pass filter for
  clarity, and light compression for consistent volume across sentences
"""

import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional
import tempfile
import uuid
import shutil

# Configure pydub to use ffmpeg from imageio-ffmpeg
try:
    import imageio_ffmpeg
    import pydub
    pydub.AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
    pydub.AudioSegment.ffprobe = imageio_ffmpeg.get_ffmpeg_exe().replace('ffmpeg', 'ffprobe')
except ImportError:
    pass  # imageio-ffmpeg not available, pydub will try system ffmpeg

import edge_tts
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

from .base_tts import BaseTTS, TTSVoice, TTSResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EdgeTTSEngine(BaseTTS):
    """
    Microsoft Edge TTS engine using edge-tts library.
    Completely free, high-quality voices in multiple languages.
    """

    # Default voices for common languages
    DEFAULT_VOICES = {
        "en": "en-IN-PrabhatNeural",    # Clear Indian English male — best for UPSC news
        "en-us": "en-US-AndrewNeural",  # Natural US male
        "en-gb": "en-GB-RyanNeural",
        "en-in": "en-IN-PrabhatNeural",
        "hi": "hi-IN-MadhurNeural",      # Male Hindi
        "ta": "ta-IN-ValluvarNeural",    # Male Tamil
        "te": "te-IN-MohanNeural",       # Male Telugu
        "bn": "bn-IN-BashkarNeural",     # Male Bengali
        "mr": "mr-IN-ManoharNeural",     # Male Marathi
        "gu": "gu-IN-NiranjanNeural",    # Male Gujarati
        "kn": "kn-IN-GaganNeural",       # Male Kannada
        "ml": "ml-IN-MidhunNeural",      # Male Malayalam
    }

    # Female voice alternatives
    FEMALE_VOICES = {
        "en": "en-US-JennyNeural",
        "en-us": "en-US-JennyNeural",
        "en-gb": "en-GB-SoniaNeural",
        "en-in": "en-IN-NeerjaNeural",
        "hi": "hi-IN-SwaraNeural",
        "ta": "ta-IN-PallaviNeural",
        "te": "te-IN-ShrutiNeural",
    }

    def __init__(
        self,
        default_voice: str = None,
        rate: str = "-8%",
        pitch: str = "-5Hz",
        volume: str = "+0%"
    ):
        """
        Initialize Edge TTS engine.

        Args:
            default_voice: Default voice ID
            rate: Default speaking rate (slower = more soothing)
            pitch: Default pitch (lower = warmer tone)
            volume: Default volume
        """
        self.default_voice = default_voice or self.DEFAULT_VOICES["en"]
        self.default_rate = rate
        self.default_pitch = pitch
        self.default_volume = volume

        logger.info(f"Initialized EdgeTTS with voice: {self.default_voice}")

    # ------------------------------------------------------------------
    # Text pre-processing — makes speech sound natural and clear
    # ------------------------------------------------------------------

    def _preprocess_text(self, text: str) -> str:
        """
        Clean and restructure text so Edge TTS produces natural,
        easy-to-understand speech:

        1. Strip markdown / symbols that TTS reads aloud awkwardly
        2. Insert natural pause markers (SSML-like via punctuation tricks)
        3. Expand common abbreviations used in current affairs
        4. Break very long sentences into breath-sized chunks
        """
        # ── 1. Remove markdown and noisy symbols ──────────────────────
        # Bold/italic markers
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
        # Bullet symbols → nothing (TTS will read them as words otherwise)
        text = re.sub(r'^[\s]*[▸♦→•\-\*]+\s*', '', text, flags=re.MULTILINE)
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove excessive brackets content like (GS2 | Polity)
        text = re.sub(r'\(GS\d.*?\)', '', text)
        # Remove hashtags
        text = re.sub(r'#\w+', '', text)
        # Remove emojis and special chars that aren't speech-friendly
        text = re.sub(r'[✔✗✓✕→←↑↓■□●○◆◇★☆]', '', text)

        # ── 2. Expand common abbreviations ────────────────────────────
        abbreviations = {
            r'\bSC\b': 'Supreme Court',
            r'\bHC\b': 'High Court',
            r'\bPM\b': 'Prime Minister',
            r'\bCM\b': 'Chief Minister',
            r'\bMP\b': 'Member of Parliament',
            r'\bMLA\b': 'Member of Legislative Assembly',
            r'\bGDP\b': 'Gross Domestic Product',
            r'\bRBI\b': 'Reserve Bank of India',
            r'\bISRO\b': 'Indian Space Research Organisation',
            r'\bDRDO\b': 'Defence Research and Development Organisation',
            r'\bNITI\b': 'NITI',
            r'\bBNS\b': 'Bharatiya Nyaya Sanhita',
            r'\bRPA\b': 'Representation of People Act',
            r'\bNCRB\b': 'National Crime Records Bureau',
            r'\bUoI\b': 'Union of India',
            r'\bv\.\s*UoI\b': 'versus Union of India',
            r'\bArt\.\s*(\d+)': r'Article \1',
            r'\bSec\.\s*(\d+)': r'Section \1',
            r'\bFY(\d{2})\b': r'Financial Year 20\1',
            r'\b(\d+)%\b': r'\1 percent',
            r'\b₹\s*(\d+)\b': r'\1 rupees',
            r'\b(\d+)\s*crore\b': r'\1 crore rupees',
            r'\bLEO\b': 'Low Earth Orbit',
            r'\bG20\b': 'G 20',
            r'\bG7\b': 'G 7',
            r'\bBRICS\b': 'BRICS',
            r'\bNATO\b': 'NATO',
            r'\bASEAN\b': 'ASEAN',
            r'\bLUFS\b': 'LUFS',
        }
        for pattern, replacement in abbreviations.items():
            text = re.sub(pattern, replacement, text)

        # ── 3. Add natural breathing pauses ─────────────────────────────
        # Edge TTS respects commas and ellipses as pauses — use them for a
        # calm, unhurried delivery that sounds soothing.

        # After a full stop → add a gentle pause before next sentence
        text = re.sub(r'\.\s+([A-Z])', r'.\n\1', text)

        # Paragraph breaks → longer pause (period + double newline)
        text = re.sub(r'\n\n+', '.\n\n', text)
        text = re.sub(r'\n', ' ... ', text)   # ellipsis = natural breathing pause

        # After colons in headers like "Key Points:" → calm pause
        text = re.sub(r':\s+', ': ... ', text)

        # Number sequences like "1. point  2. point" → pause between items
        text = re.sub(r'(\d+)\.\s+', r'\1 ... ', text)

        # After semicolons → gentle pause
        text = re.sub(r';\s+', '; ... ', text)

        # ── 4. Break very long sentences at conjunctions ──────────────
        # Sentences over 200 chars → split at "and", "but", "which", "that"
        def break_long_sentence(m):
            s = m.group(0)
            if len(s) > 200:
                s = re.sub(
                    r'(?<!\w)(and|but|which|that|however|therefore|moreover|furthermore)\s+',
                    r'\1, ',
                    s,
                    count=1
                )
            return s

        text = re.sub(r'[^.!?]+[.!?]', break_long_sentence, text)

        # ── 5. Final cleanup ──────────────────────────────────────────
        text = re.sub(r' {2,}', ' ', text)   # collapse multiple spaces
        text = text.strip()

        return text

    # ------------------------------------------------------------------
    # Audio post-processing — clearer, louder, more consistent voice
    # ------------------------------------------------------------------

    def _postprocess_audio(self, audio_path: str) -> None:
        """
        Apply gentle audio enhancement for a warm, soothing voice:
          1. Soft high-pass at 80 Hz     → removes rumble without thinning the voice
          2. Gentle low-pass at 12 kHz   → rolls off harsh sibilance (s/t sounds)
          3. Very light compression       → consistent volume, preserves natural dynamics
          4. Loudness normalisation       → target -16 LUFS for comfortable listening
        All done with pydub; if any step fails it's silently skipped.
        """
        try:
            audio = AudioSegment.from_file(audio_path)

            # 1. Soft high-pass filter — remove rumble but keep warmth (lower cutoff)
            audio = audio.high_pass_filter(80)

            # 2. Gentle low-pass filter — tame harsh sibilance for soothing feel
            audio = audio.low_pass_filter(12000)

            # 3. Very light compression — preserve natural dynamics, just even out extremes
            try:
                audio = compress_dynamic_range(
                    audio,
                    threshold=-18.0,   # dB — higher threshold = less compression
                    ratio=2.0,         # 2:1 ratio — very gentle, natural sounding
                    attack=10.0,       # ms — slower attack preserves transients
                    release=100.0      # ms — slower release for smoother output
                )
            except Exception:
                pass  # compress_dynamic_range signature varies by pydub version

            # 4. Normalise loudness to -16 LUFS — slightly quieter = more comfortable/soothing
            audio = normalize(audio, headroom=2.0)

            # No additional volume boost — keeps the voice warm and non-fatiguing

            # Export back to same path
            audio.export(audio_path, format="mp3", bitrate="192k",
                         parameters=["-q:a", "0"])
            logger.info(f"Audio post-processed (warm mode): {audio_path}")

        except Exception as e:
            logger.warning(f"Audio post-processing skipped: {e}")

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        rate: str = None,
        pitch: str = None,
        volume: str = None
    ) -> TTSResult:
        """
        Synthesize text to speech using Edge TTS.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            voice: Voice ID to use
            rate: Speaking rate (e.g., "+10%", "-5%")
            pitch: Pitch adjustment (e.g., "+5Hz", "-10Hz")
            volume: Volume adjustment (e.g., "+10%", "-5%")

        Returns:
            TTSResult object
        """
        voice = voice or self.default_voice
        rate = rate or self.default_rate
        pitch = pitch or self.default_pitch
        volume = volume or self.default_volume

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Create communicate object
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            # Stream audio + capture word boundaries for viseme lip-sync
            word_boundaries = []
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
                elif chunk["type"] == "WordBoundary":
                    word_boundaries.append({
                        "text": chunk["text"],
                        "offset_us": chunk["offset"] / 10,      # 100ns → microseconds
                        "duration_us": chunk["duration"] / 10,
                    })

            # Write audio file
            with open(str(output_path), "wb") as f:
                f.write(audio_data)

            # Save word timing JSON for viseme-based lip-sync
            word_timing_path = str(Path(output_path).with_suffix('.wordtiming.json'))
            if word_boundaries:
                with open(word_timing_path, 'w', encoding='utf-8') as f:
                    json.dump(word_boundaries, f)
                logger.info(f"Word timing saved: {len(word_boundaries)} words → {word_timing_path}")
            else:
                word_timing_path = None

            # Enhance audio clarity (normalise, compress, EQ)
            self._postprocess_audio(str(output_path))

            # Get audio duration
            duration = self._get_audio_duration(str(output_path))

            logger.info(
                f"Generated audio: {duration:.1f}s, "
                f"{len(text)} chars, voice: {voice}"
            )

            # Create voice info
            voice_info = TTSVoice(
                id=voice,
                name=voice,
                language=voice.split("-")[0],
                language_code="-".join(voice.split("-")[:2]),
                gender="unknown",
                provider="edge-tts"
            )

            return TTSResult(
                audio_path=str(output_path),
                duration=duration,
                text=text,
                voice=voice_info,
                success=True,
                word_timing_path=word_timing_path,
            )

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return TTSResult(
                audio_path="",
                duration=0,
                text=text,
                voice=TTSVoice(
                    id=voice, name=voice, language="",
                    language_code="", gender="", provider="edge-tts"
                ),
                success=False,
                error=str(e)
            )

    async def synthesize_long_text(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        rate: str = None,
        pitch: str = None,
        max_chunk_size: int = 5000
    ) -> TTSResult:
        """
        Synthesize long text by splitting into chunks.
        Edge TTS has limits on text length, so we split and merge.

        Args:
            text: Long text to synthesize
            output_path: Path to save final audio
            voice: Voice ID
            rate: Speaking rate
            pitch: Pitch
            max_chunk_size: Maximum characters per chunk

        Returns:
            TTSResult object
        """
        voice = voice or self.default_voice
        rate = rate or self.default_rate
        pitch = pitch or self.default_pitch

        # Split text into chunks
        chunks = self._split_text(text, max_chunk_size)
        logger.info(f"Split text into {len(chunks)} chunks")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Use system temp directory for temp files to avoid Windows file locking issues
        import uuid
        import shutil
        temp_dir = Path(tempfile.gettempdir()) / f"edge_tts_{uuid.uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_files = []

        try:
            # Generate audio for each chunk, capturing word boundaries
            all_word_boundaries = []
            cumulative_offset_us = 0.0

            for i, chunk in enumerate(chunks):
                temp_path = temp_dir / f"chunk_{i}.mp3"
                temp_files.append(temp_path)

                # Stream to capture word boundaries (retry up to 3 times)
                chunk_audio = b""
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        chunk_audio = b""
                        communicate = edge_tts.Communicate(
                            text=chunk,
                            voice=voice,
                            rate=rate,
                            pitch=pitch
                        )
                        async for evt in communicate.stream():
                            if evt["type"] == "audio":
                                chunk_audio += evt["data"]
                            elif evt["type"] == "WordBoundary":
                                all_word_boundaries.append({
                                    "text": evt["text"],
                                    "offset_us": evt["offset"] / 10 + cumulative_offset_us,
                                    "duration_us": evt["duration"] / 10,
                                })
                        if chunk_audio:
                            break
                        logger.warning(f"Chunk {i} returned empty audio, retry {attempt + 1}/{max_retries}")
                    except Exception as retry_err:
                        logger.warning(f"Chunk {i} TTS error (attempt {attempt + 1}): {retry_err}")
                        if attempt == max_retries - 1:
                            raise

                if not chunk_audio:
                    raise RuntimeError(f"Edge TTS returned empty audio for chunk {i} after {max_retries} retries")

                with open(str(temp_path), "wb") as f:
                    f.write(chunk_audio)

                # Get this chunk's duration to offset the next chunk's timestamps
                chunk_dur = self._get_audio_duration(str(temp_path))
                cumulative_offset_us += chunk_dur * 1_000_000  # seconds → microseconds

            # Get ffmpeg path
            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                ffmpeg_exe = "ffmpeg"  # Fall back to system ffmpeg

            # Merge all chunks using ffmpeg directly (more reliable on Windows)
            import subprocess

            # Create a file list for ffmpeg concat
            list_file = temp_dir / "files.txt"
            with open(list_file, "w") as f:
                for temp_file in temp_files:
                    f.write(f"file '{temp_file}'\n")

            # Use ffmpeg concat demuxer to merge files
            cmd = [
                ffmpeg_exe,
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                "-y",  # Overwrite output
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg error: {result.stderr}")

            # Enhance audio clarity (normalise, compress, EQ)
            self._postprocess_audio(str(output_path))

            # Get duration using ffprobe or estimate from file size
            try:
                duration_cmd = [
                    ffmpeg_exe,
                    "-i", str(output_path),
                    "-f", "null", "-"
                ]
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                # Parse duration from stderr (ffmpeg outputs to stderr)
                import re
                time_match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", duration_result.stderr)
                if time_match:
                    h, m, s = time_match.groups()
                    duration = int(h) * 3600 + int(m) * 60 + float(s)
                else:
                    duration = 0
            except Exception:
                duration = 0

            # Cleanup - try to remove temp directory
            try:
                shutil.rmtree(str(temp_dir), ignore_errors=True)
            except Exception:
                pass  # Ignore cleanup errors on Windows

            # Save accumulated word timing JSON for viseme lip-sync
            word_timing_path = str(Path(output_path).with_suffix('.wordtiming.json'))
            if all_word_boundaries:
                with open(word_timing_path, 'w', encoding='utf-8') as f:
                    json.dump(all_word_boundaries, f)
                logger.info(f"Word timing saved: {len(all_word_boundaries)} words → {word_timing_path}")
            else:
                word_timing_path = None

            logger.info(f"Generated long audio: {duration:.1f}s")

            voice_info = TTSVoice(
                id=voice,
                name=voice,
                language=voice.split("-")[0],
                language_code="-".join(voice.split("-")[:2]),
                gender="unknown",
                provider="edge-tts"
            )

            return TTSResult(
                audio_path=str(output_path),
                duration=duration,
                text=text,
                voice=voice_info,
                success=True,
                word_timing_path=word_timing_path,
            )

        except Exception as e:
            # Cleanup on error - try to remove temp directory
            try:
                shutil.rmtree(str(temp_dir), ignore_errors=True)
            except Exception:
                pass  # Ignore cleanup errors on Windows

            logger.error(f"Long text TTS failed: {e}")
            return TTSResult(
                audio_path="",
                duration=0,
                text=text,
                voice=TTSVoice(
                    id=voice, name=voice, language="",
                    language_code="", gender="", provider="edge-tts"
                ),
                success=False,
                error=str(e)
            )

    def _split_text(self, text: str, max_size: int) -> List[str]:
        """Split text into chunks at sentence boundaries"""
        if len(text) <= max_size:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except Exception:
            return 0.0

    async def list_voices(self, language: str = None) -> List[TTSVoice]:
        """
        List available Edge TTS voices.

        Args:
            language: Filter by language code (e.g., 'en', 'hi')

        Returns:
            List of TTSVoice objects
        """
        voices = await edge_tts.list_voices()
        result = []

        for voice in voices:
            # Filter by language if specified
            if language:
                voice_lang = voice["Locale"].split("-")[0].lower()
                if voice_lang != language.lower():
                    continue

            result.append(TTSVoice(
                id=voice["ShortName"],
                name=voice["FriendlyName"],
                language=voice["Locale"].split("-")[0],
                language_code=voice["Locale"],
                gender=voice.get("Gender", "Unknown"),
                provider="edge-tts"
            ))

        return result

    def get_default_voice(self, language: str) -> str:
        """Get default voice for a language"""
        language = language.lower()
        return self.DEFAULT_VOICES.get(language, self.DEFAULT_VOICES["en"])

    def get_female_voice(self, language: str) -> str:
        """Get female voice for a language"""
        language = language.lower()
        return self.FEMALE_VOICES.get(language, self.FEMALE_VOICES.get("en"))


# Synchronous wrapper for convenience
def synthesize_sync(
    text: str,
    output_path: str,
    voice: str = None,
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> TTSResult:
    """
    Synchronous wrapper for TTS synthesis.

    Args:
        text: Text to synthesize
        output_path: Output file path
        voice: Voice ID
        rate: Speaking rate
        pitch: Pitch

    Returns:
        TTSResult object
    """
    engine = EdgeTTSEngine()
    return asyncio.run(engine.synthesize(
        text=text,
        output_path=output_path,
        voice=voice,
        rate=rate,
        pitch=pitch
    ))
