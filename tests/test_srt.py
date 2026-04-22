"""
Unit tests for SRTGenerator component.
"""

import os
import sys
import tempfile
import json
import pytest

sys.path.insert(0, '/home/fit/Videos/lyrics_render')

from lyrics_render._types import AudioSegment
from lyrics_render._srt import SRTGenerator


@pytest.fixture
def sample_segments():
    """Create sample AudioSegment objects for testing."""
    return [
        AudioSegment(0.0, 2.5, text="Hello, world!"),
        AudioSegment(3.0, 5.5, text="This is a test."),
        AudioSegment(6.0, 8.5, text="Third segment here."),
    ]


class TestSRTGenerator:
    """Tests for SRTGenerator class."""

    def test_generate_srt_basic(self, sample_segments):
        """Test basic SRT file generation."""
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name

        try:
            success = SRTGenerator.generate_srt(sample_segments, srt_path)
            assert success is True
            assert os.path.exists(srt_path)

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "1" in content
            assert "00:00:00,000 --> 00:00:02,500" in content
            assert "Hello, world!" in content
            assert "00:00:03,000 --> 00:00:05,500" in content
            assert "This is a test." in content
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass

    def test_generate_srt_empty_segments(self):
        """Test SRT generation with empty segment list."""
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name

        try:
            success = SRTGenerator.generate_srt([], srt_path)
            assert success is True

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert content == ""
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass

    def test_generate_srt_skips_empty_text(self):
        """Test that segments with empty text are skipped."""
        segments = [
            AudioSegment(0.0, 2.0, text="Valid text"),
            AudioSegment(2.0, 4.0, text=""),
            AudioSegment(4.0, 6.0, text="   "),
            AudioSegment(6.0, 8.0, text="More valid text"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name

        try:
            success = SRTGenerator.generate_srt(segments, srt_path)
            assert success is True

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.strip().split('\n\n')
            assert len(lines) == 2

            assert "Valid text" in content
            assert "More valid text" in content
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass

    def test_generate_srt_timing_format(self):
        """Test SRT timing format is correct."""
        segments = [
            AudioSegment(1.234, 5.678, text="Test timing"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name

        try:
            SRTGenerator.generate_srt(segments, srt_path)

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "00:00:01,234 --> 00:00:05,678" in content
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass

    def test_generate_srt_large_times(self):
        """Test SRT with times over an hour."""
        segments = [
            AudioSegment(3661.5, 3723.25, text="Over an hour"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name

        try:
            SRTGenerator.generate_srt(segments, srt_path)

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "01:01:01,500 --> 01:02:03,250" in content
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass

    def test_generate_json_basic(self, sample_segments):
        """Test basic JSON file generation."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            json_path = tmp.name

        try:
            success = SRTGenerator.generate_json(sample_segments, json_path)
            assert success is True
            assert os.path.exists(json_path)

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert len(data) == 3

            assert data[0]["start"] == 0.0
            assert data[0]["end"] == 2.5
            assert data[0]["duration"] == 2.5
            assert data[0]["text"] == "Hello, world!"

            assert data[1]["start"] == 3.0
            assert data[1]["end"] == 5.5
            assert data[2]["start"] == 6.0
        finally:
            try:
                os.unlink(json_path)
            except Exception:
                pass

    def test_generate_json_skips_empty_text(self):
        """Test that JSON generation skips segments with empty text."""
        segments = [
            AudioSegment(0.0, 2.0, text="Valid"),
            AudioSegment(2.0, 4.0, text=""),
        ]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            json_path = tmp.name

        try:
            success = SRTGenerator.generate_json(segments, json_path)
            assert success is True

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["text"] == "Valid"
        finally:
            try:
                os.unlink(json_path)
            except Exception:
                pass

    def test_validate_srt_valid(self, sample_segments):
        """Test SRT validation with valid file."""
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name

        try:
            SRTGenerator.generate_srt(sample_segments, srt_path)
            assert SRTGenerator.validate_srt(srt_path) is True
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass

    def test_validate_srt_empty_file(self):
        """Test SRT validation with empty file."""
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name
            with open(srt_path, 'w') as f:
                f.write("")

        try:
            assert SRTGenerator.validate_srt(srt_path) is False
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass

    def test_validate_srt_invalid_format(self):
        """Test SRT validation with invalid format."""
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name
            with open(srt_path, 'w') as f:
                f.write("not a valid srt file\nwith bad format")

        try:
            assert SRTGenerator.validate_srt(srt_path) is False
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass

    def test_srt_output_format(self, sample_segments):
        """Test that SRT output follows exact format specification."""
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as tmp:
            srt_path = tmp.name

        try:
            SRTGenerator.generate_srt(sample_segments, srt_path)

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            expected = """1
00:00:00,000 --> 00:00:02,500
Hello, world!

2
00:00:03,000 --> 00:00:05,500
This is a test.

3
00:00:06,000 --> 00:00:08,500
Third segment here.
"""
            assert content == expected
        finally:
            try:
                os.unlink(srt_path)
            except Exception:
                pass