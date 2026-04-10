"""System tray icon running in a background thread alongside GTK."""

import threading

import pystray
from PIL import Image, ImageDraw

from . import logger

log = logger.get(__name__)

_COLORS = {
    "idle": "#888888",
    "recording": "#e74c3c",
    "transcribing": "#f39c12",
    "translating": "#3498db",
}

_TITLES = {
    "idle": "Live STT — Idle",
    "recording": "Live STT — Recording…",
    "transcribing": "Live STT — Transcribing…",
    "translating": "Live STT — Translating…",
}


def _make_icon(state: str) -> Image.Image:
    size = 64
    margin = 8
    recording_margin = 20
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = _COLORS.get(state, _COLORS["idle"])
    draw.ellipse([margin, margin, size - margin, size - margin], fill=color)
    if state == "recording":
        draw.ellipse(
            [recording_margin, recording_margin, size - recording_margin, size - recording_margin],
            fill="#ffffff",
        )
    return img


class TrayIcon:
    """System tray icon with show-window and quit actions."""

    def __init__(self, on_show_window, on_quit):
        self._on_show_window = on_show_window
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Show", lambda _i, _it: self._on_show_window(), default=True),
            pystray.MenuItem("Quit", lambda _i, _it: self._on_quit()),
        )
        self._icon = pystray.Icon(
            "live-stt",
            _make_icon("idle"),
            _TITLES["idle"],
            menu,
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        log.info("System tray icon ready.")

    def set_state(self, state: str) -> None:
        if self._icon is not None:
            self._icon.icon = _make_icon(state)
            self._icon.title = _TITLES.get(state, _TITLES["idle"])

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()
            self._icon = None
