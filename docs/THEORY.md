# 歌词渲染流水线 (Lyrics Render Pipeline)

使用 ASR 和 VAD 分割从视频文件中提取歌词/字幕。

## 问题背景

**为什么存在这个项目？**

当我们需要为视频（如科普视频）添加字幕时，我们尝试使用 GPT 等 LLM 来处理转录文本并生成 SRT 文件。然而，我们遇到了几个问题：

1. **LLM 会产生幻觉**：GPT 类模型容易"幻觉"——它们编造内容、跳过部分或添加不存在的内容。这对于需要准确性的长视频来说尤其成问题。

2. **上下文窗口限制**：1 小时视频产生约 15,000+ token 的转录。即使有 128K 上下文窗口，LLM 在这么长的序列中也难以保持完美准确性。

3. **确定性 vs 概率性**：对 ASR 输出（时间戳、文本段）进行传统编程比让 LLM"理解"内容更可靠——后者可能引入微妙但关键的错误。

4. **成本和速度**：为长转录调用 LLM API 既昂贵又缓慢。纯编程方法更快且免费。

**我们的解决方案**：使用 ASR 进行精确的带时间戳转录，然后进行简单的确定性操作来生成字幕。字幕生成步骤不需要 LLM。

---

## 工作原理

### 流水线概览

```
视频文件 (.mp4)
     │
     ▼
┌─────────────────┐
│ AudioExtractor  │  使用 FFmpeg 提取 16kHz WAV 音频
│   (FFmpeg)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  VADSegmenter   │  语音活动检测将音频分割成
│ (WebRTC VAD)    │  带时间戳的语音段
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ASRTranscriber  │  FunASR-nano-2512 转录每个
│   (FunASR)      │  段落的文本
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SRTGenerator  │  将时间戳 + 文本组合成
│   (我们的代码)  │  标准 SRT 字幕格式
└────────┬────────┘
         │
         ▼
  字幕文件 (.srt)
```

### 组件详情

#### 1. AudioExtractor（音频提取器）
- 使用 FFmpeg 从视频中提取音轨
- 转换为 16kHz 单声道 WAV（VAD 和 ASR 所需）
- 存储在临时目录中供流水线处理

#### 2. VADSegmenter（语音活动检测）
- 使用 WebRTC VAD 检测语音与静音
- 灵敏度级别 0-3 控制敏感性
- 合并接近的段落（默认间隔 < 0.3 秒）
- 遵守最小/最大段落持续时间限制

**为什么用 VAD？**：直接转录 1 小时视频会占用大量内存。VAD 将其分成可管理的段落（每个约 0.5-10 秒），允许批处理。

#### 3. ASRTranscriber（自动语音识别）
- 使用 FunASR-nano-2512 模型
- 对于每个 VAD 段落：
  - 提取音频片段
  - 运行 ASR 推理
  - 返回文本转录

**FunASR 输出格式**：
```python
{
    "text": "你好世界",           # 转录文本
    "text_notypo": "你好世界",    # 无拼写纠正
    "text_cs": "你好世界"          # 中文文本（如适用）
}
```

#### 4. SRTGenerator（SRT 生成器）
- 将段落转换为标准 SRT 格式：
```
1
00:00:01,000 --> 00:00:03,500
你好世界

2
00:00:04,200 --> 00:00:07,800
这是第二条字幕。
```
- 还支持带结构化数据的 JSON 输出

---

## 处理长视频（1+ 小时）

### 挑战

1. **内存**：ASR 模型必须始终保持在内存中
2. **VAD 准确性**：长视频中的背景噪音可能导致误报
3. **段落管理**：数千个段落需要正确处理

### 我们的方法

1. **VAD 优先分割**：不是在连续处理，而是先分割再转录。这可以防止内存堆积。

2. **段落持续时间限制**：`max_segment_duration=10.0` 确保没有单个段落对于 ASR 模型上下文来说太长。

3. **流式就绪设计**：流水线逐段处理，因此无论视频长度如何，内存使用都保持有界。

### 长视频建议

```bash
# 使用 GPU 加快处理
python -m lyrics_render --input long_video.mp4 --output subs.srt --device cuda

# 针对嘈杂内容调整 VAD
python -m lyrics_render --input long_video.mp4 --vad-aggressiveness 2

# 保留临时文件以便调试
python -m lyrics_render --input long_video.mp4 --keep-temp
```

---

## 为什么不用 Whisper API？

| 因素 | 我们的流水线 | Whisper API |
|------|--------------|-------------|
| 成本 | 免费（本地模型） | $0.006/分钟 |
| 隐私 | 全部本地 | 数据发送到 API |
| 时间戳 | 原生 SRT 就绪 | 需要单独对齐 |
| 长视频 | 处理任意长度 | 上下文限制 |
| 自定义 | 完全可定制 | 有限 |

---

## 使用方法

```bash
# 基本使用 (CPU)
python -m lyrics_render --input video.mp4 --output subtitles.srt

# GPU（推荐用于长视频）
python -m lyrics_render --input video.mp4 --output subtitles.srt --device cuda

# 带语言提示（更快）
python -m lyrics_render --input video.mp4 --output subtitles.srt --language en
```

### 烧录字幕到视频

生成 SRT 字幕后，可以使用 FFmpeg 将字幕烧录到视频中：

```bash
# 烧录硬字幕到视频
ffmpeg -i video.mp4 -vf subtitles=subtitles.srt -c:a copy output_with_subs.mp4

# 如果视频已有音轨
ffmpeg -i video.mp4 -vf subtitles=subtitles.srt -c:a copy -map 0:a? output.mp4
```

---

## 项目结构

```
lyrics_render/
├── lyrics_render/           # 主包
│   ├── __init__.py          # 导出
│   ├── __main__.py         # CLI 入口
│   ├── _types.py           # AudioSegment, PipelineConfig
│   ├── _audio.py           # AudioExtractor
│   ├── _vad.py             # VADSegmenter
│   ├── _asr.py             # ASRTranscriber
│   ├── _srt.py             # SRTGenerator
│   ├── _pipeline.py        # LyricsRenderPipeline
│   └── _cli.py             # CLI 参数解析
├── tests/                   # 单元测试
├── docs/                    # 文档
│   ├── THEORY.md          # 本文档 - 设计原理
│   ├── THEORY_EN.md       # Design documentation (English)
│   ├── INSTALL.md         # 中文安装指南
│   └── INSTALL_EN.md      # Installation guide (English)
├── README.md               # 中文快速概览
├── README_EN.md            # English quick overview
├── install.sh               # 安装脚本
└── requirements.txt        # Python 依赖
```