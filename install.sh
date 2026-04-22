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

# Ask about GPU/CPU installation
echo ""
echo "Select installation type:"
echo "  1) CUDA (GPU) - Recommended if you have NVIDIA GPU"
echo "  2) CPU only - For machines without GPU"
read -p "Enter choice (1/2) [1]: " -n 1 -r
echo
if [[ -z "$REPLY" ]]; then
    INSTALL_TYPE=1
else
    INSTALL_TYPE=$REPLY
fi

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
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch
if [ "$INSTALL_TYPE" = "1" ]; then
    echo "Installing PyTorch with CUDA support..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    echo "Installing PyTorch (CPU only)..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install basic dependencies
echo "Installing basic dependencies..."
pip install pydub webrtcvad numpy scipy tqdm pytest

# Clone and install FunASR from GitHub (editable mode)
echo "Installing FunASR from GitHub..."
if [ -d "FunASR" ]; then
    echo "FunASR directory already exists, skipping clone."
else
    echo "Cloning FunASR repository..."
    git clone https://github.com/alibaba/FunASR.git
fi

echo "Installing FunASR in editable mode..."
cd FunASR
pip install -e ./
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run the pipeline (GPU):"
echo "  python -m lyrics_render --input video.mp4 --output subtitles.srt --device cuda"
echo ""
echo "To run the pipeline (CPU):"
echo "  python -m lyrics_render --input video.mp4 --output subtitles.srt --device cpu"
echo ""