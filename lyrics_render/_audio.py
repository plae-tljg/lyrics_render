"""
Audio extraction from video files using FFmpeg.
"""

import os
import subprocess
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AudioExtractor:
    """Extract audio from video files using FFmpeg."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def extract_audio(self, video_path: str, output_path: str,
                      sample_rate: int = 16000, channels: int = 1) -> bool:
        """
        Extract audio from video file to WAV format.

        Args:
            video_path: Path to input video file
            output_path: Path to output WAV file
            sample_rate: Output sample rate (Hz)
            channels: Number of audio channels (1 for mono)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-ac", str(channels),
                "-ar", str(sample_rate),
                "-acodec", "pcm_s16le",
                "-y",
                output_path
            ]

            logger.info(f"Extracting audio from {video_path} to {output_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Audio extraction successful: {output_path}")
                return True
            else:
                logger.error("Audio extraction failed: output file not created")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            return False

    def get_audio_info(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """Get audio file information using FFprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-select_streams", "a",
                audio_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            info = json.loads(result.stdout)
            if info.get("streams"):
                stream = info["streams"][0]
                return {
                    "duration": float(stream.get("duration", 0)),
                    "sample_rate": int(stream.get("sample_rate", 0)),
                    "channels": int(stream.get("channels", 0)),
                    "codec": stream.get("codec_name", "")
                }
            return None

        except Exception as e:
            logger.warning(f"Could not get audio info: {e}")
            return None

    def is_video_file(self, video_path: str) -> bool:
        """Check if file is a valid video file using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v",
                "-show_entries", "stream=codec_type",
                "-of", "json",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            return len(info.get("streams", [])) > 0
        except Exception:
            return False

    def get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration in seconds."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            return float(info.get("format", {}).get("duration", 0))
        except Exception:
            return None