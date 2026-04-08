"""
Wav2Lip ONNX inference for CPU-based realistic lip-sync.
Uses ONNX Runtime instead of PyTorch for much faster CPU inference.
"""

import cv2
import numpy as np
import subprocess
import tempfile
from pathlib import Path
from loguru import logger

# Audio processing
import librosa
from scipy import signal
from scipy.io import wavfile


# Mel spectrogram parameters (matching Wav2Lip hparams)
_SR = 16000
_N_FFT = 800
_HOP_SIZE = 200
_WIN_SIZE = 800
_NUM_MELS = 80
_FMIN = 55
_FMAX = 7600
_REF_LEVEL_DB = 20
_MIN_LEVEL_DB = -100
_MEL_STEP_SIZE = 16

_mel_basis = None


def _build_mel_basis():
    return librosa.filters.mel(sr=_SR, n_fft=_N_FFT, n_mels=_NUM_MELS, fmin=_FMIN, fmax=_FMAX)


def _linear_to_mel(spectogram):
    global _mel_basis
    if _mel_basis is None:
        _mel_basis = _build_mel_basis()
    return np.dot(_mel_basis, spectogram)


def _amp_to_db(x):
    min_level = np.exp(_MIN_LEVEL_DB / 20 * np.log(10))
    return 20 * np.log10(np.maximum(min_level, x))


def _normalize(S):
    return np.clip((2 * 4.0) * ((S - _MIN_LEVEL_DB) / (-_MIN_LEVEL_DB)) - 4.0, -4.0, 4.0)


def _stft(y):
    return librosa.stft(y=y, n_fft=_N_FFT, hop_length=_HOP_SIZE, win_length=_WIN_SIZE)


def melspectrogram(wav):
    D = _stft(wav)
    S = _amp_to_db(_linear_to_mel(np.abs(D))) - _REF_LEVEL_DB
    return _normalize(S)


def load_wav(path, sr=_SR):
    return librosa.core.load(path, sr=sr)[0]


def face_detect_simple(image):
    """Simple face detection using OpenCV Haar cascade."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
    if len(faces) == 0:
        # Fallback: assume face is center of image
        h, w = image.shape[:2]
        return (int(w * 0.15), int(h * 0.05), int(w * 0.85), int(h * 0.85))
    x, y, w, h = faces[0]
    return (x, y, x + w, y + h)


def wav2lip_onnx_inference(
    face_image_path: str,
    audio_path: str,
    output_path: str,
    onnx_model_path: str,
    fps: int = 30,
    img_size: int = 96,
    batch_size: int = 8,
    pads: list = None
) -> bool:
    """
    Run Wav2Lip inference using ONNX Runtime (CPU-optimized).

    Args:
        face_image_path: Path to face image (jpg/png)
        audio_path: Path to audio file (wav)
        output_path: Path for output video (mp4)
        onnx_model_path: Path to wav2lip_gan.onnx
        fps: Output video FPS
        img_size: Face crop size (96 for standard Wav2Lip)
        batch_size: Inference batch size
        pads: Face detection padding [top, bottom, left, right]

    Returns:
        True if successful
    """
    import onnxruntime as ort

    pads = pads or [0, 10, 0, 0]

    # Load ONNX model
    logger.info(f"Loading Wav2Lip ONNX model: {onnx_model_path}")
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.intra_op_num_threads = 4
    session = ort.InferenceSession(
        onnx_model_path,
        sess_options=sess_options,
        providers=['CPUExecutionProvider']
    )

    # Load face image
    face_image = cv2.imread(face_image_path)
    if face_image is None:
        raise ValueError(f"Could not read face image: {face_image_path}")

    # Convert audio to WAV if needed
    wav_path = audio_path
    temp_wav = None
    if not audio_path.endswith('.wav'):
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            ffmpeg_exe = "ffmpeg"
        temp_wav = str(Path(output_path).parent / "temp_wav2lip_audio.wav")
        subprocess.run([ffmpeg_exe, "-y", "-i", audio_path, "-acodec", "pcm_s16le",
                       "-ar", "16000", "-ac", "1", temp_wav],
                      capture_output=True, check=True)
        wav_path = temp_wav

    # Load audio and compute mel spectrogram
    wav = load_wav(wav_path)
    mel = melspectrogram(wav)
    logger.info(f"Mel spectrogram shape: {mel.shape}")

    if np.isnan(mel.reshape(-1)).sum() > 0:
        raise ValueError("Mel contains NaN values")

    # Split mel into chunks
    mel_chunks = []
    mel_idx_multiplier = 80.0 / fps
    i = 0
    while True:
        start_idx = int(i * mel_idx_multiplier)
        if start_idx + _MEL_STEP_SIZE > mel.shape[1]:
            mel_chunks.append(mel[:, mel.shape[1] - _MEL_STEP_SIZE:])
            break
        mel_chunks.append(mel[:, start_idx: start_idx + _MEL_STEP_SIZE])
        i += 1

    logger.info(f"Mel chunks: {len(mel_chunks)}, generating {len(mel_chunks)} frames")

    # Detect face in image
    x1, y1, x2, y2 = face_detect_simple(face_image)
    pady1, pady2, padx1, padx2 = pads
    y1 = max(0, y1 - pady1)
    y2 = min(face_image.shape[0], y2 + pady2)
    x1 = max(0, x1 - padx1)
    x2 = min(face_image.shape[1], x2 + padx2)

    face_crop = face_image[y1:y2, x1:x2]
    face_resized = cv2.resize(face_crop, (img_size, img_size))

    # Prepare output video
    frame_h, frame_w = face_image.shape[:2]
    temp_avi = str(Path(output_path).parent / "temp_wav2lip_result.avi")
    out = cv2.VideoWriter(temp_avi, cv2.VideoWriter_fourcc(*'DIVX'), fps, (frame_w, frame_h))

    # Process in batches
    total_batches = int(np.ceil(len(mel_chunks) / batch_size))

    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(mel_chunks))

        batch_mels = mel_chunks[start:end]
        cur_batch_size = len(batch_mels)

        # Prepare image batch (same face for all frames since it's a static image)
        img_batch = np.array([face_resized] * cur_batch_size)
        mel_batch = np.array(batch_mels)

        # Mask lower half of face
        img_masked = img_batch.copy()
        img_masked[:, img_size // 2:] = 0

        # Concatenate masked + original (6 channels)
        img_batch_input = np.concatenate((img_masked, img_batch), axis=3) / 255.0
        mel_batch_input = mel_batch.reshape(cur_batch_size, mel_batch.shape[1], mel_batch.shape[2], 1)

        # Transpose to NCHW format
        img_batch_input = np.transpose(img_batch_input, (0, 3, 1, 2)).astype(np.float32)
        mel_batch_input = np.transpose(mel_batch_input, (0, 3, 1, 2)).astype(np.float32)

        # ONNX inference
        pred = session.run(None, {
            'mel_spectrogram': mel_batch_input,
            'video_frames': img_batch_input
        })[0]

        # Post-process predictions
        pred = np.transpose(pred, (0, 2, 3, 1)) * 255.0

        for p in pred:
            frame = face_image.copy()
            p_resized = cv2.resize(p.astype(np.uint8), (x2 - x1, y2 - y1))
            frame[y1:y2, x1:x2] = p_resized
            out.write(frame)

        if batch_idx % 10 == 0:
            progress = (batch_idx + 1) / total_batches * 100
            logger.info(f"Wav2Lip ONNX progress: {progress:.0f}% ({batch_idx + 1}/{total_batches} batches)")

    out.release()

    # Mux audio + video with ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg_exe = "ffmpeg"

    mux_cmd = [ffmpeg_exe, "-y", "-i", wav_path, "-i", temp_avi,
               "-strict", "-2", "-q:v", "1", output_path]
    result = subprocess.run(mux_cmd, capture_output=True, text=True)

    # Cleanup
    try:
        Path(temp_avi).unlink(missing_ok=True)
        if temp_wav:
            Path(temp_wav).unlink(missing_ok=True)
    except Exception:
        pass

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg mux failed: {result.stderr}")

    logger.info(f"Wav2Lip ONNX inference complete: {output_path}")
    return True
