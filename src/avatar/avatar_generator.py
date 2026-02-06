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
        Generate animated avatar video with subtle movements and audio.
        Creates a more engaging video than a static image.
        """
        try:
            from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
            from PIL import Image
            import numpy as np

            logger.info("Generating animated avatar video with audio")

            # Load audio
            audio = AudioFileClip(audio_path)
            duration = audio.duration

            # Load and prepare the avatar image
            pil_image = Image.open(avatar_image)

            # Resize to 1080p maintaining aspect ratio
            target_height = 1080
            aspect_ratio = pil_image.width / pil_image.height
            target_width = int(target_height * aspect_ratio)
            # Ensure width is even for video encoding
            target_width = target_width if target_width % 2 == 0 else target_width + 1

            pil_image = pil_image.resize((target_width, target_height), Image.LANCZOS)

            # Convert to numpy array
            base_frame = np.array(pil_image)

            # Create subtle animation frames
            def make_animated_frame(t):
                """Create frame with subtle breathing/idle animation"""
                import math

                # Copy base frame
                frame = base_frame.copy()

                # Subtle vertical "breathing" movement (very slight scale pulse)
                breath_cycle = math.sin(t * 1.5) * 0.003  # Very subtle 1.5 Hz breathing

                # Apply subtle brightness variation to simulate life
                brightness_var = 1.0 + math.sin(t * 0.8) * 0.02  # Subtle brightness pulse

                # Apply brightness variation
                frame = np.clip(frame * brightness_var, 0, 255).astype(np.uint8)

                return frame

            # Create the animated video clip
            animated_clip = ImageClip(avatar_image, duration=duration)
            animated_clip = animated_clip.resize(height=target_height)

            # For a more sophisticated animation, we can create a VideoClip with frame function
            from moviepy.video.VideoClip import VideoClip

            # Create animated video with subtle movement
            def make_frame(t):
                """Generate frame with subtle idle animation"""
                import math

                frame = base_frame.copy().astype(np.float32)

                # Subtle brightness variation (simulates subtle lighting changes)
                brightness = 1.0 + math.sin(t * 0.7) * 0.015
                frame = frame * brightness

                # Clip values to valid range
                frame = np.clip(frame, 0, 255).astype(np.uint8)

                return frame

            animated_video = VideoClip(make_frame, duration=duration)
            animated_video = animated_video.set_fps(30)

            # Set audio
            video = animated_video.set_audio(audio)

            # Write output
            logger.info(f"Writing animated avatar video: {output_path}")
            video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                bitrate='5000k',
                verbose=False,
                logger=None
            )

            # Cleanup
            audio.close()
            animated_video.close()

            logger.info(f"Avatar video generated successfully: {duration:.1f}s")

            return AvatarResult(
                success=True,
                video_path=output_path,
                duration=duration,
                method="simple_animated"
            )

        except Exception as e:
            logger.error(f"Animated avatar generation failed: {e}")
            # Try basic static fallback
            return self._generate_static_fallback(audio_path, output_path, avatar_image)

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

            # Friendly smile
            smile_color = '#dc2626'
            smile_y = head_center_y + 55
            # Draw a nice curved smile
            draw.arc([center_x - 40, smile_y - 20, center_x + 40, smile_y + 20],
                     start=10, end=170, fill=smile_color, width=5)

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
