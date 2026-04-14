import os
import shutil
import subprocess
import time

from . import logger
from .config import Config

log = logger.get(__name__)

_PRE_PASTE_DELAY = 0.05
_POST_PASTE_DELAY = 0.15

class Paster:
    """Inserts text into the currently focused input field.

    Supports X11 (xclip + xdotool) and Wayland (wl-copy + wtype) backends.
    """

    def __init__(self, config: Config):
        self._config = config
        self._refresh()
        config.subscribe({"paste_method", "paste_shortcut"}, self._on_config_changed)

    def _on_config_changed(self, _changed: set[str]) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self._method = self._resolve(self._config.paste_method)
        self._shortcut = self._config.paste_shortcut
        log.info("Paste backend updated: %s (shortcut: %s)", self._method, self._shortcut)

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
    def _get_clipboard_xclip() -> bytes | None:
        """Read current clipboard contents via xclip."""
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, OSError):
            pass
        return None

    @staticmethod
    def _set_clipboard_xclip(data: bytes) -> None:
        """Write data to clipboard via xclip."""
        proc = subprocess.Popen(
            ["xclip", "-selection", "clipboard"],
            stdin=subprocess.PIPE,
        )
        proc.communicate(data)

    def _paste_xclip(self, text: str) -> None:
        """Copy to clipboard via xclip, then simulate paste shortcut."""
        saved = self._get_clipboard_xclip()
        self._set_clipboard_xclip(text.encode())
        time.sleep(_PRE_PASTE_DELAY)
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", self._shortcut],
            check=True,
        )
        if saved is not None:
            time.sleep(_POST_PASTE_DELAY)
            self._set_clipboard_xclip(saved)

    @staticmethod
    def _paste_xdotool(text: str) -> None:
        """Type text directly via xdotool (slower, no clipboard)."""
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", "12", "--", text],
            check=True,
        )

    @staticmethod
    def _get_clipboard_wayland() -> bytes | None:
        """Read current clipboard contents via wl-paste."""
        try:
            result = subprocess.run(
                ["wl-paste", "--no-newline"],
                capture_output=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, OSError):
            pass
        return None

    def _paste_wayland(self, text: str) -> None:
        """Copy via wl-copy, then simulate paste shortcut via wtype."""
        saved = self._get_clipboard_wayland()
        subprocess.run(["wl-copy", "--", text], check=True)
        time.sleep(_PRE_PASTE_DELAY)
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
        if saved is not None:
            time.sleep(_POST_PASTE_DELAY)
            subprocess.run(["wl-copy", "--", saved], check=True)
