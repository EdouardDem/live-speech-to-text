import logging
import os
import shutil
import subprocess
import time

log = logging.getLogger(__name__)


class Paster:
    """Inserts text into the currently focused input field.

    Supports X11 (xclip + xdotool) and Wayland (wl-copy + wtype) backends.
    """

    def __init__(self, method: str = "auto"):
        self._method = self._resolve(method)
        log.info("Paste backend: %s", self._method)

    # -- public ---------------------------------------------------------------

    def paste(self, text: str) -> None:
        fn = getattr(self, f"_paste_{self._method}", None)
        if fn is None:
            raise RuntimeError(f"Unknown paste method: {self._method}")
        fn(text)

    # -- auto-detection -------------------------------------------------------

    @staticmethod
    def _resolve(method: str) -> str:
        if method != "auto":
            return method

        session = os.environ.get("XDG_SESSION_TYPE", "x11")

        if session == "wayland":
            if shutil.which("wl-copy") and shutil.which("wtype"):
                return "wayland"

        if shutil.which("xdotool"):
            if shutil.which("xclip"):
                return "xclip"
            return "xdotool"

        raise RuntimeError(
            "No supported paste backend found.\n"
            "  X11:     install  xdotool + xclip\n"
            "  Wayland: install  wl-copy + wtype"
        )

    # -- backends -------------------------------------------------------------

    @staticmethod
    def _paste_xclip(text: str) -> None:
        """Copy to clipboard via xclip, then simulate Ctrl+V."""
        proc = subprocess.Popen(
            ["xclip", "-selection", "clipboard"],
            stdin=subprocess.PIPE,
        )
        proc.communicate(text.encode())
        time.sleep(0.05)
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
            check=True,
        )

    @staticmethod
    def _paste_xdotool(text: str) -> None:
        """Type text directly via xdotool (slower, no clipboard)."""
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", "12", "--", text],
            check=True,
        )

    @staticmethod
    def _paste_wayland(text: str) -> None:
        """Copy via wl-copy, then simulate Ctrl+V via wtype."""
        subprocess.run(["wl-copy", "--", text], check=True)
        time.sleep(0.05)
        subprocess.run(
            ["wtype", "-M", "ctrl", "v", "-m", "ctrl"],
            check=True,
        )
