"""
Unit tests for AudioExtractor component.
"""

import os
import sys
import tempfile
import subprocess
import pytest

sys.path.insert(0, '/home/fit/Videos/lyrics_render')

from lyrics_render._audio import AudioExtractor


@pytest.fixture
def audio_extractor():
    """Create AudioExtractor instance."""
    return AudioExtractor()


@pytest.fixture
def test_audio_file():
    """Create a temporary test audio file using FFmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    cmd = [
        "ffmpeg", "-f", "lavfi",
        "-i", "sine=frequency=440:duration=1",
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
def test_video_file():
    """Create a temporary test video file using FFmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    cmd = [
        "ffmpeg", "-f", "lavfi",
        "-i", "sine=frequency=440:duration=2",
        "-f", "lavfi",
        "-i", "color=size=320x240:rate=1:duration=2:color=black",
        "-c:v", "libx264", "-c:a", "aac",
        "-t", "2", "-y", tmp_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip("FFmpeg not available or failed to generate test video")

    yield tmp_path

    try:
        os.unlink(tmp_path)
    except Exception:
        pass


class TestAudioExtractor:
    """Tests for AudioExtractor class."""

    def test_initialization(self, audio_extractor):
        """Test AudioExtractor initialization."""
        assert audio_extractor.ffmpeg_path == "ffmpeg"

    def test_initialization_custom_path(self):
        """Test AudioExtractor with custom FFmpeg path."""
        extractor = AudioExtractor(ffmpeg_path="/custom/ffmpeg")
        assert extractor.ffmpeg_path == "/custom/ffmpeg"

    def test_extract_audio_success(self, audio_extractor, test_video_file):
        """Test successful audio extraction from video."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        try:
            success = audio_extractor.extract_audio(test_video_file, output_path)
            assert success is True
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            try:
                os.unlink(output_path)
            except Exception:
                pass

    def test_extract_audio_invalid_input(self, audio_extractor):
        """Test audio extraction with invalid input file."""
        success = audio_extractor.extract_audio(
            "/nonexistent/file.mp4",
            "/tmp/output.wav"
        )
        assert success is False

    def test_extract_audio_custom_sample_rate(self, audio_extractor, test_video_file):
        """Test audio extraction with custom sample rate."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        try:
            success = audio_extractor.extract_audio(
                test_video_file,
                output_path,
                sample_rate=8000
            )
            assert success is True

            info = audio_extractor.get_audio_info(output_path)
            assert info is not None
            assert info["sample_rate"] == 8000
        finally:
            try:
                os.unlink(output_path)
            except Exception:
                pass

    def test_extract_audio_mono_channel(self, audio_extractor, test_video_file):
        """Test audio extraction with mono channel."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        try:
            success = audio_extractor.extract_audio(
                test_video_file,
                output_path,
                channels=1
            )
            assert success is True

            info = audio_extractor.get_audio_info(output_path)
            assert info is not None
            assert info["channels"] == 1
        finally:
            try:
                os.unlink(output_path)
            except Exception:
                pass

    def test_get_audio_info(self, audio_extractor, test_audio_file):
        """Test getting audio file information."""
        info = audio_extractor.get_audio_info(test_audio_file)

        assert info is not None
        assert "duration" in info
        assert "sample_rate" in info
        assert "channels" in info
        assert "codec" in info
        assert info["sample_rate"] == 16000
        assert info["channels"] == 1
        assert info["codec"] == "pcm_s16le"

    def test_get_audio_info_invalid_file(self, audio_extractor):
        """Test getting info for invalid audio file."""
        info = audio_extractor.get_audio_info("/nonexistent/file.wav")
        assert info is None

    def test_is_video_file_valid(self, audio_extractor, test_video_file):
        """Test checking if file is a valid video."""
        assert audio_extractor.is_video_file(test_video_file) is True

    def test_is_video_file_invalid(self, audio_extractor, test_audio_file):
        """Test checking if audio file is not a video."""
        assert audio_extractor.is_video_file(test_audio_file) is False

    def test_get_video_duration(self, audio_extractor, test_video_file):
        """Test getting video duration."""
        duration = audio_extractor.get_video_duration(test_video_file)
        assert duration is not None
        assert duration > 0
        assert duration <= 3

    def test_get_video_duration_invalid(self, audio_extractor):
        """Test getting duration of invalid video."""
        duration = audio_extractor.get_video_duration("/nonexistent/file.mp4")
        assert duration is None