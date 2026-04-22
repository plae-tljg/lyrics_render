"""
Audio data types for lyrics render pipeline.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np


@dataclass
class AudioSegment:
    """Represents a segment of audio with timing information."""
    start_time: float
    end_time: float
    audio_data: Optional[np.ndarray] = None
    text: Optional[str] = None

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def time_str(self, time_format: str = "srt") -> Tuple[str, str]:
        """Convert times to string format."""
        def to_srt_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            milliseconds = int((secs - int(secs)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{milliseconds:03d}"

        if time_format == "srt":
            return to_srt_time(self.start_time), to_srt_time(self.end_time)
        else:
            return f"{self.start_time:.3f}", f"{self.end_time:.3f}"


@dataclass
class PipelineConfig:
    """Configuration for the lyrics render pipeline."""
    ffmpeg_path: str = "ffmpeg"
    vad_aggressiveness: int = 3
    sample_rate: int = 16000
    min_segment_duration: float = 0.5
    max_segment_duration: float = 10.0
    merge_gap: float = 0.3
    device: str = "cpu"
    batch_size: int = 1
    model_name: str = "iic/funasr_nano-2512"
    model_revision: str = "v2.0.4"
    language: str = "auto"
    keep_temp: bool = False
    generate_json: bool = False