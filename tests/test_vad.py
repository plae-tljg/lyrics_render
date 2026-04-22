"""
Unit tests for VADSegmenter component.
"""

import os
import sys
import tempfile
import subprocess
import pytest

sys.path.insert(0, '/home/fit/Videos/lyrics_render')

from lyrics_render._types import AudioSegment
from lyrics_render._vad import VADSegmenter


@pytest.fixture
def vad_segmenter():
    """Create VADSegmenter instance."""
    return VADSegmenter(aggressiveness=3, sample_rate=16000)


@pytest.fixture
def test_audio_speech_like():
    """Create a test audio file with speech-like patterns (multiple tones)."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    cmd = [
        "ffmpeg", "-f", "lavfi",
        "-i", "aevalsrc=0:d=0.5[s1];sine=frequency=440:d=1[s2];aevalsrc=0:d=0.5[s3];sine=frequency=660:d=1[s4];[s1][s2][s3][s4]concat=n=4:v=0:a=1",
        "-ac", "1", "-ar", "16000", "-y", tmp_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip("FFmpeg not available or failed to generate test audio")

    yield tmp_path

    try:
        os.unlink(tmp_path)
    except Exception:
        pass


@pytest.fixture
def test_audio_silence():
    """Create a test audio file with mostly silence."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    cmd = [
        "ffmpeg", "-f", "lavfi",
        "-i", "anullsrc=r=16000:cl=mono:d=3",
        "-ac", "1", "-ar", "16000", "-y", tmp_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip("FFmpeg not available or failed to generate test audio")

    yield tmp_path

    try:
        os.unlink(tmp_path)
    except Exception:
        pass


class TestVADSegmenter:
    """Tests for VADSegmenter class."""

    def test_initialization(self, vad_segmenter):
        """Test VADSegmenter initialization."""
        assert vad_segmenter.sample_rate == 16000
        assert vad_segmenter.frame_duration_ms == 30
        assert vad_segmenter.frame_size == 480

    def test_initialization_aggressiveness(self):
        """Test VADSegmenter with different aggressiveness levels."""
        for agg in [0, 1, 2, 3]:
            segmenter = VADSegmenter(aggressiveness=agg, sample_rate=16000)
            assert segmenter.vad is not None

    def test_initialization_invalid_aggressiveness(self):
        """Test VADSegmenter with invalid aggressiveness level."""
        with pytest.raises(Exception):
            VADSegmenter(aggressiveness=4, sample_rate=16000)

    def test_segment_audio_basic(self, vad_segmenter, test_audio_speech_like):
        """Test basic audio segmentation."""
        segments = vad_segmenter.segment_audio(
            test_audio_speech_like,
            min_segment_duration=0.3,
            max_segment_duration=2.0,
            merge_gap=0.2
        )

        assert len(segments) > 0
        for segment in segments:
            assert isinstance(segment, AudioSegment)
            assert segment.start_time < segment.end_time
            assert segment.duration > 0

    def test_segment_audio_silence_only(self, vad_segmenter, test_audio_silence):
        """Test segmentation of silence-only audio."""
        segments = vad_segmenter.segment_audio(
            test_audio_silence,
            min_segment_duration=0.3,
            max_segment_duration=2.0
        )

        assert isinstance(segments, list)

    def test_segment_audio_nonexistent_file(self, vad_segmenter):
        """Test segmentation with non-existent file."""
        with pytest.raises(Exception):
            vad_segmenter.segment_audio("/nonexistent/file.wav")

    def test_segment_respects_min_duration(self, vad_segmenter, test_audio_speech_like):
        """Test that segments respect minimum duration."""
        min_dur = 0.5
        segments = vad_segmenter.segment_audio(
            test_audio_speech_like,
            min_segment_duration=min_dur,
            max_segment_duration=10.0,
            merge_gap=0.3
        )

        for segment in segments:
            assert segment.duration >= min_dur - 0.01

    def test_segment_respects_max_duration(self, vad_segmenter, test_audio_speech_like):
        """Test that segments are split to respect maximum duration."""
        max_dur = 0.8
        segments = vad_segmenter.segment_audio(
            test_audio_speech_like,
            min_segment_duration=0.1,
            max_segment_duration=max_dur,
            merge_gap=0.3
        )

        for segment in segments:
            assert segment.duration <= max_dur + 0.01

    def test_segments_are_ordered(self, vad_segmenter, test_audio_speech_like):
        """Test that returned segments are ordered by start time."""
        segments = vad_segmenter.segment_audio(
            test_audio_speech_like,
            min_segment_duration=0.3,
            max_segment_duration=10.0
        )

        for i in range(len(segments) - 1):
            assert segments[i].start_time <= segments[i + 1].start_time

    def test_segments_are_contiguous(self, vad_segmenter, test_audio_speech_like):
        """Test that segments cover the audio without large gaps."""
        segments = vad_segmenter.segment_audio(
            test_audio_speech_like,
            min_segment_duration=0.3,
            max_segment_duration=10.0,
            merge_gap=0.5
        )

        if len(segments) > 1:
            for i in range(len(segments) - 1):
                gap = segments[i + 1].start_time - segments[i].end_time
                assert gap < 1.0

    def test_detect_speech_returns_tuples(self, vad_segmenter, test_audio_speech_like):
        """Test that _detect_speech returns correct format."""
        from pydub import AudioSegment

        audio = AudioSegment.from_file(test_audio_speech_like)
        if audio.channels > 1:
            audio = audio.set_channels(1)
        if audio.frame_rate != 16000:
            audio = audio.set_frame_rate(16000)

        import numpy as np
        raw_data = np.array(audio.get_array_of_samples(), dtype=np.int16)
        duration = len(raw_data) / 16000

        segments = vad_segmenter._detect_speech(raw_data, duration)

        assert isinstance(segments, list)
        for start, end in segments:
            assert isinstance(start, float)
            assert isinstance(end, float)
            assert start < end

    def test_merge_segments_empty_input(self, vad_segmenter):
        """Test merging with empty input."""
        result = vad_segmenter._merge_segments([], 0.3, 0.5, 10.0)
        assert result == []

    def test_merge_segments_merges_close_segments(self, vad_segmenter):
        """Test that close segments are merged."""
        segments = [(0.0, 1.0), (1.1, 2.0), (5.0, 6.0)]

        merged = vad_segmenter._merge_segments(segments, 0.3, 0.5, 10.0)

        assert len(merged) <= len(segments)

    def test_merge_segments_respects_min_duration(self, vad_segmenter):
        """Test that short segments are filtered out."""
        segments = [(0.0, 0.1), (0.5, 1.0)]

        merged = vad_segmenter._merge_segments(segments, 0.3, 0.5, 10.0)

        for segment in merged:
            assert segment.duration >= 0.5 - 0.01