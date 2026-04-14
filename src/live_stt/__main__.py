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

    config = Config.load()
    logger.setup(console=config.log_to_console)

    missing = _check_system_deps()
    if missing:
        log = logger.get("live_stt")
        log.warning("Missing system tools (paste may not work):\n%s", "\n".join(missing))

    from .app import App

    App(config).run()


if __name__ == "__main__":
    main()
