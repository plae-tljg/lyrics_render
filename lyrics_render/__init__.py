"""
Lyrics Render Pipeline
A complete pipeline for extracting lyrics/subtitles from video files.
"""

from ._types import AudioSegment, PipelineConfig
from ._audio import AudioExtractor
from ._vad import VADSegmenter
from ._asr import ASRTranscriber
from ._srt import SRTGenerator
from ._pipeline import LyricsRenderPipeline
from ._cli import main as cli_main

__all__ = [
    "AudioSegment",
    "PipelineConfig",
    "AudioExtractor",
    "VADSegmenter",
    "ASRTranscriber",
    "SRTGenerator",
    "LyricsRenderPipeline",
    "cli_main",
]

__version__ = "1.0.0"