"""
Automatic Speech Recognition (ASR) using FunASR.
"""

import os
import tempfile
import logging
from typing import List
from pydub import AudioSegment

from ._types import AudioSegment as AudioSegmentType

logger = logging.getLogger(__name__)


class ASRTranscriber:
    """Transcribe audio segments using FunASR."""

    DEFAULT_MODEL = "FunAudioLLM/Fun-ASR-Nano-2512"

    def __init__(self, model_name: str = None,
                 device: str = "cpu",
                 language: str = "auto"):
        """
        Initialize ASR transcriber.

        Args:
            model_name: FunASR model name (default: FunAudioLLM/Fun-ASR-Nano-2512)
            device: Device to run inference on (cpu, cuda, cuda:0, etc.)
            language: Language code for ASR
        """
        if model_name is None:
            model_name = self.DEFAULT_MODEL

        try:
            from funasr.models.fun_asr_nano.model import FunASRNano
            from funasr.register import tables
            tables.model_classes["FunASRNano"] = FunASRNano
            from funasr import AutoModel

            logger.info(f"Loading ASR model: {model_name}")

            # Try loading without revision first (let funasr auto-detect)
            try:
                self.model = AutoModel(
                    model=model_name,
                    device=device,
                    disable_update=True,
                    trust_remote_code=True
                )
            except Exception:
                # Fallback: try with model dir
                self.model = AutoModel(
                    model=model_name,
                    model_revision="master",
                    device=device,
                    disable_update=True,
                    trust_remote_code=True
                )

            self.device = device
            self.language = language
            logger.info(f"ASR model loaded successfully on {device}")

        except ImportError:
            logger.error("funasr not installed. Install with: pip install funasr")
            raise
        except Exception as e:
            logger.error(f"Failed to load ASR model: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load ASR model: {e}")
            raise

    def transcribe_segments(self, audio_path: str,
                            segments: List[AudioSegmentType],
                            batch_size: int = 1) -> List[AudioSegmentType]:
        """
        Transcribe audio segments.

        Args:
            audio_path: Path to audio file
            segments: List of AudioSegment objects
            batch_size: Batch size for inference

        Returns:
            List of AudioSegment objects with text populated
        """
        try:
            audio = AudioSegment.from_file(audio_path)

            transcribed_segments = []
            total_batches = (len(segments) + batch_size - 1) // batch_size

            for i in range(0, len(segments), batch_size):
                batch = segments[i:i + batch_size]
                batch_num = i // batch_size + 1
                logger.info(f"Transcribing batch {batch_num}/{total_batches}")

                for segment in batch:
                    start_ms = int(segment.start_time * 1000)
                    end_ms = int(segment.end_time * 1000)
                    segment_audio = audio[start_ms:end_ms]

                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp_path = tmp.name
                        segment_audio.export(tmp_path, format="wav")

                    try:
                        result = self.model.generate(
                            input=tmp_path,
                            language=self.language,
                            batch_size=batch_size
                        )

                        if result and len(result) > 0:
                            text = result[0].get("text", "").strip()
                            segment.text = text
                            logger.debug(f"Segment {segment.start_time:.2f}-{segment.end_time:.2f}: {text}")
                        else:
                            segment.text = ""
                            logger.warning(f"No transcription for segment {segment.start_time:.2f}-{segment.end_time:.2f}")

                    except Exception as e:
                        logger.error(f"Transcription error for segment {segment.start_time:.2f}-{segment.end_time:.2f}: {e}")
                        segment.text = ""

                    finally:
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass

                    transcribed_segments.append(segment)

            return transcribed_segments

        except Exception as e:
            logger.error(f"ASR transcription error: {e}")
            raise