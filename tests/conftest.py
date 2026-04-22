"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys

sys.path.insert(0, '/home/fit/Videos/lyrics_render')


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_ffmpeg: marks tests that require FFmpeg"
    )
    config.addinivalue_line(
        "markers", "requires_asr: marks tests that require ASR model download"
    )