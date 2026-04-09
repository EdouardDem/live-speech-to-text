import argparse
import logging
import shutil
import sys

from .app import App
from .config import Config


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
        "--no-tray",
        action="store_true",
        help="Run without system-tray icon (headless mode)",
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

    app = App(config, use_tray=not args.no_tray)
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nInterrupted – shutting down.")


if __name__ == "__main__":
    main()
