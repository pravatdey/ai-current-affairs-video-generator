"""
KDTalker HF Space Avatar Engine

Generates realistic talking head videos from a single photo + audio
using KDTalker via the free HuggingFace Space (fffiloni/KDTalker).

KDTalker produces natural head movements, expressions, and lip-sync
that look like a real person talking — not a frozen photo.

For long audio (>15s), splits into chunks, generates each via the
HF Space's free GPU, and concatenates with ffmpeg.

HF Space: https://huggingface.co/spaces/fffiloni/KDTalker
"""

import math
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class KDTalkerConfig:
    """Configuration for KDTalker HF Space generation."""
    hf_space_id: str = "fffiloni/KDTalker"

    # Chunking: 15s per chunk stays well within ZeroGPU limits
    # (~20s fixed overhead + ~3.5s/second of audio ≈ 72s GPU per chunk)
    max_chunk_seconds: float = 15.0

    # Retry settings for transient HF Space failures
    max_retries: int = 3
    retry_delay: int = 20   # seconds between retries

    # Delay between chunk submissions to avoid rate limiting
    inter_chunk_delay: float = 3.0


class KDTalkerEngine:
    """
    Generates talking head videos using KDTalker HF Space.

    Takes a single photo + audio and produces a video where the person
    naturally moves their head, blinks, changes expressions, and speaks.

    For long audio (>15s), splits into chunks, generates each,
    and concatenates with ffmpeg.
    """

    def __init__(self, config: KDTalkerConfig = None):
        self.config = config or KDTalkerConfig()
        logger.info(f"KDTalkerEngine initialized: space={self.config.hf_space_id}")

    def is_available(self) -> bool:
        """Check if gradio_client is installed."""
        try:
            from gradio_client import Client
            return True
        except ImportError:
            logger.debug("gradio_client not installed")
            return False

    def generate(
        self,
        audio_path: str,
        image_path: str,
        output_path: str,
    ) -> dict:
        """
        Generate a talking head video.

        Args:
            audio_path: Path to audio file (mp3/wav).
            image_path: Path to face photo (jpg/png).
            output_path: Where to save the output mp4.

        Returns:
            dict with keys: success, video_path, duration, error
        """
        if not self.is_available():
            return {
                "success": False, "video_path": "", "duration": 0,
                "error": "gradio_client not installed (pip install gradio_client)",
            }

        audio_duration = self._get_audio_duration(audio_path)
        if audio_duration <= 0:
            return {
                "success": False, "video_path": "", "duration": 0,
                "error": f"Could not determine audio duration: {audio_path}",
            }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"KDTalker: {audio_duration:.1f}s audio, "
            f"image={Path(image_path).name}"
        )

        if audio_duration <= self.config.max_chunk_seconds:
            return self._generate_single(audio_path, image_path, output_path)

        return self._generate_chunked(
            audio_path, image_path, output_path, audio_duration
        )

    def _generate_single(
        self,
        audio_path: str,
        image_path: str,
        output_path: str,
    ) -> dict:
        """Generate a single video clip via KDTalker HF Space."""
        try:
            from gradio_client import Client, handle_file

            logger.info(f"Connecting to KDTalker: {self.config.hf_space_id}")
            client = Client(self.config.hf_space_id)

            # Ensure audio is WAV (KDTalker works best with WAV)
            wav_audio = self._ensure_wav(audio_path)
            if not wav_audio:
                return {
                    "success": False, "video_path": "", "duration": 0,
                    "error": f"Failed to convert audio to WAV: {audio_path}",
                }

            logger.info("Submitting to KDTalker HF Space...")
            start_time = time.time()

            result = client.predict(
                source_image=handle_file(os.path.abspath(image_path)),
                driven_audio=handle_file(os.path.abspath(wav_audio)),
                api_name="/gradio_infer",
            )

            elapsed = time.time() - start_time
            logger.info(f"KDTalker completed in {elapsed:.0f}s")

            video_file = str(result) if result else None
            if not video_file or not Path(video_file).exists():
                return {
                    "success": False, "video_path": "", "duration": 0,
                    "error": f"KDTalker returned no video. Result: {result}",
                }

            shutil.copy2(video_file, output_path)
            duration = self._get_video_duration(output_path)
            logger.info(f"KDTalker video saved: {output_path} ({duration:.1f}s)")

            # Clean up temp WAV if we created one
            if wav_audio != audio_path and Path(wav_audio).exists():
                try:
                    Path(wav_audio).unlink()
                except Exception:
                    pass

            return {
                "success": True,
                "video_path": output_path,
                "duration": duration,
                "error": None,
            }

        except Exception as e:
            logger.error(f"KDTalker generation failed: {e}")
            return {
                "success": False, "video_path": "", "duration": 0,
                "error": f"KDTalker error: {e}",
            }

    def _generate_chunked(
        self,
        audio_path: str,
        image_path: str,
        output_path: str,
        total_duration: float,
    ) -> dict:
        """Split long audio into chunks, generate each, concatenate."""
        chunk_dur = self.config.max_chunk_seconds
        num_chunks = math.ceil(total_duration / chunk_dur)
        logger.info(
            f"KDTalker chunked: {total_duration:.0f}s audio -> "
            f"{num_chunks} chunks of {chunk_dur:.0f}s"
        )

        ffmpeg_exe = self._get_ffmpeg()
        chunk_dir = Path(output_path).parent / "kdtalker_chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)

        chunk_videos = []
        failed_chunks = 0

        for i in range(num_chunks):
            start = i * chunk_dur
            end = min(start + chunk_dur, total_duration)
            chunk_audio = str(chunk_dir / f"chunk_{i:03d}.wav")

            # Extract audio chunk with ffmpeg
            cmd = [
                ffmpeg_exe, "-y", "-i", audio_path,
                "-ss", str(start), "-to", str(end),
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                chunk_audio,
            ]
            subprocess.run(cmd, capture_output=True, timeout=60)

            if not Path(chunk_audio).exists():
                logger.warning(f"Failed to extract chunk {i}")
                failed_chunks += 1
                continue

            chunk_video = str(chunk_dir / f"chunk_{i:03d}.mp4")
            logger.info(
                f"  Chunk {i+1}/{num_chunks} "
                f"({start:.0f}s-{end:.0f}s)"
            )

            # Retry loop for transient failures
            result = None
            for attempt in range(1, self.config.max_retries + 1):
                result = self._generate_single(
                    chunk_audio, image_path, chunk_video
                )
                if result["success"]:
                    break
                logger.warning(
                    f"  Chunk {i+1} attempt {attempt} failed: {result['error']}"
                )
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay)

            if result and result["success"]:
                chunk_videos.append(chunk_video)
            else:
                logger.error(f"  Chunk {i+1} failed after {self.config.max_retries} retries")
                failed_chunks += 1

            # Small delay between chunks to avoid rate limiting
            if i < num_chunks - 1:
                time.sleep(self.config.inter_chunk_delay)

        if not chunk_videos:
            shutil.rmtree(chunk_dir, ignore_errors=True)
            return {
                "success": False, "video_path": "", "duration": 0,
                "error": f"All {num_chunks} chunks failed",
            }

        if failed_chunks > 0:
            logger.warning(
                f"KDTalker: {failed_chunks}/{num_chunks} chunks failed, "
                f"continuing with {len(chunk_videos)} successful chunks"
            )

        # Concatenate chunks with ffmpeg
        if len(chunk_videos) == 1:
            shutil.copy2(chunk_videos[0], output_path)
        else:
            concat_file = str(chunk_dir / "concat.txt")
            with open(concat_file, "w") as f:
                for v in chunk_videos:
                    # Use absolute paths for ffmpeg concat
                    f.write(f"file '{os.path.abspath(v)}'\n")

            cmd = [
                ffmpeg_exe, "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file, "-c", "copy", output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"FFmpeg concat failed: {result.stderr[:200]}")

        # Cleanup
        shutil.rmtree(chunk_dir, ignore_errors=True)

        if Path(output_path).exists():
            duration = self._get_video_duration(output_path)
            logger.info(
                f"KDTalker final video: {output_path} ({duration:.1f}s, "
                f"{len(chunk_videos)}/{num_chunks} chunks)"
            )
            return {
                "success": True,
                "video_path": output_path,
                "duration": duration,
                "error": None,
            }

        return {
            "success": False, "video_path": "", "duration": 0,
            "error": "FFmpeg concatenation failed",
        }

    def _ensure_wav(self, audio_path: str) -> Optional[str]:
        """Convert audio to WAV 16kHz mono if needed."""
        if audio_path.lower().endswith(".wav"):
            return audio_path

        wav_path = audio_path.rsplit(".", 1)[0] + "_kdtalker.wav"
        try:
            ffmpeg_exe = self._get_ffmpeg()
            cmd = [
                ffmpeg_exe, "-y", "-i", audio_path,
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                wav_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)
            return wav_path if Path(wav_path).exists() else None
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return None

    @staticmethod
    def _get_ffmpeg() -> str:
        """Get ffmpeg executable path."""
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            return "ffmpeg"

    @staticmethod
    def _get_audio_duration(path: str) -> float:
        """Get audio duration in seconds."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(path)
            return len(audio) / 1000.0
        except Exception:
            return 0.0

    @staticmethod
    def _get_video_duration(path: str) -> float:
        """Get video duration in seconds."""
        try:
            ffmpeg_exe = KDTalkerEngine._get_ffmpeg()
            ffprobe = ffmpeg_exe.replace("ffmpeg", "ffprobe")
            result = subprocess.run(
                [ffprobe, "-v", "quiet", "-show_entries",
                 "format=duration", "-of", "csv=p=0", path],
                capture_output=True, text=True, timeout=30,
            )
            return float(result.stdout.strip())
        except Exception:
            try:
                from pydub import AudioSegment
                # pydub can also read video duration for some formats
                return 0.0
            except Exception:
                return 0.0
