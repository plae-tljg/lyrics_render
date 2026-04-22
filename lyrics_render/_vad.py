"""
Voice Activity Detection (VAD) for audio segmentation.
"""

import logging
from typing import List, Tuple
import numpy as np
from pydub import AudioSegment

from ._types import AudioSegment as AudioSegmentType

logger = logging.getLogger(__name__)


class VADSegmenter:
    """Segment audio using Voice Activity Detection."""

    def __init__(self, aggressiveness: int = 3, sample_rate: int = 16000):
        """
        Initialize VAD segmenter.

        Args:
            aggressiveness: VAD aggressiveness level (0-3, 3 most aggressive)
            sample_rate: Audio sample rate in Hz
        """
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(aggressiveness)
            self.sample_rate = sample_rate
            self.frame_duration_ms = 30
            self.frame_size = int(sample_rate * self.frame_duration_ms / 1000)
            logger.info(f"VAD initialized with aggressiveness {aggressiveness}")
        except ImportError:
            logger.error("webrtcvad not installed. Install with: pip install webrtcvad")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize VAD: {e}")
            raise

    def segment_audio(self, audio_path: str,
                      min_segment_duration: float = 0.5,
                      max_segment_duration: float = 10.0,
                      merge_gap: float = 0.3) -> List[AudioSegmentType]:
        """
        Segment audio file using VAD.

        Args:
            audio_path: Path to audio file
            min_segment_duration: Minimum segment duration in seconds
            max_segment_duration: Maximum segment duration in seconds
            merge_gap: Maximum gap between speech segments to merge (seconds)

        Returns:
            List of AudioSegment objects
        """
        try:
            logger.info(f"Loading audio file: {audio_path}")
            audio = AudioSegment.from_file(audio_path)

            if audio.channels > 1:
                audio = audio.set_channels(1)
            if audio.frame_rate != self.sample_rate:
                audio = audio.set_frame_rate(self.sample_rate)

            raw_data = np.array(audio.get_array_of_samples(), dtype=np.int16)
            duration = len(raw_data) / self.sample_rate

            logger.info("Performing VAD segmentation...")
            speech_segments = self._detect_speech(raw_data, duration)

            merged_segments = self._merge_segments(
                speech_segments,
                merge_gap,
                min_segment_duration,
                max_segment_duration
            )

            logger.info(f"Detected {len(merged_segments)} speech segments")
            return merged_segments

        except Exception as e:
            logger.error(f"VAD segmentation error: {e}")
            raise

    def _detect_speech(self, audio_data: np.ndarray, duration: float) -> List[Tuple[float, float]]:
        """Detect speech segments in audio data."""
        frames = []
        num_frames = len(audio_data) // self.frame_size

        for i in range(num_frames):
            start = i * self.frame_size
            end = start + self.frame_size
            frame = audio_data[start:end]

            if len(frame) < self.frame_size:
                frame = np.pad(frame, (0, self.frame_size - len(frame)), 'constant')

            try:
                is_speech = self.vad.is_speech(frame.tobytes(), self.sample_rate)
                frames.append((i * self.frame_duration_ms / 1000.0, is_speech))
            except Exception:
                frames.append((i * self.frame_duration_ms / 1000.0, False))

        segments = []
        in_speech = False
        speech_start = 0

        for time, is_speech in frames:
            if is_speech and not in_speech:
                speech_start = time
                in_speech = True
            elif not is_speech and in_speech:
                segments.append((speech_start, time))
                in_speech = False

        if in_speech:
            segments.append((speech_start, duration))

        return segments

    def _merge_segments(self, segments: List[Tuple[float, float]],
                        max_gap: float,
                        min_duration: float,
                        max_duration: float) -> List[AudioSegmentType]:
        """Merge close segments and apply duration constraints."""
        if not segments:
            return []

        segments.sort(key=lambda x: x[0])

        merged = []
        current_start, current_end = segments[0]

        for start, end in segments[1:]:
            if start - current_end <= max_gap:
                current_end = end
            else:
                if current_end - current_start >= min_duration:
                    merged.append(AudioSegmentType(current_start, current_end))
                current_start, current_end = start, end

        if current_end - current_start >= min_duration:
            merged.append(AudioSegmentType(current_start, current_end))

        final_segments = []
        for segment in merged:
            if segment.duration > max_duration:
                num_splits = int(np.ceil(segment.duration / max_duration))
                split_duration = segment.duration / num_splits
                for i in range(num_splits):
                    split_start = segment.start_time + i * split_duration
                    split_end = min(segment.start_time + (i + 1) * split_duration, segment.end_time)
                    final_segments.append(AudioSegmentType(split_start, split_end))
            else:
                final_segments.append(segment)

        return final_segments