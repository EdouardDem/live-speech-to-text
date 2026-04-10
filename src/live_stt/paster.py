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

    def __init__(self, method: str = "auto", shortcut: str = "ctrl+shift+v"):
        self._method = self._resolve(method)
        self._shortcut = shortcut
        log.info("Paste backend: %s (shortcut: %s)", self._method, self._shortcut)

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

    def _paste_xclip(self, text: str) -> None:
        """Copy to clipboard via xclip, then simulate paste shortcut."""
        proc = subprocess.Popen(
            ["xclip", "-selection", "clipboard"],
            stdin=subprocess.PIPE,
        )
        proc.communicate(text.encode())
        time.sleep(0.05)
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", self._shortcut],
            check=True,
        )

    @staticmethod
    def _paste_xdotool(text: str) -> None:
        """Type text directly via xdotool (slower, no clipboard)."""
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", "12", "--", text],
            check=True,
        )

    def _paste_wayland(self, text: str) -> None:
        """Copy via wl-copy, then simulate paste shortcut via wtype."""
        subprocess.run(["wl-copy", "--", text], check=True)
        time.sleep(0.05)
        # Build wtype args from shortcut (e.g. "ctrl+shift+v")
        parts = self._shortcut.split("+")
        key = parts[-1]
        modifiers = parts[:-1]
        wtype_args = ["wtype"]
        for mod in modifiers:
            wtype_args += ["-M", mod]
        wtype_args.append(key)
        for mod in reversed(modifiers):
            wtype_args += ["-m", mod]
        subprocess.run(wtype_args, check=True)
