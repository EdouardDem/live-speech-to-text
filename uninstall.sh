#!/bin/bash

set -euo pipefail

# Deactivate virtual environment
echo "Deactivating virtual environment (if active)..."
source deactivate || true

# Remove virtual environment
echo "Removing virtual environment..."
echo "[Running] rm -rf .venv"
rm -rf .venv

# Uninstall packages, ask for confirmation
echo "Uninstalling packages..."
read -p "Do you want to uninstall these packages: libportaudio2, xdotool, xclip? (y/N) " -n 1 -r
echo   
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "[Running] sudo apt remove libportaudio2 xdotool xclip"
    sudo apt remove libportaudio2 xdotool xclip
fi
