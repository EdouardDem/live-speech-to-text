#!/bin/bash

set -euo pipefail

APT_PACKAGES="libportaudio2 xdotool xclip python3-gi python3-gi-cairo gir1.2-gtk-3.0"

# Deactivate virtual environment
echo "Deactivating virtual environment (if active)..."
source deactivate || true

# Remove virtual environment
echo "Removing virtual environment..."
echo "[Running] rm -rf .venv"
rm -rf .venv

# Uninstall packages, ask for confirmation
echo "Uninstalling packages..."
read -p "Do you want to uninstall these packages: $APT_PACKAGES? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "[Running] sudo apt remove $APT_PACKAGES"
    sudo apt remove $APT_PACKAGES
fi
