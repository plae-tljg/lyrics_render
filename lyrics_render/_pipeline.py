"""
Main lyrics render pipeline coordinating all components.
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from ._types import AudioSegment, PipelineConfig
from ._audio import AudioExtractor
from ._vad import VADSegmenter
from ._asr import ASRTranscriber
from ._srt import SRTGenerator

logger = logging.getLogger(__name__)


class LyricsRenderPipeline:
    """Main pipeline for lyrics rendering."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pipeline with configuration.

        Args:
            config: Pipeline configuration dictionary
        """
        self.config = config or {}

        self.audio_extractor = AudioExtractor(
            ffmpeg_path=self.config.get("ffmpeg_path", "ffmpeg")
        )

        self.vad_segmenter = VADSegmenter(
            aggressiveness=self.config.get("vad_aggressiveness", 3),
            sample_rate=self.config.get("sample_rate", 16000)
        )

        self.asr_transcriber = ASRTranscriber(
            model_name=self.config.get("model_name"),
            device=self.config.get("device", "cpu"),
            language=self.config.get("language", "auto")
        )

        self.srt_generator = SRTGenerator()

        self.temp_dir = tempfile.mkdtemp(prefix="lyrics_render_")
        logger.info(f"Using temporary directory: {self.temp_dir}")

    def process(self, video_path: str, output_path: Optional[str] = None) -> bool:
        """
        Process video file and generate subtitles.

        Args:
            video_path: Path to input video file
            output_path: Path to output SRT file (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"Input file not found: {video_path}")
                return False

            if output_path is None:
                video_stem = Path(video_path).stem
                output_path = str(Path(video_path).parent / f"{video_stem}.srt")

            logger.info(f"Starting lyrics render pipeline")
            logger.info(f"Input: {video_path}")
            logger.info(f"Output: {output_path}")

            audio_path = os.path.join(self.temp_dir, "extracted_audio.wav")
            logger.info("Step 1: Extracting audio from video...")
            if not self.audio_extractor.extract_audio(video_path, audio_path):
                logger.error("Audio extraction failed")
                return False

            audio_info = self.audio_extractor.get_audio_info(audio_path)
            if audio_info:
                logger.info(f"Audio info: {audio_info['duration']:.2f}s, "
                          f"{audio_info['sample_rate']}Hz, {audio_info['channels']} channels")

            logger.info("Step 2: Segmenting audio using VAD...")
            segments = self.vad_segmenter.segment_audio(
                audio_path,
                min_segment_duration=self.config.get("min_segment_duration", 0.5),
                max_segment_duration=self.config.get("max_segment_duration", 10.0),
                merge_gap=self.config.get("merge_gap", 0.3)
            )

            if not segments:
                logger.warning("No speech segments detected")
                if audio_info:
                    segments = [AudioSegment(0, audio_info["duration"])]
                else:
                    segments = [AudioSegment(0, 60)]

            logger.info(f"Detected {len(segments)} segments for transcription")

            logger.info("Step 3: Transcribing segments using ASR...")
            transcribed_segments = self.asr_transcriber.transcribe_segments(
                audio_path,
                segments,
                batch_size=self.config.get("batch_size", 1)
            )

            valid_segments = [s for s in transcribed_segments if s.text and s.text.strip()]
            logger.info(f"Successfully transcribed {len(valid_segments)}/{len(segments)} segments")

            if not valid_segments:
                logger.warning("No valid transcriptions generated")
                with open(output_path, 'w') as f:
                    f.write("")
                logger.info(f"Empty SRT file created: {output_path}")
                return True

            logger.info("Step 4: Generating SRT file...")
            if not self.srt_generator.generate_srt(valid_segments, output_path):
                logger.error("SRT generation failed")
                return False

            json_output = output_path.replace('.srt', '.json')
            if self.config.get("generate_json", False):
                self.srt_generator.generate_json(valid_segments, json_output)

            if not self.config.get("keep_temp", False):
                self._cleanup()

            logger.info(f"Pipeline completed successfully!")
            logger.info(f"Total segments: {len(valid_segments)}")

            total_duration = sum(s.duration for s in valid_segments)
            total_text = sum(len(s.text) for s in valid_segments if s.text)
            logger.info(f"Total speech duration: {total_duration:.2f}s")
            logger.info(f"Total characters transcribed: {total_text}")

            return True

        except Exception as e:
            logger.error(f"Pipeline processing error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _cleanup(self):
        """Clean up temporary files and directory."""
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        if getattr(self, 'config', None) and not self.config.get("keep_temp", False):
            self._cleanup()