"""
Command-line interface for lyrics render pipeline.
"""

import sys
import argparse
import logging
from typing import Dict, Any

from ._pipeline import LyricsRenderPipeline

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Lyrics Render Pipeline - Extract subtitles from video files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input video.mp4 --output subtitles.srt
  %(prog)s --input video.mp4 --language zh --device cuda --batch-size 4
  %(prog)s --input video.mp4 --vad-aggressiveness 2 --min-segment-duration 1.0
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input video file path"
    )

    parser.add_argument(
        "--output", "-o",
        help="Output SRT file path (default: same as input with .srt extension)"
    )

    parser.add_argument(
        "--language", "-l",
        default="auto",
        help="Language code for ASR (zh, en, ja, ko, etc., default: auto-detect)"
    )

    parser.add_argument(
        "--vad-aggressiveness",
        type=int,
        choices=[0, 1, 2, 3],
        default=3,
        help="VAD aggressiveness level 0-3 (default: 3, most aggressive)"
    )

    parser.add_argument(
        "--min-segment-duration",
        type=float,
        default=0.5,
        help="Minimum segment duration in seconds (default: 0.5)"
    )

    parser.add_argument(
        "--max-segment-duration",
        type=float,
        default=10.0,
        help="Maximum segment duration in seconds (default: 10.0)"
    )

    parser.add_argument(
        "--merge-gap",
        type=float,
        default=0.3,
        help="Maximum gap between speech segments to merge in seconds (default: 0.3)"
    )

    parser.add_argument(
        "--device",
        default="cpu",
        help="Device for ASR inference (cpu, cuda, cuda:0, etc., default: cpu)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch size for ASR inference (default: 1)"
    )

    parser.add_argument(
        "--model-name",
        default=None,
        help="FunASR model name (default: FunAudioLLM/Fun-ASR-Nano-2512)"
    )

    parser.add_argument(
        "--ffmpeg-path",
        default="ffmpeg",
        help="Path to ffmpeg executable (default: ffmpeg)"
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary audio files (default: False)"
    )

    parser.add_argument(
        "--generate-json",
        action="store_true",
        help="Generate JSON file with transcription results (default: False)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output"
    )

    return parser


def build_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration dictionary from parsed arguments."""
    config = {
        "ffmpeg_path": args.ffmpeg_path,
        "vad_aggressiveness": args.vad_aggressiveness,
        "min_segment_duration": args.min_segment_duration,
        "max_segment_duration": args.max_segment_duration,
        "merge_gap": args.merge_gap,
        "device": args.device,
        "batch_size": args.batch_size,
        "language": args.language,
        "keep_temp": args.keep_temp,
        "generate_json": args.generate_json,
        "sample_rate": 16000,
    }
    if args.model_name is not None:
        config["model_name"] = args.model_name
    return config


def main():
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    config = build_config(args)
    pipeline = LyricsRenderPipeline(config)

    try:
        success = pipeline.process(args.input, args.output)
        if success:
            logger.info("Lyrics render completed successfully!")
            return 0
        else:
            logger.error("Lyrics render failed!")
            return 1
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())