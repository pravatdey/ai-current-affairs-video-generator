"""
Viseme Mapper — converts word-timing data from edge_tts into a per-frame
viseme timeline that drives phoneme-aware lip-sync animation.

Enhanced 9-viseme system aligned with Rhubarb Lip Sync's Preston Blair
phoneme set for consistency across both phoneme sources:

  0  CLOSED   — silence / pause (lips together, neutral rest)
  1  MBP      — b, m, p (lips pressed together firmly)
  2  SMALL_OPEN — generic small opening (most consonants when quiet)
  3  EH       — e as in "bed" (mid-open, relaxed jaw)
  4  AH       — a as in "father" (wide open mouth, jaw drops)
  5  OH       — o as in "go" (rounded lips, medium open)
  6  OO       — oo as in "food" (tight round lips, small opening)
  7  FV       — f, v (lower lip tucked under upper teeth)
  8  L_TH     — l, th (tongue visible, tip touches teeth/ridge)

No external NLP dependencies — uses a fast rule-based English
letter-to-phoneme mapper that covers common patterns.
"""

import re
import numpy as np
from typing import List, Dict

from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Viseme IDs (aligned with Rhubarb Preston Blair shapes) ─────────────────
CLOSED = 0       # X — silence / rest
MBP = 1          # A — lips pressed
SMALL_OPEN = 2   # B — small generic opening
EH = 3           # C — mid open (e in "bed")
AH = 4           # D — wide open (a in "father")
OH = 5           # E — rounded medium
OO = 6           # F — tight round
FV = 7           # G — lip tuck (f, v)
L_TH = 8         # H — tongue visible (l, th)

NUM_VISEMES = 9

VISEME_NAMES = [
    "CLOSED", "MBP", "SMALL_OPEN", "EH", "AH",
    "OH", "OO", "FV", "L_TH",
]

# ── Digraph / trigraph → viseme (checked FIRST, longest match wins) ─────────
_DIGRAPH_MAP: List[tuple] = [
    # Trigraphs
    ("tch", [SMALL_OPEN, EH]),
    ("sch", [SMALL_OPEN]),
    ("igh", [AH]),
    ("ous", [AH, SMALL_OPEN]),
    ("tion", [SMALL_OPEN, AH, SMALL_OPEN]),
    ("sion", [SMALL_OPEN, AH, SMALL_OPEN]),
    # Digraphs — consonants
    ("th", [L_TH]),
    ("sh", [SMALL_OPEN]),
    ("ch", [SMALL_OPEN]),
    ("ph", [FV]),
    ("wh", [OO]),
    ("ck", [SMALL_OPEN]),
    ("ng", [SMALL_OPEN]),
    ("qu", [OO, OH]),
    ("gh", []),       # silent in "light" — skip
    ("kn", [SMALL_OPEN]),
    ("wr", [SMALL_OPEN]),
    ("gn", [SMALL_OPEN]),
    # Digraphs — vowels
    ("ee", [EH]),
    ("ea", [EH]),
    ("oo", [OO]),
    ("ou", [AH, OO]),
    ("ow", [AH, OH]),
    ("oi", [OH, EH]),
    ("oy", [OH, EH]),
    ("ai", [AH, EH]),
    ("ay", [AH, EH]),
    ("ei", [AH, EH]),
    ("ey", [AH, EH]),
    ("ie", [EH]),
    ("au", [AH, OH]),
    ("aw", [AH]),
    ("oa", [OH]),
    ("ue", [OO]),
    ("ui", [OO, EH]),
    ("er", [EH]),
    ("ir", [EH]),
    ("ur", [EH]),
    ("or", [OH]),
    ("ar", [AH]),
]

# ── Single-letter → viseme ──────────────────────────────────────────────────
_LETTER_MAP: Dict[str, int] = {
    # Vowels
    "a": AH,
    "e": EH,
    "i": EH,
    "o": OH,
    "u": OO,
    "y": EH,
    # Labial stops / nasals (lips close)
    "b": MBP,
    "m": MBP,
    "p": MBP,
    # Labiodental fricatives (lip tuck)
    "f": FV,
    "v": FV,
    # Alveolar / dental / tongue
    "d": SMALL_OPEN,
    "l": L_TH,
    "n": SMALL_OPEN,
    "r": SMALL_OPEN,
    "s": SMALL_OPEN,
    "t": SMALL_OPEN,
    "z": SMALL_OPEN,
    # Velar / palatal / glottal
    "c": SMALL_OPEN,
    "g": SMALL_OPEN,
    "h": AH,
    "j": SMALL_OPEN,
    "k": SMALL_OPEN,
    "q": OO,
    "w": OO,
    "x": SMALL_OPEN,
}


def word_to_visemes(word: str) -> List[int]:
    """
    Convert an English word to a sequence of viseme IDs using
    rule-based letter pattern matching.

    Handles digraphs/trigraphs first, then falls back to single letters.
    """
    word = word.lower().strip()
    # Remove non-alpha characters
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return [CLOSED]

    visemes: List[int] = []
    i = 0
    while i < len(word):
        matched = False
        # Try longest patterns first (trigraphs, then digraphs)
        for pattern, vids in _DIGRAPH_MAP:
            plen = len(pattern)
            if word[i: i + plen] == pattern:
                visemes.extend(vids)
                i += plen
                matched = True
                break
        if not matched:
            ch = word[i]
            vid = _LETTER_MAP.get(ch, SMALL_OPEN)  # default to small opening
            visemes.append(vid)
            i += 1

    # Filter out empty sequences (silent digraphs like "gh")
    if not visemes:
        visemes = [CLOSED]

    return visemes


def generate_viseme_timeline(
    word_boundaries: List[Dict],
    fps: int,
    total_duration: float,
) -> np.ndarray:
    """
    Generate a per-frame viseme timeline from edge_tts word boundary data.

    Parameters
    ----------
    word_boundaries : list of dicts with keys: text, offset_us, duration_us
    fps : video frame rate (typically 30)
    total_duration : total audio duration in seconds

    Returns
    -------
    numpy int8 array of shape (n_frames,) — viseme ID per frame
    """
    n_frames = int(total_duration * fps) + 1
    timeline = np.zeros(n_frames, dtype=np.int8)  # default CLOSED

    for wb in word_boundaries:
        word = wb.get("text", "")
        offset_us = wb.get("offset_us", 0)
        duration_us = wb.get("duration_us", 0)

        start_sec = offset_us / 1_000_000
        dur_sec = max(duration_us / 1_000_000, 0.01)  # min 10ms

        visemes = word_to_visemes(word)
        if not visemes:
            continue

        # Distribute visemes evenly across the word's duration
        phoneme_dur = dur_sec / len(visemes)

        for j, vid in enumerate(visemes):
            ph_start = start_sec + j * phoneme_dur
            ph_end = ph_start + phoneme_dur

            frame_start = max(0, min(int(ph_start * fps), n_frames - 1))
            frame_end = max(0, min(int(ph_end * fps), n_frames - 1))

            timeline[frame_start: frame_end + 1] = vid

    unique = len(set(timeline.tolist()))
    logger.info(f"Viseme timeline: {n_frames} frames, {unique} unique visemes used")
    return timeline
