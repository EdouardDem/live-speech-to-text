#!/bin/bash

set -euo pipefail

APT_PACKAGES="libportaudio2 xdotool xclip python3-gi python3-gi-cairo gir1.2-gtk-3.0"

# Install system packages
echo "Installing system packages..."
echo "[Running] sudo apt install $APT_PACKAGES"
sudo apt install $APT_PACKAGES

# Create virtual environment
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    echo "[Running] python3 -m venv .venv --system-site-packages"
    python3 -m venv .venv --system-site-packages
fi
# Activate virtual environment  
echo "Activating virtual environment..."
echo "[Running] source .venv/bin/activate"
source .venv/bin/activate

# Install live-stt
echo "Installing live-stt..."
echo "[Running] pip install -e ."
pip install -e .

# Final message
echo "Installation complete. Run ./start.sh to run the program"