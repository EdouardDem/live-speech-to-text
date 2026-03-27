# Live Speech-to-Text

A lightweight Linux daemon that records speech from your microphone and inserts
the transcript into the currently focused text field, powered by
[NVIDIA Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3).

## How it works

1. Press a global hotkey (default **Ctrl+Shift+S**) to start recording.
2. Press the hotkey again to stop.
3. The audio is transcribed locally using the Parakeet model (GPU-accelerated
   when available).
4. The resulting text is pasted into whatever input field has focus.

A system-tray icon provides visual feedback:

| Color  | State         |
|--------|---------------|
| Grey   | Idle          |
| Red    | Recording     |
| Orange | Transcribing  |

## Prerequisites

### System packages (Debian / Ubuntu)

```bash
# Audio capture
sudo apt install libportaudio2

# Text insertion (X11)
sudo apt install xdotool xclip

# Text insertion (Wayland — instead of xdotool/xclip)
# sudo apt install wl-clipboard wtype
```

### Python

Python >= 3.10 is required. A virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### PyTorch (GPU)

If you have an NVIDIA GPU, install the CUDA build of PyTorch **before**
installing the project so NeMo picks it up automatically:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Skip this step to use CPU-only inference.

## Install

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run with system tray icon (default)
live-stt

# Run headless (no tray, Ctrl+C to quit)
live-stt --no-tray

# Override the hotkey
live-stt --hotkey '<super>+s'

# Force CPU inference
live-stt --device cpu

# Verbose logging
live-stt -v
```

You can also run it as a module:

```bash
python -m live_stt
```

## Configuration

Copy the example config and edit to taste:

```bash
mkdir -p ~/.config/live-stt
cp config.yaml ~/.config/live-stt/config.yaml
```

Settings can also be overridden via CLI flags (see `live-stt --help`).

| Key            | Default                          | Description                        |
|----------------|----------------------------------|------------------------------------|
| `hotkey`       | `<ctrl>+<shift>+s`              | Global hotkey (pynput format)      |
| `model_name`   | `nvidia/parakeet-tdt-0.6b-v3`   | HuggingFace model identifier       |
| `sample_rate`  | `16000`                          | Mic sample rate in Hz              |
| `device`       | `auto`                           | `auto`, `cpu`, or `cuda`           |
| `paste_method` | `auto`                           | `auto`, `xclip`, `xdotool`, `wayland` |

## Supported languages

Parakeet v3 auto-detects the spoken language. Supported:
bg, cs, da, de, el, en, es, et, fi, fr, hr, hu, it, lt, lv, mt, nl, pl, pt, ro, ru, sk, sl, sv, uk.

## License

See [LICENSE](LICENSE).
