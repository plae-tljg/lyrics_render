# Lyrics Render Pipeline

Extract lyrics/subtitles from video files using ASR and VAD segmentation.

## The Problem

**Why does this project exist?**

When we needed to add subtitles to videos (like popular science content), we tried using LLMs like GPT to process transcripts and generate SRT files. However, we encountered several issues:

1. **LLMs hallucinate**: GPT-style models tend to "hallucinate" - they make up content, skip sections, or add things that weren't said. This is especially problematic for long-form content where accuracy matters.

2. **Context window limitations**: A 1-hour video produces ~15,000+ tokens of transcription. Even with 128K context windows, LLMs struggle to maintain perfect accuracy across such long sequences.

3. **Deterministic vs probabilistic**: Traditional programming with ASR output (timestamps, text segments) is more reliable than asking an LLM to "understand" the content - the latter can introduce subtle but critical errors.

4. **Cost and speed**: Calling LLM APIs for long transcripts is expensive and slow. A purely programmatic approach is faster and free.

**Our solution**: Use ASR for accurate transcription with timestamps, then do simple deterministic operations to produce subtitles. No LLM needed for the subtitle generation step.

---

## How It Works

### Pipeline Overview

```
Video File (.mp4)
     │
     ▼
┌─────────────────┐
│ AudioExtractor  │  Extract audio to 16kHz WAV using FFmpeg
│ (FFmpeg)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  VADSegmenter   │  Voice Activity Detection splits audio
│ (WebRTC VAD)    │  into speech segments with timestamps
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ASRTranscriber  │  FunASR-nano-2512 transcribes each
│   (FunASR)      │  segment to text
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SRTGenerator  │  Combine timestamps + text into
│   (Our code)    │  standard SRT subtitle format
└────────┬────────┘
         │
         ▼
  Subtitles (.srt)
```

### Component Details

#### 1. AudioExtractor
- Uses FFmpeg to extract audio track from video
- Converts to 16kHz mono WAV (required by VAD and ASR)
- Stores in temporary directory for pipeline processing

#### 2. VADSegmenter (Voice Activity Detection)
- Uses WebRTC VAD to detect speech vs silence
- Aggressiveness levels 0-3 control sensitivity
- Merges segments that are close together (gap < 0.3s default)
- Respects min/max segment duration constraints

**Why VAD?**: Directly transcribing a 1-hour video is memory-intensive. VAD breaks it into manageable segments (~0.5-10 seconds each), allowing batch processing.

#### 3. ASRTranscriber (Automatic Speech Recognition)
- Uses FunASR-nano-2512 model
- For each VAD segment:
  - Extracts audio slice
  - Runs ASR inference
  - Returns text transcription

**FunASR output format**:
```python
{
    "text": "Hello world",      # Transcribed text
    "text_notypo": "Hello world",  # Without typo correction (if enabled)
    "text_cs": "你好世界"         # Chinese text (if applicable)
}
```

#### 4. SRTGenerator
- Converts segments to standard SRT format:
```
1
00:00:01,000 --> 00:00:03,500
Hello world

2
00:00:04,200 --> 00:00:07,800
This is the second subtitle.
```
- Also supports JSON output with structured data

---

## Handling Long Videos (1+ hours)

### Challenges

1. **Memory**: ASR model must stay in memory throughout
2. **VAD accuracy**: Background noise in long videos can cause false positives
3. **Segment management**: Thousands of segments need proper handling

### Our Approach

1. **VAD-first segmentation**: Rather than processing continuously, we segment first, then transcribe in batches. This prevents memory buildup.

2. **Segment duration limits**: `max_segment_duration=10.0` ensures no single segment is too long for the ASR model context.

3. **Streaming-ready design**: The pipeline processes segment by segment, so memory usage stays bounded regardless of video length.

### Recommendations for Long Videos

```bash
# Use GPU for faster processing
python -m lyrics_render --input long_video.mp4 --output subs.srt --device cuda

# Adjust VAD for noisy content
python -m lyrics_render --input long_video.mp4 --vad-aggressiveness 2

# Keep temp files for debugging
python -m lyrics_render --input long_video.mp4 --keep-temp
```

---

## Why Not Just Use Whisper API?

| Factor | Our Pipeline | Whisper API |
|--------|--------------|-------------|
| Cost | Free (local model) | $0.006/min |
| Privacy | Everything local | Data sent to API |
| Timestamps | Native SRT-ready | Need to align separately |
| Long videos | Handles any length | Context limits |
| Customization | Fully customizable | Limited |

---

## Usage

```bash
# Basic (CPU)
python -m lyrics_render --input video.mp4 --output subtitles.srt

# GPU (recommended for long videos)
python -m lyrics_render --input video.mp4 --output subtitles.srt --device cuda

# With language hint (faster)
python -m lyrics_render --input video.mp4 --output subtitles.srt --language en
```

### Burn Subtitles into Video

After generating the SRT file, you can burn the subtitles into the video:

```bash
# Hardcoded subtitles (burn into video)
ffmpeg -i video.mp4 -vf subtitles=subtitles.srt -c:a copy output_with_subs.mp4

# If video already has audio track
ffmpeg -i video.mp4 -vf subtitles=subtitles.srt -c:a copy -map 0:a? output.mp4
```

---

## Project Structure

```
lyrics_render/
├── lyrics_render/           # Main package
│   ├── __init__.py          # Exports
│   ├── __main__.py         # CLI entry (python -m lyrics_render)
│   ├── _types.py           # AudioSegment, PipelineConfig
│   ├── _audio.py           # AudioExtractor
│   ├── _vad.py             # VADSegmenter
│   ├── _asr.py             # ASRTranscriber
│   ├── _srt.py             # SRTGenerator
│   ├── _pipeline.py        # LyricsRenderPipeline
│   └── _cli.py             # CLI argument parser
├── tests/                   # Unit tests
├── docs/                    # Documentation
│   ├── README_EN.md        # This file
│   └── INSTALL_EN.md       # Installation guide
├── README.md               # Chinese overview
├── README_EN.md            # English overview
├── INSTALL.md              # Chinese installation guide
└── install.sh              # Setup script
```