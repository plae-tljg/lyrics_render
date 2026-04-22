# Lyrics Render Pipeline

Extract lyrics/subtitles from video files using ASR and VAD segmentation.

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-repo/lyrics_render.git
cd lyrics_render
bash install.sh
source venv/bin/activate

# Run pipeline
python -m lyrics_render --input video.mp4 --output subtitles.srt --device cuda
```

## Features

- **Audio Extraction** - Extract audio from video to WAV using FFmpeg
- **Voice Activity Detection** - Segment speech using WebRTC VAD
- **Speech Recognition** - Transcribe using FunASR-nano-2512
- **Subtitle Generation** - Generate SRT subtitle files

## Documentation

- [Installation Guide](INSTALL.md) - Full setup instructions
- [Chinese Documentation](README.md) - 中文文档