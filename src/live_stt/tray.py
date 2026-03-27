import logging

import pystray
from PIL import Image, ImageDraw

log = logging.getLogger(__name__)

_COLORS = {
    "idle": "#888888",
    "recording": "#e74c3c",
    "transcribing": "#f39c12",
}

_TITLES = {
    "idle": "Live STT - Idle",
    "recording": "Live STT - Recording...",
    "transcribing": "Live STT - Transcribing...",
}


def _make_icon(state: str) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = _COLORS.get(state, _COLORS["idle"])
    draw.ellipse([4, 4, size - 4, size - 4], fill=color)
    if state == "recording":
        draw.ellipse([20, 20, size - 20, size - 20], fill="#ffffff")
    return img


class TrayIcon:
    """System-tray indicator with toggle / quit menu."""

    def __init__(self, on_toggle, on_quit):
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None

    def start(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Toggle recording", lambda _i, _it: self._on_toggle()),
            pystray.MenuItem("Quit", lambda _i, _it: self._on_quit()),
        )
        self._icon = pystray.Icon(
            "live-stt",
            _make_icon("idle"),
            _TITLES["idle"],
            menu,
        )
        log.info("System tray icon ready.")
        self._icon.run()  # blocks until stop()

    def set_state(self, state: str) -> None:
        if self._icon is not None:
            self._icon.icon = _make_icon(state)
            self._icon.title = _TITLES.get(state, _TITLES["idle"])

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()
