"""
Avatar Video Generator - Creates talking head videos from image + audio

Supports:
- SadTalker (realistic lip sync + head movements)
- Wav2Lip (precise lip sync)
- Simple fallback (image + audio overlay)
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import tempfile

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AvatarResult:
    """Result of avatar video generation"""
    success: bool
    video_path: str
    duration: float
    method: str
    error: Optional[str] = None


class AvatarGenerator:
    """
    Generates talking head videos from a still image and audio.

    Supports multiple methods:
    1. SadTalker - Best quality, realistic head movements
    2. Wav2Lip - Good lip sync, less head movement
    3. Simple - Static image with audio (fallback)
    """

    def __init__(
        self,
        method: str = "auto",
        avatar_image: str = None,
        sadtalker_path: str = None,
        wav2lip_path: str = None
    ):
        """
        Initialize avatar generator.

        Args:
            method: Generation method ("sadtalker", "wav2lip", "simple", "auto")
            avatar_image: Path to default avatar image
            sadtalker_path: Path to SadTalker installation
            wav2lip_path: Path to Wav2Lip installation
        """
        self.method = method
        self.avatar_image = avatar_image or "assets/avatars/news_anchor.png"
        self.sadtalker_path = sadtalker_path or os.getenv("SADTALKER_PATH", "")
        self.wav2lip_path = wav2lip_path or os.getenv("WAV2LIP_PATH", "")

        # Detect available methods
        self.available_methods = self._detect_methods()

        # Select best available method if auto
        if method == "auto":
            self.method = self._select_best_method()

        # Mouth region for the default avatar (set when avatar is created)
        self._default_mouth_region = None

        logger.info(f"AvatarGenerator initialized: method={self.method}, available={self.available_methods}")

    def _detect_methods(self) -> list:
        """Detect which generation methods are available"""
        available = ["simple"]  # Always available

        # Check for SadTalker
        if self._check_sadtalker():
            available.append("sadtalker")

        # Check for Wav2Lip
        if self._check_wav2lip():
            available.append("wav2lip")

        return available

    def _check_sadtalker(self) -> bool:
        """Check if SadTalker is available"""
        if self.sadtalker_path and Path(self.sadtalker_path).exists():
            inference_script = Path(self.sadtalker_path) / "inference.py"
            return inference_script.exists()

        # Try to import as package
        try:
            import sadtalker
            return True
        except ImportError:
            pass

        return False

    def _check_wav2lip(self) -> bool:
        """Check if Wav2Lip is available"""
        if self.wav2lip_path and Path(self.wav2lip_path).exists():
            inference_script = Path(self.wav2lip_path) / "inference.py"
            return inference_script.exists()

        return False

    def _select_best_method(self) -> str:
        """Select the best available method"""
        if "sadtalker" in self.available_methods:
            return "sadtalker"
        elif "wav2lip" in self.available_methods:
            return "wav2lip"
        return "simple"

    def generate(
        self,
        audio_path: str,
        output_path: str,
        avatar_image: str = None,
        method: str = None
    ) -> AvatarResult:
        """
        Generate talking head video from audio.

        Args:
            audio_path: Path to input audio file
            output_path: Path to save output video
            avatar_image: Path to avatar image (uses default if not provided)
            method: Override generation method

        Returns:
            AvatarResult object
        """
        method = method or self.method
        avatar_image = avatar_image or self.avatar_image

        # Validate inputs
        if not Path(audio_path).exists():
            return AvatarResult(
                success=False,
                video_path="",
                duration=0,
                method=method,
                error=f"Audio file not found: {audio_path}"
            )

        if not Path(avatar_image).exists():
            # Try to create a default avatar
            avatar_image = self._create_default_avatar()
            if not avatar_image:
                return AvatarResult(
                    success=False,
                    video_path="",
                    duration=0,
                    method=method,
                    error="Avatar image not found and couldn't create default"
                )

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating avatar video: method={method}")

        # Generate based on method
        if method == "sadtalker" and "sadtalker" in self.available_methods:
            return self._generate_sadtalker(audio_path, output_path, avatar_image)
        elif method == "wav2lip" and "wav2lip" in self.available_methods:
            return self._generate_wav2lip(audio_path, output_path, avatar_image)
        else:
            return self._generate_simple(audio_path, output_path, avatar_image)

    def _generate_sadtalker(
        self,
        audio_path: str,
        output_path: str,
        avatar_image: str
    ) -> AvatarResult:
        """Generate video using SadTalker"""
        try:
            # SadTalker command
            cmd = [
                "python",
                str(Path(self.sadtalker_path) / "inference.py"),
                "--driven_audio", audio_path,
                "--source_image", avatar_image,
                "--result_dir", str(Path(output_path).parent),
                "--still",  # Less head movement for news style
                "--preprocess", "crop",
                "--enhancer", "gfpgan"  # Face enhancement
            ]

            logger.info(f"Running SadTalker: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.sadtalker_path
            )

            if result.returncode != 0:
                raise Exception(f"SadTalker failed: {result.stderr}")

            # Find output file (SadTalker generates with timestamp)
            output_dir = Path(output_path).parent
            generated_files = list(output_dir.glob("*.mp4"))
            if generated_files:
                # Move to expected output path
                latest_file = max(generated_files, key=lambda p: p.stat().st_mtime)
                shutil.move(str(latest_file), output_path)

            duration = self._get_video_duration(output_path)

            return AvatarResult(
                success=True,
                video_path=output_path,
                duration=duration,
                method="sadtalker"
            )

        except Exception as e:
            logger.error(f"SadTalker generation failed: {e}")
            # Fallback to simple method
            logger.info("Falling back to simple method")
            return self._generate_simple(audio_path, output_path, avatar_image)

    def _generate_wav2lip(
        self,
        audio_path: str,
        output_path: str,
        avatar_image: str
    ) -> AvatarResult:
        """Generate video using Wav2Lip"""
        try:
            # First, create a static video from image
            temp_video = Path(output_path).parent / "temp_static.mp4"

            # Get audio duration
            audio_duration = self._get_audio_duration(audio_path)

            # Create static video
            self._create_static_video(avatar_image, str(temp_video), audio_duration)

            # Wav2Lip command
            cmd = [
                "python",
                str(Path(self.wav2lip_path) / "inference.py"),
                "--checkpoint_path", str(Path(self.wav2lip_path) / "checkpoints/wav2lip_gan.pth"),
                "--face", str(temp_video),
                "--audio", audio_path,
                "--outfile", output_path,
                "--resize_factor", "1",
                "--nosmooth"
            ]

            logger.info(f"Running Wav2Lip: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.wav2lip_path
            )

            # Cleanup temp file
            temp_video.unlink(missing_ok=True)

            if result.returncode != 0:
                raise Exception(f"Wav2Lip failed: {result.stderr}")

            duration = self._get_video_duration(output_path)

            return AvatarResult(
                success=True,
                video_path=output_path,
                duration=duration,
                method="wav2lip"
            )

        except Exception as e:
            logger.error(f"Wav2Lip generation failed: {e}")
            # Fallback to simple method
            return self._generate_simple(audio_path, output_path, avatar_image)

    def _generate_simple(
        self,
        audio_path: str,
        output_path: str,
        avatar_image: str
    ) -> AvatarResult:
        """
        Generate lip-sync animated avatar video.

        Analyses per-frame audio amplitude and drives mouth open/close animation
        so the avatar appears to speak in sync with the audio.
        Also applies subtle breathing brightness variation for a lifelike feel.
        """
        try:
            from moviepy.video.VideoClip import VideoClip
            from moviepy.editor import AudioFileClip
            from PIL import Image, ImageDraw
            import numpy as np
            import math

            logger.info("Generating lip-sync animated avatar video")

            # ── Audio ────────────────────────────────────────────────────────
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            fps = 30

            # Per-frame amplitude values in [0, 1] — used to drive mouth open
            amplitudes = self._extract_audio_amplitude(audio_path, fps, duration)
            logger.info(f"Lip-sync: extracted {len(amplitudes)} amplitude frames")

            # ── Avatar image ─────────────────────────────────────────────────
            pil_image = Image.open(avatar_image).convert('RGB')

            # Resize to 720 p, preserving aspect ratio, even width
            target_height = 720
            aspect_ratio = pil_image.width / pil_image.height
            target_width = int(target_height * aspect_ratio)
            target_width = target_width if target_width % 2 == 0 else target_width + 1
            pil_image = pil_image.resize((target_width, target_height), Image.LANCZOS)

            # ── Mouth detection ──────────────────────────────────────────────
            mouth_region = self._get_mouth_region(pil_image, avatar_image)
            logger.info(f"Mouth region ({mouth_region['method']}): "
                        f"cx={mouth_region['cx']} cy={mouth_region['cy']} "
                        f"w={mouth_region['w']} h={mouth_region['h']}")

            # Frozen base frame (numpy) — we copy & paint over each frame
            base_array = np.array(pil_image)

            # ── Frame generator ──────────────────────────────────────────────
            def make_frame(t):
                # --- amplitude for this timestamp ---
                frame_idx = min(int(t * fps), len(amplitudes) - 1)
                amplitude = float(amplitudes[frame_idx])

                # Subtle breathing brightness variation
                brightness = 1.0 + math.sin(t * 0.9) * 0.010 + math.cos(t * 1.7) * 0.005
                frame_array = np.clip(base_array * brightness, 0, 255).astype(np.uint8)

                # Draw animated mouth on top
                frame_img = Image.fromarray(frame_array)
                draw = ImageDraw.Draw(frame_img)
                self._draw_mouth_frame(draw, mouth_region, amplitude, t)

                return np.array(frame_img)

            # ── Build and export ─────────────────────────────────────────────
            video_clip = VideoClip(make_frame, duration=duration)
            video_clip = video_clip.set_fps(fps)
            video_clip = video_clip.set_audio(audio)

            logger.info(f"Writing lip-sync avatar video: {output_path}")
            video_clip.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                bitrate='4000k',
                verbose=False,
                logger=None
            )

            audio.close()
            video_clip.close()

            logger.info(f"Lip-sync avatar video generated successfully: {duration:.1f}s")
            return AvatarResult(
                success=True,
                video_path=output_path,
                duration=duration,
                method="lip_sync_animated"
            )

        except Exception as e:
            logger.error(f"Lip-sync avatar generation failed: {e}")
            return self._generate_static_fallback(audio_path, output_path, avatar_image)

    # ── Lip-sync helpers ──────────────────────────────────────────────────────

    def _extract_audio_amplitude(
        self, audio_path: str, fps: int, duration: float
    ):
        """
        Return a float32 numpy array of length int(duration*fps)+1 whose
        values are the normalised RMS amplitude of the audio at each video frame.
        0 = silence, 1 = peak loudness.

        Falls back gracefully: librosa → pydub → simulated speech rhythm.
        """
        import numpy as np

        n_frames = int(duration * fps) + 1

        # ── librosa (best quality) ────────────────────────────────────────────
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=None, mono=True)
            hop = max(1, int(sr / fps))
            rms = librosa.feature.rms(y=y, hop_length=hop)[0].astype(np.float32)
            logger.debug("Lip-sync amplitude: librosa")
        except ImportError:
            rms = None

        # ── pydub ─────────────────────────────────────────────────────────────
        if rms is None:
            try:
                from pydub import AudioSegment
                seg = AudioSegment.from_file(audio_path).set_channels(1)
                sr = seg.frame_rate
                samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
                frame_size = max(1, int(sr / fps))
                rms = np.array([
                    np.sqrt(np.mean(
                        samples[i * frame_size: min((i + 1) * frame_size, len(samples))] ** 2
                    ))
                    for i in range(n_frames)
                ], dtype=np.float32)
                logger.debug("Lip-sync amplitude: pydub")
            except Exception as exc:
                logger.debug(f"Lip-sync pydub failed: {exc}")
                rms = None

        # ── simulated speech rhythm (last resort) ─────────────────────────────
        if rms is None:
            logger.debug("Lip-sync amplitude: simulated rhythm")
            t = np.linspace(0, duration, n_frames, dtype=np.float32)
            rms = (
                np.abs(np.sin(t * 3.8)) * np.abs(np.sin(t * 7.1 + 0.9)) * 0.75
                + np.abs(np.sin(t * 2.3 + 0.4)) * 0.20
            )

        # Normalise
        rms = np.asarray(rms, dtype=np.float32)
        peak = rms.max()
        if peak > 1e-6:
            rms = rms / peak

        # Smooth (~80 ms window) for natural jaw movement
        window = max(3, fps // 12)
        kernel = np.ones(window, dtype=np.float32) / window
        rms = np.convolve(np.pad(rms, (window // 2, window // 2), mode='edge'),
                          kernel, mode='valid')

        # Guarantee exact frame count
        if len(rms) > n_frames:
            rms = rms[:n_frames]
        elif len(rms) < n_frames:
            rms = np.pad(rms, (0, n_frames - len(rms)), mode='edge')

        return rms

    def _get_mouth_region(self, pil_image, avatar_image_path: str = None) -> dict:
        """
        Locate the lip/mouth area in the (already-resized) avatar image.

        Detection order:
          1. MediaPipe face-mesh  (most accurate, optional dependency)
          2. OpenCV Haar cascade  (good, optional dependency)
          3. Default avatar known proportions
          4. Generic portrait heuristic
        Returns dict: {cx, cy, w, h, method}
        """
        import numpy as np

        img_w, img_h = pil_image.size

        # ── 1. MediaPipe ──────────────────────────────────────────────────────
        try:
            import mediapipe as mp
            with mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True, max_num_faces=1, refine_landmarks=True
            ) as fm:
                res = fm.process(np.array(pil_image))
                if res.multi_face_landmarks:
                    lm = res.multi_face_landmarks[0].landmark
                    # Outer-lip landmark indices (MediaPipe 468-point mesh)
                    lip_ids = [
                        61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
                        146, 91, 181, 84, 17, 314, 405, 321, 375,
                    ]
                    lx = [lm[i].x * img_w for i in lip_ids]
                    ly = [lm[i].y * img_h for i in lip_ids]
                    cx = int(np.mean(lx))
                    cy = int(np.mean(ly))
                    lip_w = int((max(lx) - min(lx)) * 1.5)
                    lip_h = int((max(ly) - min(ly)) * 3.5)
                    return {
                        'cx': cx, 'cy': cy,
                        'w': max(lip_w, int(img_w * 0.10)),
                        'h': max(lip_h, int(img_h * 0.04)),
                        'method': 'mediapipe',
                    }
        except (ImportError, Exception):
            pass

        # ── 2. OpenCV Haar cascade ────────────────────────────────────────────
        try:
            import cv2
            gray = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
            )
            if len(faces) > 0:
                fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                return {
                    'cx': fx + fw // 2,
                    'cy': fy + int(fh * 0.76),   # mouth ≈ 76 % down the face box
                    'w': int(fw * 0.48),
                    'h': int(fh * 0.20),
                    'method': 'opencv',
                }
        except (ImportError, Exception):
            pass

        # ── 3. Default avatar known proportions ───────────────────────────────
        # Our generated avatar (512 × 640) has mouth centre at (256, 275).
        # Proportionally: cx = 50 %, cy = 43 % of height.
        if avatar_image_path and Path(avatar_image_path).name == 'news_anchor.png':
            return {
                'cx': img_w // 2,
                'cy': int(img_h * 0.43),
                'w': int(img_w * 0.175),
                'h': int(img_h * 0.070),
                'method': 'default_avatar_known',
            }

        # ── 4. Generic portrait heuristic ─────────────────────────────────────
        return {
            'cx': img_w // 2,
            'cy': int(img_h * 0.66),
            'w': int(img_w * 0.22),
            'h': int(img_h * 0.09),
            'method': 'heuristic',
        }

    def _draw_mouth_frame(
        self, draw, mouth_region: dict, amplitude: float, t: float
    ) -> None:
        """
        Paint an animated mouth onto a PIL ImageDraw at the given mouth_region.

        Parameters
        ----------
        draw         : PIL.ImageDraw.Draw
        mouth_region : {cx, cy, w, h}  — centre x/y, total width, max height
        amplitude    : float [0, 1]    — current audio loudness
        t            : float           — current video time (seconds), for jitter
        """
        import math

        cx = mouth_region['cx']
        cy = mouth_region['cy']
        mw = mouth_region['w']
        mh = mouth_region['h']

        # Natural micro-jitter (proportional to speech energy so silence is still)
        jitter = (math.sin(t * 21.3) * 0.03 + math.cos(t * 13.7) * 0.02) * amplitude
        eff_amp = max(0.0, min(1.0, amplitude + jitter))

        # Gamma curve: small movements for quiet audio, wide for loud speech
        open_ratio = eff_amp ** 0.60
        open_h = int(mh * open_ratio)
        half_open = open_h // 2
        half_w = mw // 2

        # Style parameters
        lip_thick = max(2, mh // 5)

        # Colour palette
        LIP_COLOR  = (185, 78, 78)    # pink-red lips
        DARK_COLOR = (28, 8, 8)       # inner-mouth darkness
        TEETH_TOP  = (248, 244, 236)  # upper teeth — warm white
        TEETH_BOT  = (235, 232, 224)  # lower teeth — slightly darker

        if open_h < 3:
            # ── CLOSED ──────────────────────────────────────────────────────
            # Upper lip arch
            draw.arc(
                [cx - half_w, cy - lip_thick, cx + half_w, cy + lip_thick // 2],
                start=195, end=345, fill=LIP_COLOR, width=lip_thick,
            )
            # Lower lip (slightly fuller)
            draw.arc(
                [cx - half_w + 4, cy - lip_thick // 2,
                 cx + half_w - 4, cy + lip_thick + 2],
                start=15, end=165, fill=LIP_COLOR, width=lip_thick,
            )
        else:
            # ── OPEN ─────────────────────────────────────────────────────────

            # 1. Dark inner cavity
            draw.ellipse(
                [cx - half_w + lip_thick, cy - half_open,
                 cx + half_w - lip_thick, cy + half_open],
                fill=DARK_COLOR,
            )

            # 2. Upper teeth
            upper_teeth_h = max(2, half_open - lip_thick)
            if upper_teeth_h > 3:
                tb = [
                    cx - half_w + lip_thick + 2,
                    cy - half_open + lip_thick // 2,
                    cx + half_w - lip_thick - 2,
                    cy - half_open + lip_thick // 2 + upper_teeth_h,
                ]
                draw.rectangle(tb, fill=TEETH_TOP)
                # Tooth divider lines
                tw = (tb[2] - tb[0]) // 4
                for i in range(1, 4):
                    tx = tb[0] + i * tw
                    draw.line([(tx, tb[1]), (tx, tb[3])],
                              fill=(215, 210, 200), width=1)

            # 3. Lower teeth (thin sliver)
            if half_open > lip_thick * 2:
                lower_h = max(2, min(half_open // 3, lip_thick))
                lb = [
                    cx - half_w + lip_thick + 4,
                    cy + half_open - lip_thick // 2 - lower_h,
                    cx + half_w - lip_thick - 4,
                    cy + half_open - lip_thick // 2,
                ]
                draw.rectangle(lb, fill=TEETH_BOT)

            # 4. Upper lip arc
            draw.arc(
                [cx - half_w, cy - half_open - lip_thick // 2,
                 cx + half_w, cy - half_open + lip_thick],
                start=180, end=360, fill=LIP_COLOR, width=lip_thick,
            )

            # 5. Lower lip arc (slightly fuller)
            lo_thick = int(lip_thick * 1.25)
            draw.arc(
                [cx - half_w, cy + half_open - lip_thick,
                 cx + half_w, cy + half_open + lo_thick // 2],
                start=0, end=180, fill=LIP_COLOR, width=lo_thick,
            )

            # 6. Corner accents
            corner_r = max(2, lip_thick // 2)
            for corner_x in [cx - half_w, cx + half_w]:
                draw.ellipse(
                    [corner_x - corner_r, cy - corner_r,
                     corner_x + corner_r, cy + corner_r],
                    fill=LIP_COLOR,
                )

    # ─────────────────────────────────────────────────────────────────────────

    def _generate_static_fallback(
        self,
        audio_path: str,
        output_path: str,
        avatar_image: str
    ) -> AvatarResult:
        """
        Ultimate fallback - simple static image with audio.
        """
        try:
            from moviepy.editor import ImageClip, AudioFileClip

            logger.info("Using static fallback for avatar video")

            # Load audio
            audio = AudioFileClip(audio_path)
            duration = audio.duration

            # Create image clip
            image_clip = ImageClip(avatar_image, duration=duration)

            # Resize to 1080p maintaining aspect ratio
            target_height = 1080
            image_clip = image_clip.resize(height=target_height)

            # Ensure width is even
            if image_clip.w % 2 != 0:
                image_clip = image_clip.resize(width=image_clip.w + 1)

            # Set audio
            video = image_clip.set_audio(audio)

            # Write output
            video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )

            # Cleanup
            audio.close()
            image_clip.close()

            return AvatarResult(
                success=True,
                video_path=output_path,
                duration=duration,
                method="simple_static"
            )

        except Exception as e:
            logger.error(f"Static fallback also failed: {e}")
            return AvatarResult(
                success=False,
                video_path="",
                duration=0,
                method="simple",
                error=str(e)
            )

    def _create_default_avatar(self) -> Optional[str]:
        """Create a cartoon-style AI avatar image"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import math

            # Create a cartoon-style news anchor avatar
            avatar_path = Path("assets/avatars/news_anchor.png")
            avatar_path.parent.mkdir(parents=True, exist_ok=True)

            # Create image with gradient-like background
            width, height = 512, 640
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)

            # Background gradient effect (darker at edges)
            for i in range(height):
                gradient_color = int(26 + (i / height) * 15)
                draw.line([(0, i), (width, i)], fill=(gradient_color, gradient_color, 46 + int(i/height * 20)))

            center_x = width // 2

            # === BODY / SUIT ===
            # Suit jacket (professional blue)
            suit_color = '#2563eb'  # Nice blue suit
            suit_top = 380
            # Draw shoulders and torso
            draw.polygon([
                (center_x - 150, suit_top),  # Left shoulder
                (center_x - 180, height),     # Left bottom
                (center_x + 180, height),     # Right bottom
                (center_x + 150, suit_top),   # Right shoulder
            ], fill=suit_color)

            # Suit lapels (darker)
            lapel_color = '#1d4ed8'
            # Left lapel
            draw.polygon([
                (center_x - 40, suit_top + 20),
                (center_x - 80, height),
                (center_x - 20, height),
                (center_x, suit_top + 80),
            ], fill=lapel_color)
            # Right lapel
            draw.polygon([
                (center_x + 40, suit_top + 20),
                (center_x + 80, height),
                (center_x + 20, height),
                (center_x, suit_top + 80),
            ], fill=lapel_color)

            # White shirt / collar
            shirt_color = '#f8fafc'
            draw.polygon([
                (center_x - 35, suit_top + 10),
                (center_x, suit_top + 100),
                (center_x + 35, suit_top + 10),
            ], fill=shirt_color)

            # Tie
            tie_color = '#dc2626'  # Red tie
            draw.polygon([
                (center_x - 12, suit_top + 30),
                (center_x + 12, suit_top + 30),
                (center_x + 8, height - 100),
                (center_x - 8, height - 100),
            ], fill=tie_color)
            # Tie knot
            draw.ellipse([center_x - 15, suit_top + 20, center_x + 15, suit_top + 50], fill=tie_color)

            # === NECK ===
            neck_color = '#fcd9b6'  # Skin tone
            neck_width = 50
            neck_top = 340
            draw.rectangle([
                center_x - neck_width // 2, neck_top,
                center_x + neck_width // 2, suit_top + 30
            ], fill=neck_color)

            # === HEAD ===
            head_center_y = 220
            head_radius_x = 90
            head_radius_y = 110

            # Main face (oval)
            draw.ellipse([
                center_x - head_radius_x, head_center_y - head_radius_y,
                center_x + head_radius_x, head_center_y + head_radius_y
            ], fill=neck_color)

            # === HAIR ===
            hair_color = '#1f2937'  # Dark hair
            # Top hair
            draw.ellipse([
                center_x - head_radius_x - 5, head_center_y - head_radius_y - 20,
                center_x + head_radius_x + 5, head_center_y - 30
            ], fill=hair_color)

            # Side hair (left)
            draw.ellipse([
                center_x - head_radius_x - 10, head_center_y - head_radius_y + 20,
                center_x - head_radius_x + 40, head_center_y + 20
            ], fill=hair_color)

            # Side hair (right)
            draw.ellipse([
                center_x + head_radius_x - 40, head_center_y - head_radius_y + 20,
                center_x + head_radius_x + 10, head_center_y + 20
            ], fill=hair_color)

            # === FACIAL FEATURES ===
            # Eyebrows
            eyebrow_color = '#374151'
            eyebrow_y = head_center_y - 40
            # Left eyebrow
            draw.arc([center_x - 55, eyebrow_y - 10, center_x - 15, eyebrow_y + 10],
                     start=200, end=340, fill=eyebrow_color, width=4)
            # Right eyebrow
            draw.arc([center_x + 15, eyebrow_y - 10, center_x + 55, eyebrow_y + 10],
                     start=200, end=340, fill=eyebrow_color, width=4)

            # Eyes
            eye_y = head_center_y - 15
            eye_spacing = 35

            # Eye whites
            eye_white = '#ffffff'
            eye_width = 28
            eye_height = 20
            # Left eye
            draw.ellipse([
                center_x - eye_spacing - eye_width, eye_y - eye_height,
                center_x - eye_spacing + eye_width, eye_y + eye_height
            ], fill=eye_white)
            # Right eye
            draw.ellipse([
                center_x + eye_spacing - eye_width, eye_y - eye_height,
                center_x + eye_spacing + eye_width, eye_y + eye_height
            ], fill=eye_white)

            # Pupils (looking slightly to the side - more engaging)
            pupil_color = '#1f2937'
            pupil_radius = 10
            pupil_offset = 3  # Slight offset for natural look
            # Left pupil
            draw.ellipse([
                center_x - eye_spacing + pupil_offset - pupil_radius,
                eye_y - pupil_radius,
                center_x - eye_spacing + pupil_offset + pupil_radius,
                eye_y + pupil_radius
            ], fill=pupil_color)
            # Right pupil
            draw.ellipse([
                center_x + eye_spacing + pupil_offset - pupil_radius,
                eye_y - pupil_radius,
                center_x + eye_spacing + pupil_offset + pupil_radius,
                eye_y + pupil_radius
            ], fill=pupil_color)

            # Eye shine (makes it look alive)
            shine_color = '#ffffff'
            shine_radius = 4
            draw.ellipse([
                center_x - eye_spacing + pupil_offset - shine_radius + 5,
                eye_y - shine_radius - 3,
                center_x - eye_spacing + pupil_offset + shine_radius + 5,
                eye_y + shine_radius - 3
            ], fill=shine_color)
            draw.ellipse([
                center_x + eye_spacing + pupil_offset - shine_radius + 5,
                eye_y - shine_radius - 3,
                center_x + eye_spacing + pupil_offset + shine_radius + 5,
                eye_y + shine_radius - 3
            ], fill=shine_color)

            # Nose (simple)
            nose_color = '#e5c9a8'
            nose_y = head_center_y + 20
            draw.polygon([
                (center_x, nose_y - 25),
                (center_x - 12, nose_y + 10),
                (center_x + 12, nose_y + 10),
            ], fill=nose_color)

            # Mouth position stored for lip-sync animation (not drawn statically)
            smile_y = head_center_y + 55
            self._default_mouth_region = {
                'cx': center_x, 'cy': smile_y,
                'w': 90, 'h': 48,   # pixel coords in 512×640 image space
                'method': 'default_avatar_known'
            }

            # Ears
            ear_color = '#fcd9b6'
            ear_y = head_center_y - 10
            # Left ear
            draw.ellipse([
                center_x - head_radius_x - 5, ear_y - 20,
                center_x - head_radius_x + 20, ear_y + 30
            ], fill=ear_color)
            # Right ear
            draw.ellipse([
                center_x + head_radius_x - 20, ear_y - 20,
                center_x + head_radius_x + 5, ear_y + 30
            ], fill=ear_color)

            # === MICROPHONE (news anchor detail) ===
            mic_color = '#374151'
            mic_x = center_x - 100
            mic_y = suit_top + 60
            # Microphone body
            draw.ellipse([mic_x - 8, mic_y - 15, mic_x + 8, mic_y + 15], fill=mic_color)
            # Microphone wire hint
            draw.line([(mic_x, mic_y + 15), (mic_x - 20, suit_top + 120)], fill=mic_color, width=2)

            # === NEWS BADGE ===
            badge_color = '#fbbf24'  # Gold badge
            badge_x = center_x + 80
            badge_y = suit_top + 50
            draw.ellipse([badge_x - 15, badge_y - 15, badge_x + 15, badge_y + 15], fill=badge_color)
            # "AI" text on badge
            try:
                badge_font = ImageFont.truetype("arial.ttf", 14)
            except:
                badge_font = ImageFont.load_default()
            draw.text((badge_x - 8, badge_y - 8), "AI", fill='#1f2937', font=badge_font)

            # Save the cartoon avatar
            img.save(str(avatar_path), quality=95)
            logger.info(f"Created cartoon-style avatar: {avatar_path}")

            return str(avatar_path)

        except Exception as e:
            logger.error(f"Failed to create cartoon avatar: {e}")
            return None

    def _create_static_video(
        self,
        image_path: str,
        output_path: str,
        duration: float
    ) -> None:
        """Create a static video from an image"""
        from moviepy.editor import ImageClip

        clip = ImageClip(image_path, duration=duration)
        clip.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            verbose=False,
            logger=None
        )
        clip.close()

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except Exception:
            return 0.0

    def _get_video_duration(self, video_path: str) -> float:
        """Get duration of video file"""
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_path)
            duration = clip.duration
            clip.close()
            return duration
        except Exception:
            return 0.0

    def setup_instructions(self) -> str:
        """Get setup instructions for advanced avatar methods"""
        return """
=== Avatar Generator Setup Instructions ===

Currently using: {method}
Available methods: {available}

To enable advanced avatar generation:

1. SadTalker (Recommended - Best quality)
   - Clone: git clone https://github.com/OpenTalker/SadTalker
   - Install: pip install -r requirements.txt
   - Download models from the repo instructions
   - Set environment variable: SADTALKER_PATH=/path/to/SadTalker

2. Wav2Lip (Good lip sync)
   - Clone: git clone https://github.com/Rudrabha/Wav2Lip
   - Install: pip install -r requirements.txt
   - Download checkpoints from the repo
   - Set environment variable: WAV2LIP_PATH=/path/to/Wav2Lip

Note: Both methods require a GPU for reasonable performance.
Without GPU, video generation will be slow (10-20 minutes per video).

The 'simple' method (static image + audio) works without any setup.
""".format(method=self.method, available=self.available_methods)


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Avatar Generator CLI")
    parser.add_argument("--test", action="store_true", help="Run test generation")
    parser.add_argument("--audio", type=str, help="Input audio file")
    parser.add_argument("--image", type=str, help="Avatar image")
    parser.add_argument("--output", type=str, default="output/test_avatar.mp4", help="Output path")
    parser.add_argument("--method", type=str, default="auto", help="Generation method")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")

    args = parser.parse_args()

    generator = AvatarGenerator(method=args.method)

    if args.setup:
        print(generator.setup_instructions())

    elif args.test or args.audio:
        if not args.audio:
            print("Error: --audio required for generation")
            print("Example: python -m src.avatar.avatar_generator --audio output/test.mp3 --output output/test.mp4")
        else:
            result = generator.generate(
                audio_path=args.audio,
                output_path=args.output,
                avatar_image=args.image
            )

            if result.success:
                print(f"\nSuccess! Video generated at: {result.video_path}")
                print(f"Duration: {result.duration:.1f} seconds")
                print(f"Method: {result.method}")
            else:
                print(f"\nError: {result.error}")

    else:
        parser.print_help()
        print("\n" + generator.setup_instructions())
