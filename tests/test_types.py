"""
Unit tests for AudioSegment datatype.
"""

import pytest
import sys
sys.path.insert(0, '/home/fit/Videos/lyrics_render')

from lyrics_render._types import AudioSegment


class TestAudioSegment:
    """Tests for AudioSegment dataclass."""

    def test_creation(self):
        """Test basic AudioSegment creation."""
        segment = AudioSegment(start_time=0.0, end_time=2.5)
        assert segment.start_time == 0.0
        assert segment.end_time == 2.5
        assert segment.audio_data is None
        assert segment.text is None

    def test_duration_property(self):
        """Test duration property calculation."""
        segment = AudioSegment(start_time=1.0, end_time=3.5)
        assert segment.duration == 2.5

    def test_duration_zero(self):
        """Test duration of zero-length segment."""
        segment = AudioSegment(start_time=5.0, end_time=5.0)
        assert segment.duration == 0.0

    def test_time_str_srt_format(self):
        """Test SRT time string formatting."""
        segment = AudioSegment(start_time=1.5, end_time=3.756)
        start_str, end_str = segment.time_str("srt")

        assert start_str == "00:00:01,500"
        assert end_str == "00:00:03,756"

    def test_time_str_srt_hour_format(self):
        """Test SRT time string with hours."""
        segment = AudioSegment(start_time=3661.5, end_time=3723.123)
        start_str, end_str = segment.time_str("srt")

        assert start_str == "01:01:01,500"
        assert end_str == "01:02:03,123"

    def test_time_str_simple_format(self):
        """Test simple time string formatting."""
        segment = AudioSegment(start_time=1.234, end_time=5.678)
        start_str, end_str = segment.time_str("simple")

        assert start_str == "1.234"
        assert end_str == "5.678"

    def test_time_str_default_is_srt(self):
        """Test that default time format is SRT."""
        segment = AudioSegment(start_time=0.0, end_time=1.0)
        start_str, end_str = segment.time_str()

        assert "," in start_str
        assert "," in end_str

    def test_with_audio_data(self):
        """Test AudioSegment with audio data."""
        import numpy as np
        data = np.array([1, 2, 3, 4, 5], dtype=np.int16)
        segment = AudioSegment(start_time=0.0, end_time=1.0, audio_data=data)

        assert segment.audio_data is not None
        assert len(segment.audio_data) == 5

    def test_with_text(self):
        """Test AudioSegment with transcription text."""
        segment = AudioSegment(start_time=0.0, end_time=2.0, text="Hello world")

        assert segment.text == "Hello world"

    def test_immutable_times(self):
        """Test that times are not accidentally modified."""
        segment = AudioSegment(start_time=1.0, end_time=3.0)
        _ = segment.duration

        assert segment.start_time == 1.0
        assert segment.end_time == 3.0


class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        from lyrics_render._types import PipelineConfig

        config = PipelineConfig()

        assert config.ffmpeg_path == "ffmpeg"
        assert config.vad_aggressiveness == 3
        assert config.sample_rate == 16000
        assert config.min_segment_duration == 0.5
        assert config.max_segment_duration == 10.0
        assert config.merge_gap == 0.3
        assert config.device == "cpu"
        assert config.batch_size == 1
        assert config.model_name == "iic/funasr_nano-2512"
        assert config.language == "auto"
        assert config.keep_temp is False
        assert config.generate_json is False

    def test_custom_config(self):
        """Test custom configuration values."""
        from lyrics_render._types import PipelineConfig

        config = PipelineConfig(
            vad_aggressiveness=2,
            min_segment_duration=1.0,
            device="cuda",
            batch_size=4
        )

        assert config.vad_aggressiveness == 2
        assert config.min_segment_duration == 1.0
        assert config.device == "cuda"
        assert config.batch_size == 4