# Live Speech-to-Text

[![Buy Me a Coffee](https://img.shields.io/badge/buy_me_a_coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/edouarddem)

A Linux desktop application that records speech from your microphone and inserts
the transcript into the currently focused text field, with optional on-the-fly
translation. Powered by
[NVIDIA Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3).

## Features

- GTK 3 graphical interface with system tray integration
- Local speech-to-text transcription (GPU-accelerated when available)
- Optional translation via Anthropic (Claude) or DeepL APIs
- Global hotkeys for hands-free operation
- Clipboard content preserved after pasting
- API keys stored encrypted in the configuration file
- Transcription and translation history with one-click copy

## How it works

1. Click **Transcribe** (or press **Ctrl+Shift+Z**) to start recording.
2. Click **Stop** (or press the hotkey again) to stop.
3. The audio is transcribed locally using the Parakeet model.
4. The resulting text is pasted into whatever input field has focus.

### Translation mode

Click **Translate** (or press **Ctrl+Shift+T**) to start recording with
translation enabled. The transcribed text will be translated to the target
language (default: English) before being pasted.

### System tray

The application lives in the system tray. Closing the window hides it to the
tray — right-click the tray icon and select **Quit** to exit completely.

| Tray color | State        |
| ---------- | ------------ |
| Grey       | Idle         |
| Red        | Recording    |
| Orange     | Transcribing |
| Blue       | Translating  |

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

# GTK 3 Python bindings
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Text insertion (X11)
sudo apt install xdotool xclip

# Text insertion (Wayland — instead of xdotool/xclip)
# sudo apt install wl-clipboard wtype
```

#### 2. Python

Python >= 3.10 is required. Create a virtual environment with access to
system site-packages (required for GTK bindings):

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
```

If you already have a virtual environment, enable system site-packages by
setting `include-system-site-packages = true` in `.venv/pyvenv.cfg`.

#### 3. Install

```bash
pip install -e .
```

## Usage

```bash
# Quick start (activates the virtual environment automatically)
./start.sh
```

If the virtual environment is already activated:

```bash
live-stt
```

## Configuration

All settings are accessible from the **Settings** tab in the application.
Changes are saved to `~/.config/live-stt/config.yaml`.

API keys (Anthropic, DeepL) are entered as password fields in the Settings tab
and stored encrypted. They can also be provided via environment variables as a
fallback.

### General settings

| Setting            | Default                       | Description                                    |
| ------------------ | ----------------------------- | ---------------------------------------------- |
| `hotkey`           | `<ctrl>+<shift>+z`            | Global hotkey for transcription (pynput format) |
| `model_name`       | `nvidia/parakeet-tdt-0.6b-v3` | HuggingFace model identifier                   |
| `device`           | `auto`                        | `auto`, `cpu`, or `cuda`                       |
| `paste_method`     | `auto`                        | `auto`, `xclip`, `xdotool`, `wayland`          |
| `paste_shortcut`   | `ctrl+shift+v`                | `ctrl+shift+v` or `ctrl+v`                     |
| `log_to_console`   | `false`                       | Output application logs to the console          |

### Translation settings

| Setting              | Default                     | Description                                  |
| -------------------- | --------------------------- | -------------------------------------------- |
| `translate_hotkey`   | `<ctrl>+<shift>+t`          | Global hotkey for transcribe + translate      |
| `translate_language`  | `English`                  | Target language for translation               |
| `translate_provider`  | `anthropic`                | Translation backend (`anthropic`, `deepl`)    |
| `translate_model`     | `claude-haiku-4-5-20251001`| Claude model (Anthropic provider only)        |
| `translate_max_tokens`| `1024`                     | Max tokens (Anthropic provider only)          |
| `anthropic_api_key`   |                            | Anthropic API key (stored encrypted)          |
| `deepl_api_key`       |                            | DeepL API key (stored encrypted)              |

Anthropic models are listed [here](https://platform.claude.com/docs/en/about-claude/models/overview).

## Supported languages

Parakeet v3 auto-detects the spoken language. Supported:
bg, cs, da, de, el, en, es, et, fi, fr, hr, hu, it, lt, lv, mt, nl, pl, pt, ro, ru, sk, sl, sv, uk.

## License

See [LICENSE](LICENSE).
