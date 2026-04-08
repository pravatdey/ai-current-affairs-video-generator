"""
Rhubarb Lip Sync Integration — professional-grade phoneme detection (CPU-only, free).

Rhubarb analyses audio and produces frame-accurate mouth cue data using the
Preston Blair phoneme set (shapes A–H).  This module wraps the CLI tool and
converts its output into a per-frame viseme timeline compatible with the
enhanced 14-viseme sprite system.

Preston Blair → Enhanced Viseme mapping:
  A  — MBP closed      (rest / "P", "B", "M")
  B  — EE / small open (most consonants, quiet vowels)
  C  — E open          ("EH" as in "bed")
  D  — AI wide         ("AH" / "AI" as in "idea")
  E  — O round         ("O" as in "go")
  F  — OO tight round  ("OO" as in "food")
  G  — FV lip-tuck     ("F", "V")
  H  — L tongue-up     ("L")
  X  — silence / rest

Requires: rhubarb.exe in tools/rhubarb-lip-sync/
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Rhubarb executable path (cross-platform) ─────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
import platform as _platform
if _platform.system() == "Windows":
    RHUBARB_EXE = str(
        _PROJECT_ROOT / "tools" / "rhubarb-lip-sync"
        / "Rhubarb-Lip-Sync-1.13.0-Windows" / "rhubarb.exe"
    )
else:
    RHUBARB_EXE = str(
        _PROJECT_ROOT / "tools" / "rhubarb-lip-sync"
        / "Rhubarb-Lip-Sync-1.13.0-Linux" / "rhubarb"
    )

# ── Preston Blair shape → enhanced viseme ID ──────────────────────────────────
# Maps Rhubarb's mouth shape letters to our 14-viseme IDs
# (see viseme_mapper.py for the full viseme table)
SHAPE_TO_VISEME = {
    "X": 0,   # CLOSED / silence
    "A": 1,   # MBP — lips pressed (rest position)
    "B": 2,   # SMALL_OPEN — generic small opening
    "C": 3,   # EH — mid-open, relaxed jaw
    "D": 4,   # AH — wide open mouth
    "E": 5,   # OH — rounded lips, medium open
    "F": 6,   # OO — tight round lips
    "G": 7,   # FV — lower lip tucked
    "H": 8,   # L_TH — tongue visible
}


def is_rhubarb_available() -> bool:
    """Check whether rhubarb.exe exists and is executable."""
    if not os.path.isfile(RHUBARB_EXE):
        return False
    try:
        result = subprocess.run(
            [RHUBARB_EXE, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def run_rhubarb(
    audio_path: str,
    dialog_text: Optional[str] = None,
    recogniser: str = "pocketSphinx",
) -> List[Dict]:
    """
    Run Rhubarb Lip Sync on an audio file and return mouth cues.

    Parameters
    ----------
    audio_path : path to WAV or FLAC audio file
    dialog_text : optional transcript (improves accuracy dramatically)
    recogniser : "pocketSphinx" (default, free) or "phonetic"

    Returns
    -------
    List of dicts: [{"start": float, "end": float, "shape": str}, ...]
    """
    if not is_rhubarb_available():
        raise RuntimeError(f"Rhubarb not found at {RHUBARB_EXE}")

    audio_path = str(Path(audio_path).resolve())

    # Convert to WAV if needed (Rhubarb prefers WAV)
    wav_path = _ensure_wav(audio_path)

    cmd = [
        RHUBARB_EXE,
        "-f", "json",           # JSON output
        "--machineReadable",    # no progress bars
        "-r", recogniser,       # recogniser engine
        wav_path,
    ]

    # If we have dialog text, write it to a temp file for better accuracy
    dialog_file = None
    if dialog_text and dialog_text.strip():
        dialog_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        dialog_file.write(dialog_text.strip())
        dialog_file.close()
        cmd.extend(["-d", dialog_file.name])

    logger.info(f"Running Rhubarb on: {audio_path}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(f"Rhubarb failed (code {result.returncode}): {stderr}")

        data = json.loads(result.stdout)
        cues = data.get("mouthCues", [])

        mouth_cues = []
        for i, cue in enumerate(cues):
            start = cue["start"]
            end = cue["end"]
            shape = cue["value"]  # A-H or X
            mouth_cues.append({"start": start, "end": end, "shape": shape})

        logger.info(f"Rhubarb: {len(mouth_cues)} mouth cues extracted")
        return mouth_cues

    finally:
        if dialog_file and os.path.exists(dialog_file.name):
            os.unlink(dialog_file.name)
        # Clean up temp WAV if we created one
        if wav_path != audio_path and os.path.exists(wav_path):
            os.unlink(wav_path)


def rhubarb_to_viseme_timeline(
    mouth_cues: List[Dict],
    fps: int,
    total_duration: float,
) -> np.ndarray:
    """
    Convert Rhubarb mouth cues to a per-frame viseme timeline.

    Returns numpy int8 array of shape (n_frames,) with viseme IDs.
    """
    n_frames = int(total_duration * fps) + 1
    timeline = np.zeros(n_frames, dtype=np.int8)  # default CLOSED

    for cue in mouth_cues:
        start_frame = max(0, int(cue["start"] * fps))
        end_frame = min(n_frames, int(cue["end"] * fps))
        viseme_id = SHAPE_TO_VISEME.get(cue["shape"], 0)
        timeline[start_frame:end_frame] = viseme_id

    unique = len(set(timeline.tolist()))
    logger.info(f"Rhubarb timeline: {n_frames} frames, {unique} unique visemes")
    return timeline


def _ensure_wav(audio_path: str) -> str:
    """Convert audio to WAV if it's not already WAV format."""
    ext = Path(audio_path).suffix.lower()
    if ext in (".wav", ".flac"):
        return audio_path

    # Convert using ffmpeg / pydub
    wav_path = str(Path(audio_path).with_suffix(".rhubarb.wav"))
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(wav_path, format="wav")
        logger.debug(f"Converted {audio_path} → {wav_path}")
        return wav_path
    except Exception as e:
        logger.warning(f"WAV conversion failed: {e}, trying raw path")
        return audio_path
