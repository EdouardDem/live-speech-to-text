import argparse
import shutil

from dotenv import load_dotenv

from .services.config import Config
from .services import logger


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
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    config = Config.load(args.config)
    if args.hotkey:
        config.hotkey = args.hotkey
    if args.model:
        config.model_name = args.model
    if args.device:
        config.device = args.device
    if args.paste_shortcut:
        config.paste_shortcut = args.paste_shortcut
    logger.setup(verbose=args.verbose, console=config.log_to_console)

    missing = _check_system_deps()
    if missing:
        log = logger.get("live_stt")
        log.warning("Missing system tools (paste may not work):\n%s", "\n".join(missing))

    from .app import App

    App(config).run()


if __name__ == "__main__":
    main()
