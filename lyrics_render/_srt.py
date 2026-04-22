"""
Subtitle file generation (SRT and JSON formats).
"""

import json
import logging
from typing import List

from ._types import AudioSegment

logger = logging.getLogger(__name__)


class SRTGenerator:
    """Generate SRT subtitle files."""

    @staticmethod
    def generate_srt(segments: List[AudioSegment], output_path: str) -> bool:
        """
        Generate SRT subtitle file.

        Args:
            segments: List of AudioSegment objects with text
            output_path: Path to output SRT file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, 1):
                    if not segment.text or segment.text.strip() == "":
                        continue

                    start_str, end_str = segment.time_str("srt")

                    f.write(f"{i}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{segment.text}\n\n")

            logger.info(f"SRT file generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"SRT generation error: {e}")
            return False

    @staticmethod
    def generate_json(segments: List[AudioSegment], output_path: str) -> bool:
        """
        Generate JSON file with transcription results.

        Args:
            segments: List of AudioSegment objects with text
            output_path: Path to output JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            data = []
            for segment in segments:
                if segment.text:
                    data.append({
                        "start": segment.start_time,
                        "end": segment.end_time,
                        "duration": segment.duration,
                        "text": segment.text
                    })

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"JSON file generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"JSON generation error: {e}")
            return False

    @staticmethod
    def validate_srt(srt_path: str) -> bool:
        """
        Validate an SRT file format.

        Args:
            srt_path: Path to SRT file to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                return False

            blocks = content.strip().split('\n\n')
            for block in blocks:
                lines = block.split('\n')
                if len(lines) < 3:
                    return False
                if not lines[0].strip().isdigit():
                    return False
                if '-->' not in lines[1]:
                    return False

            return True

        except Exception:
            return False