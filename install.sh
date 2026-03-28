#!/bin/bash

set -euo pipefail

# Install packages
echo "Installing packages..."
echo "[Running] sudo apt install libportaudio2 xdotool xclip"
sudo apt install libportaudio2 xdotool xclip

# Create virtual environment
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    echo "[Running] python3 -m venv .venv"
    python3 -m venv .venv
fi
# Activate virtual environment  
echo "Activating virtual environment..."
echo "[Running] source .venv/bin/activate"
source .venv/bin/activate

# Install live-stt
echo "Installing live-stt..."
echo "[Running] pip install -e ."
pip install -e .
