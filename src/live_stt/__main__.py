import argparse
import logging
import shutil
import sys

from dotenv import load_dotenv

from .services.config import Config


def _check_system_deps() -> list[str]:
    """Return a list of warnings about missing system tools."""
    import os

    warnings = []
    session = os.environ.get("XDG_SESSION_TYPE", "x11")

    if session == "wayland":
        for tool in ("wl-copy", "wtype"):
            if not shutil.which(tool):
                warnings.append(f"  - {tool} (Wayland paste support)")
    else:
        for tool in ("xdotool", "xclip"):
            if not shutil.which(tool):
                warnings.append(f"  - {tool} (X11 paste support)")

    return warnings


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="live-stt",
        description="Live speech-to-text using NVIDIA Parakeet",
    )
    parser.add_argument("-c", "--config", help="Path to YAML config file")
    parser.add_argument(
        "--hotkey",
        help="Override hotkey (pynput format, e.g. '<ctrl>+<shift>+s')",
    )
    parser.add_argument("--model", help="Override model name")
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        help="Override compute device",
    )
    parser.add_argument(
        "--paste-shortcut",
        help="Keyboard shortcut for pasting (e.g. 'ctrl+v', 'ctrl+shift+v')",
    )
    parser.add_argument(
        "--translate-hotkey",
        help="Override translation hotkey (pynput format, e.g. '<ctrl>+<shift>+t')",
    )
    parser.add_argument(
        "--translate-language",
        help="Target language for translation (default: English)",
    )
    parser.add_argument(
        "--translate-model",
        help="Claude model for translation (default: claude-haiku-4-5-20251001)",
    )
    parser.add_argument(
        "--translate-max-tokens",
        type=int,
        help="Max tokens for translation response (default: 1024)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        stream=sys.stderr,
    )

    missing = _check_system_deps()
    if missing:
        log = logging.getLogger("live_stt")
        log.warning("Missing system tools (paste may not work):\n%s", "\n".join(missing))

    config = Config.load(args.config)
    if args.hotkey:
        config.hotkey = args.hotkey
    if args.model:
        config.model_name = args.model
    if args.device:
        config.device = args.device
    if args.paste_shortcut:
        config.paste_shortcut = args.paste_shortcut
    if args.translate_hotkey:
        config.translate_hotkey = args.translate_hotkey
    if args.translate_language:
        config.translate_language = args.translate_language
    if args.translate_model:
        config.translate_model = args.translate_model
    if args.translate_max_tokens:
        config.translate_max_tokens = args.translate_max_tokens

    from .app import App

    App(config).run()


if __name__ == "__main__":
    main()
