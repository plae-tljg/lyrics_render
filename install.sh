#!/bin/bash
# Lyrics Render Pipeline - Setup Script

set -e

echo "========================================"
echo "Lyrics Render Pipeline - Installation"
echo "========================================"

# Check Python version
python3 --version || { echo "Python 3 not found!"; exit 1; }

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
    read -p "Delete and recreate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        echo "Deleted existing venv."
    else
        echo "Using existing venv."
        exit 0
    fi
fi

echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate  # Linux/macOS
# On Windows: venv\Scripts\activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install funasr pydub webrtcvad numpy scipy tqdm pytest

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run the pipeline:"
echo "  python -m lyrics_render --input video.mp4 --output subtitles.srt"
echo ""
echo "For GPU acceleration (if CUDA available):"
echo "  python -m lyrics_render --input video.mp4 --device cuda"
echo ""