"""
Tier 1: Multimodal Perception & Acoustic Ingestion Layer
Includes Silero-VAD speech segmentation, Whisper ASR, verbal error recovery,
and asynchronous visual flowsheet parsing.
"""

from .audio_pipeline import (
    run_vad,
    transcribe_audio,
    verbal_error_recovery,
    run_perception_pipeline,
)
from .vlm_batch_parser import parse_visual_chart_async

__all__ = [
    "run_vad",
    "transcribe_audio",
    "verbal_error_recovery",
    "run_perception_pipeline",
    "parse_visual_chart_async",
]
