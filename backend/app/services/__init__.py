"""
Services package for YojanaVaani backend.
Contains business logic, baseline interview manager, speech services, OCR, and agent layers.
"""

from app.services.baseline_interview import (
    BASELINE_QUESTIONS,
    TOTAL_BASELINE_QUESTIONS,
    BaselineQuestion,
    get_baseline_questions,
    get_question_by_field,
    get_question_by_index,
)
from app.services.conversation_manager import ConversationManager
from app.services.asr_service import (
    ASRProvider,
    VasistaWhisperProvider,
    TranscriptionResult,
    get_asr_provider,
)
from app.services.tts_service import (
    TTSProvider,
    IndicTTSProvider,
    GoogleHindiTTSProvider,
    get_tts_provider,
)

__all__ = [
    "BASELINE_QUESTIONS",
    "TOTAL_BASELINE_QUESTIONS",
    "BaselineQuestion",
    "get_baseline_questions",
    "get_question_by_field",
    "get_question_by_index",
    "ConversationManager",
    "ASRProvider",
    "VasistaWhisperProvider",
    "TranscriptionResult",
    "get_asr_provider",
    "TTSProvider",
    "IndicTTSProvider",
    "GoogleHindiTTSProvider",
    "get_tts_provider",
]
