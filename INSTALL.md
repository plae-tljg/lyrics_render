# Lyrics Render Pipeline - Installation & Usage

## Google Colab (Recommended)

### 1. Install Dependencies

```python
!apt-get update && apt-get install -y ffmpeg
!pip install torch torchaudio
!pip install funasr pydub webrtcvad numpy scipy tqdm pytest yt-dlp
```

### 2. Upload Project

Upload the `lyrics_render/` folder to Colab, then:
```python
%cd lyrics_render
```

### 3. Download Test Video

```python
# "What Would Happen If You Didn't Sleep?" - 5 min, clear speech
!yt-dlp -f "best[height<=720]" -o "test_video.mp4" "https://www.youtube.com/watch?v=dqONk48l5vY"
```

### 4. Run Pipeline

**CPU Mode (slower, ~2-5x realtime):**
```python
!python -m lyrics_render --input test_video.mp4 --output subtitles.srt --language en --device cpu
```

**GPU Mode (faster, ~10-20x realtime) - RECOMMENDED:**
```python
!python -m lyrics_render --input test_video.mp4 --output subtitles.srt --language en --device cuda
```

### 5. View Results

```python
%cat subtitles.srt
```

---

## Local Installation

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y ffmpeg python3 python3-venv

# macOS
brew install ffmpeg python3

# Windows
# Download from: python.org and ffmpeg.org
```

### Python Setup

```bash
python3 -m venv venv
source venv/bin/activate

pip install torch torchaudio
pip install funasr pydub webrtcvad numpy scipy tqdm pytest
```

### Run

```bash
python -m lyrics_render --input video.mp4 --output subtitles.srt
```

---

## GPU vs CPU

| Mode | Speed | Memory | Best For |
|------|-------|--------|----------|
| CPU | 2-5x realtime | ~1-2GB | Testing, short videos |
| GPU (CUDA) | 10-20x realtime | ~2-4GB | Long videos, production |

Colab typically provides free GPU access - **use GPU for best performance**.

---

## Testing Workflow

### Run Unit Tests

```bash
python -m pytest tests/ -v
```

### Process Video with GPU

```bash
python -m lyrics_render \
  --input test_video.mp4 \
  --output subtitles.srt \
  --language en \
  --device cuda
```

### Process Video with CPU

```bash
python -m lyrics_render \
  --input test_video.mp4 \
  --output subtitles.srt \
  --language en \
  --device cpu
```

### Verify Output

```bash
# View subtitles
head -50 subtitles.srt

# Count entries
grep -c "^[[:digit:]]*$" subtitles.srt

# Check video duration
ffprobe -i test_video.mp4 -show_entries format=duration -v quiet -of csv="p=0"
```

### Step 5: Burn Subtitles into Video (Optional)

Merge the generated SRT file with your video:

```bash
# Burn subtitles into video (hardcoded subtitles)
ffmpeg -i test_video.mp4 -vf subtitles=subtitles.srt -c:a copy output_with_subs.mp4

# If the video already has audio, preserve it with -map
ffmpeg -i test_video.mp4 -vf subtitles=subtitles.srt -c:a copy -map 0:a? output.mp4
```

---

## Troubleshooting

### FFmpeg not found
```bash
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg       # macOS
```

### CUDA out of memory
```bash
# Use smaller batch size or CPU
python -m lyrics_render --input video.mp4 --device cpu --batch-size 1
```

### Model download fails
```python
from funasr import AutoModel
model = AutoModel(model='FunAudioLLM/Fun-ASR-Nano-2512', trust_remote_code=True)
```

### VAD sensitivity
```bash
# Try different levels (0=least, 3=most aggressive)
python -m lyrics_render --input video.mp4 --vad-aggressiveness 2
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
│   ├── test_types.py
│   ├── test_audio.py
│   ├── test_vad.py
│   └── test_srt.py
├── docs/                     # Documentation (Chinese and English)
├── README.md                # Chinese overview (this repo uses Chinese as default)
├── README_EN.md             # English overview
└── INSTALL.md               # This documentation (English)
```
