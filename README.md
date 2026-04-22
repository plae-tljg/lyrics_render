# 歌词渲染流水线 (Lyrics Render Pipeline)

使用 ASR 和 VAD 分割从视频文件中提取歌词/字幕。

## 快速开始

```bash
# 克隆并安装
git clone https://github.com/your-repo/lyrics_render.git
cd lyrics_render
bash install.sh
source venv/bin/activate

# 运行流水线
python -m lyrics_render --input video.mp4 --output subtitles.srt --device cuda
```

## 功能

- **音频提取** - 使用 FFmpeg 从视频提取 WAV 音频
- **语音活动检测** - 使用 WebRTC VAD 分割语音段落
- **语音识别** - 使用 FunASR-nano-2512 转录
- **字幕生成** - 生成 SRT 字幕文件

## 文档

- [安装指南](INSTALL.md) - 详细安装说明（英文）
- [详细文档](docs/) - 包含中英文完整文档
- [问题背景与设计原理](docs/README.md) - 中文详细说明
- [English Documentation](docs/README_EN.md) - English documentation