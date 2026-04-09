# Live Speech-to-Text

A lightweight Linux daemon that records speech from your microphone and inserts
the transcript into the currently focused text field, powered by
[NVIDIA Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3).

## How it works

1. Press a global hotkey (default **Ctrl+Shift+Z**) to start recording.
2. Press the hotkey again to stop.
3. The audio is transcribed locally using the Parakeet model (GPU-accelerated
  when available).
4. The resulting text is pasted into whatever input field has focus.

### Translation mode

Use **Ctrl+Shift+T** to start recording with translation enabled. The
transcribed text will be translated to the target language (default: English)
using Claude Haiku before being pasted.

A system-tray icon provides visual feedback:


| Color  | State        |
| ------ | ------------ |
| Grey   | Idle         |
| Red    | Recording    |
| Orange | Transcribing |
| Blue   | Translating  |


## Prerequisites

### Installation script

```bash
./install.sh
```

### Uninstallation script

```bash
./uninstall.sh
```

### Step by step installation

#### 1. System packages (Debian / Ubuntu)

```bash
# Audio capture
sudo apt install libportaudio2

# Text insertion (X11)
sudo apt install xdotool xclip

# Text insertion (Wayland — instead of xdotool/xclip)
# sudo apt install wl-clipboard wtype
```

#### 2. Python

Python >= 3.10 is required. A virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install

```bash
pip install -e .
```

#### 4. API Key (for translation feature)

To use the translation feature, set your Anthropic API key. Create a `.env`
file in the project directory:

```bash
echo "ANTHROPIC_API_KEY=your-api-key" > .env
```

Or set it as an environment variable:

```bash
export ANTHROPIC_API_KEY=your-api-key
```

## Usage

```bash
# Quick start (activates the virtual environment automatically)
./start.sh

# With options
./start.sh --no-tray
./start.sh --hotkey '<super>+s'
```

If the virtual environment is already activated, you can run `live-stt` directly:

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

# Override translation hotkey
live-stt --translate-hotkey '<ctrl>+<alt>+t'

# Set target language for translation
live-stt --translate-language French
```

You can also run it as a module:

```bash
python -m live_stt
```

## Configuration

If you want a persistent configuration, copy the example config and edit the config file:

```bash
mkdir -p ~/.config/live-stt
cp config.yaml ~/.config/live-stt/config.yaml
```

Settings can also be set via CLI flags (see `live-stt --help`).


| Key                  | Default                       | Description                           |
| -------------------- | ----------------------------- | ------------------------------------- |
| `hotkey`             | `<ctrl>+<shift>+z`            | Global hotkey (pynput format)         |
| `model_name`         | `nvidia/parakeet-tdt-0.6b-v3` | HuggingFace model identifier          |
| `sample_rate`        | `16000`                       | Mic sample rate in Hz                 |
| `device`             | `auto`                        | `auto`, `cpu`, or `cuda`              |
| `paste_method`       | `auto`                        | `auto`, `xclip`, `xdotool`, `wayland` |
| `translate_hotkey`   | `<ctrl>+<shift>+t`            | Hotkey for speech-to-text + translate |
| `translate_language` | `English`                     | Target language for translation       |
| `translate_model`    | `claude-3-5-haiku-latest`     | Claude model for translation          |
| `translate_max_tokens` | `1024`                      | Max tokens for translation response   |


## Supported languages

Parakeet v3 auto-detects the spoken language. Supported:
bg, cs, da, de, el, en, es, et, fi, fr, hr, hu, it, lt, lv, mt, nl, pl, pt, ro, ru, sk, sl, sv, uk.

## License

See [LICENSE](LICENSE).