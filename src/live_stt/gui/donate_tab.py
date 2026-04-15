"""Donate tab — encourages users to support the project."""

import webbrowser
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GdkPixbuf, Gtk  # noqa: E402

_DONATE_URL = "https://www.buymeacoffee.com/edouarddem"
_BADGE_PATH = Path(__file__).resolve().parent.parent / "assets" / "bmc.svg"
_BADGE_HEIGHT = 36

_TXT_TITLE = "Enjoying Live STT?"
_TXT_BODY = (
    "This app is a labour of love, built and maintained on personal time. "
    "If it saves you time or makes your workflow smoother, please consider "
    "buying me a coffee. Every contribution helps keep development going, "
    "covers model-hosting experiments, and motivates new features."
)
_TXT_BTN_TOOLTIP = "Open Buy Me a Coffee in your browser"


class DonateTab(Gtk.Box):
    """A simple tab with a short message and a donation button."""

    def __init__(self, _config=None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(32)
        self.set_margin_bottom(32)
        self.set_margin_start(32)
        self.set_margin_end(32)

        title = Gtk.Label()
        title.set_markup(f'<span size="x-large" weight="bold">{_TXT_TITLE}</span>')
        title.set_xalign(0.5)
        self.pack_start(title, False, False, 0)

        body = Gtk.Label(label=_TXT_BODY)
        body.set_line_wrap(True)
        body.set_justify(Gtk.Justification.CENTER)
        body.set_max_width_chars(60)
        body.set_xalign(0.5)
        self.pack_start(body, False, False, 0)

        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_halign(Gtk.Align.CENTER)
        button.set_tooltip_text(_TXT_BTN_TOOLTIP)
        button.add(self._build_badge())
        button.connect("clicked", lambda _b: webbrowser.open(_DONATE_URL))
        self.pack_start(button, False, False, 0)

    @staticmethod
    def _build_badge() -> Gtk.Widget:
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(_BADGE_PATH), -1, _BADGE_HEIGHT, True
            )
            return Gtk.Image.new_from_pixbuf(pixbuf)
        except Exception:
            return Gtk.Label(label="☕  Buy me a coffee")
