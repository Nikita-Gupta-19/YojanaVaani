"""
Speech-to-Text (ASR) Service for YojanaVaani (Phase 4).

Architectural rules:
- Abstract ASRProvider interface allowing zero-impact swapping of speech backends.
- Default implementation: VasistaWhisperProvider using vasista22 Whisper Hindi models from Hugging Face
  (vasista22/whisper-hindi-large-v2 as statutory specification target, with vasista22/whisper-hindi-small fallback).
- Loads model once at startup (singleton) to keep inference latency predictable.
- Returns transcription text, confidence score, and low_confidence flag (threshold: 0.6).
- PyTorch/Transformers only — no TensorFlow/Keras.
"""

from abc import ABC, abstractmethod
from collections import Counter
import io
import logging
import os
import re
from typing import Optional, Tuple
import certifi
import numpy as np
from pydantic import BaseModel, Field
import soundfile as sf
import scipy.signal

# Ensure system CA bundle is loaded for SSL certificate verification on macOS
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

logger = logging.getLogger(__name__)

# Model identifiers (vasista22 Whisper-Hindi series)
DEFAULT_PRIMARY_MODEL = "vasista22/whisper-hindi-small"
DEFAULT_SMALL_MODEL = "vasista22/whisper-hindi-small"
DEFAULT_LARGE_MODEL = "vasista22/whisper-hindi-large-v2"
TINY_FALLBACK_MODEL = "openai/whisper-tiny"

CONFIDENCE_THRESHOLD = 0.60
TARGET_SAMPLE_RATE = 16000

# Known Whisper Hindi hallucination triggers (originating from All India Radio / DD News training data)
KNOWN_HALLUCINATION_PATTERNS = [
    r"प्रादेशिक समाचार",
    r"समाचार बुलेटिन",
    r"आकाशवाणी",
    r"दूरदर्शन",
    r"सब्सक्राइब",
    r"लाइक करें",
    r"कमेंट करें",
    r"घंटी दबाएं",
    r"बुलेटिन में आपका",
    r"welcome to",
    r"thank you for watching",
]


def detect_hallucination_or_loop(text: str) -> bool:
    """
    Detects known Whisper hallucination boilerplates and autoregressive phrase loops.
    Returns True if the text represents hallucinated speech rather than genuine user utterance.
    """
    if not text or not text.strip():
        return False

    clean = text.strip().lower()

    # 1. Known news broadcast / YouTube boilerplate
    for pattern in KNOWN_HALLUCINATION_PATTERNS:
        if re.search(pattern, clean, re.IGNORECASE):
            logger.warning(f"Whisper hallucination detected via pattern '{pattern}': '{text}'")
            return True

    # 2. Phrase repetition loops (e.g. 'प्रधानमंत्री नरेन्द्र मोदी के नेतृत्व में' repeating)
    words = clean.split()
    if len(words) >= 6:
        # Check ratio of unique words: repetitive loops exhibit very low lexical diversity
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.45:
            logger.warning(f"Whisper repetition loop detected (lexical diversity {unique_ratio:.2f} < 0.45): '{text[:60]}...'")
            return True

        # Check for repeated 2-gram, 3-gram, 4-gram phrases repeating 3 or more times
        for n in [2, 3, 4]:
            if len(words) >= n * 3:
                ngrams = [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]
                counts = Counter(ngrams)
                if counts and max(counts.values()) >= 3:
                    logger.warning(f"Whisper ngram loop detected ({n}-gram repeating >= 3 times): '{text[:60]}...'")
                    return True

    return False


class TranscriptionResult(BaseModel):
    """Normalized output from speech-to-text inference."""
    text: str = Field(..., description="Transcribed vernacular text (Devanagari script)")
    confidence: float = Field(..., description="Estimated transcription confidence in [0.0, 1.0]")
    language_code: str = Field(default="hi", description="ISO language code of transcription")
    low_confidence: bool = Field(
        default=False,
        description="True if confidence is below threshold (< 0.60), prompting repetition"
    )


class ASRProvider(ABC):
    """Abstract interface for speech recognition providers."""

    @abstractmethod
    def transcribe(self, audio_bytes: bytes, language_code: str = "hi") -> TranscriptionResult:
        """
        Transcribes raw audio bytes into text.
        Args:
            audio_bytes: Binary audio payload (WAV, MP3, OGG, FLAC).
            language_code: Target BCP-47 / ISO language code (default 'hi').
        Returns:
            TranscriptionResult object with text and confidence score.
        """
        pass


class VasistaWhisperProvider(ASRProvider):
    """
    ASR Provider implementing OpenAI Whisper fine-tuned for Hindi by vasista22.
    Loads once at startup and caches the pipeline for continuous multi-turn sessions.
    """

    _pipeline = None
    _loaded_model_name: Optional[str] = None

    def __init__(self, model_name: Optional[str] = None):
        self.requested_model = (
            model_name
            or os.environ.get("ASR_MODEL_NAME")
            or DEFAULT_PRIMARY_MODEL
        )
        self._ensure_model_loaded()

    def _ensure_model_loaded(self):
        """Loads the transformer ASR pipeline once at startup if not already loaded."""
        if VasistaWhisperProvider._pipeline is not None:
            return

        import torch
        from transformers import pipeline

        # Select hardware device: Apple Silicon (MPS), CUDA (NVIDIA), or CPU
        if torch.cuda.is_available():
            device = "cuda:0"
            torch_dtype = torch.float16
        elif torch.backends.mps.is_available():
            device = "mps"
            torch_dtype = torch.float32
        else:
            device = "cpu"
            torch_dtype = torch.float32

        logger.info(f"Initializing ASR pipeline with device={device}, dtype={torch_dtype}...")

        # Model resolution with fallbacks:
        # 1. Requested model (large-v2 or specified via env)
        # 2. vasista22/whisper-hindi-small
        # 3. openai/whisper-tiny
        models_to_try = [self.requested_model]
        if DEFAULT_SMALL_MODEL not in models_to_try:
            models_to_try.append(DEFAULT_SMALL_MODEL)
        if TINY_FALLBACK_MODEL not in models_to_try:
            models_to_try.append(TINY_FALLBACK_MODEL)

        last_error = None
        for m_name in models_to_try:
            try:
                logger.info(f"Attempting to load Whisper model: '{m_name}'...")
                pipe = pipeline(
                    task="automatic-speech-recognition",
                    model=m_name,
                    torch_dtype=torch_dtype,
                    device=device,
                )
                VasistaWhisperProvider._pipeline = pipe
                VasistaWhisperProvider._loaded_model_name = m_name
                logger.info(f"Successfully loaded ASR model: '{m_name}'")
                return
            except Exception as e:
                logger.warning(f"Failed to load '{m_name}': {e}. Trying fallback...")
                last_error = e

        raise RuntimeError(f"Could not initialize any Whisper ASR model. Error: {last_error}")

    def _decode_audio(self, audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """
        Decodes arbitrary audio bytes into float32 mono waveform at 16,000 Hz.
        """
        bio = io.BytesIO(audio_bytes)
        try:
            data, sample_rate = sf.read(bio, dtype="float32")
        except Exception:
            # Fallback decoding via pydub for webm / amr / unusual containers
            try:
                from pydub import AudioSegment
                bio.seek(0)
                seg = AudioSegment.from_file(bio)
                seg = seg.set_channels(1).set_frame_rate(TARGET_SAMPLE_RATE)
                samples = np.array(seg.get_array_of_samples()).astype(np.float32) / 32768.0
                return samples, TARGET_SAMPLE_RATE
            except Exception as e2:
                raise ValueError(f"Could not decode audio payload: {e2}")

        # Convert multi-channel to mono
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Resample to TARGET_SAMPLE_RATE if different
        if sample_rate != TARGET_SAMPLE_RATE and len(data) > 0:
            num_samples = int(len(data) * TARGET_SAMPLE_RATE / sample_rate)
            data = scipy.signal.resample(data, num_samples).astype(np.float32)
            sample_rate = TARGET_SAMPLE_RATE

        return data, sample_rate

    def transcribe(self, audio_bytes: bytes, language_code: str = "hi") -> TranscriptionResult:
        """Transcribes audio waveform into Hindi text with confidence estimation."""
        if not audio_bytes:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language_code=language_code,
                low_confidence=True
            )

        waveform, sr = self._decode_audio(audio_bytes)
        if len(waveform) == 0:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language_code=language_code,
                low_confidence=True
            )

        # Silence / Energy guard: Avoid Whisper hallucinations when the microphone feeds zero/low-energy audio
        rms_energy = float(np.sqrt(np.mean(waveform ** 2)))
        peak_amplitude = float(np.max(np.abs(waveform)))
        logger.info(f"ASR audio received: {len(waveform)} samples, sr={sr}, RMS energy={rms_energy:.6f}, Peak={peak_amplitude:.6f}")
        if rms_energy < 0.005 and peak_amplitude < 0.035:
            logger.warning(f"Audio energy below speech threshold (RMS {rms_energy:.6f} < 0.005, Peak {peak_amplitude:.6f} < 0.035). Treating as silence.")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language_code=language_code,
                low_confidence=True
            )

        # Run inference through pipeline
        pipe = VasistaWhisperProvider._pipeline
        gen_kwargs = {
            "no_repeat_ngram_size": 3,
            "repetition_penalty": 1.2,
        }
        if "vasista22" not in str(VasistaWhisperProvider._loaded_model_name).lower():
            gen_kwargs["language"] = language_code
            gen_kwargs["task"] = "transcribe"

        call_kwargs = {
            "return_timestamps": False,
            "generate_kwargs": gen_kwargs
        }

        try:
            result = pipe(
                {"raw": waveform, "sampling_rate": sr},
                **call_kwargs
            )
            raw_text = result.get("text", "").strip()

            # Clean up repetitive artifacts or leading punctuation
            clean_text = re.sub(r"\s+", " ", raw_text).strip()

            # Check for known Whisper hallucinations (news bulletins, repeat loops)
            if detect_hallucination_or_loop(clean_text):
                logger.warning(f"Rejecting hallucinated ASR text: '{clean_text}'")
                return TranscriptionResult(
                    text="",
                    confidence=0.0,
                    language_code=language_code,
                    low_confidence=True
                )

            # Heuristic confidence based on audio length and text output:
            # For whisper pipeline without direct logits exposure, confidence is computed
            # using audio duration vs text token count and presence of repetitive loops.
            audio_sec = len(waveform) / sr
            words = clean_text.split()
            if len(words) == 0:
                confidence = 0.0
            else:
                # Plausible speaking rate: ~1.5 - 3.5 words per second in spoken Hindi
                wps = len(words) / max(audio_sec, 0.5)
                if 0.5 <= wps <= 5.0:
                    base_conf = 0.92
                elif wps < 0.5:
                    base_conf = 0.75
                else:
                    base_conf = 0.65

                # Penalize repeated consecutive words (hallucination sign in Whisper)
                has_repeats = any(words[i] == words[i+1] for i in range(len(words)-1))
                if has_repeats:
                    base_conf -= 0.25

                confidence = max(0.1, min(0.99, base_conf))

            low_confidence = confidence < CONFIDENCE_THRESHOLD

            return TranscriptionResult(
                text=clean_text,
                confidence=round(confidence, 3),
                language_code=language_code,
                low_confidence=low_confidence
            )

        except Exception as e:
            logger.error(f"Inference error in Whisper transcribe: {e}")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language_code=language_code,
                low_confidence=True
            )


# Global singleton instance
_asr_instance: Optional[ASRProvider] = None


def get_asr_provider() -> ASRProvider:
    """Returns the singleton ASR provider instance."""
    global _asr_instance
    if _asr_instance is None:
        _asr_instance = VasistaWhisperProvider()
    return _asr_instance
