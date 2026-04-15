"""Donate tab — encourages users to support the project."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..services.config import Config

_TXT_TITLE = "Enjoying Live STT?"
_TXT_BODY = (
    "This app is a labour of love, built and maintained on personal time. "
    "If it saves you time or makes your workflow smoother, please consider "
    "buying me a coffee. Every contribution helps keep development going, "
    "covers model-hosting experiments, and motivates new features."
)
_TXT_BTN = "☕  Buy me a coffee"


class DonateTab(Gtk.Box):
    """A simple tab with a short message and a donation button."""

    def __init__(self, config: Config) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self._config = config
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

        button = Gtk.LinkButton.new_with_label(config.donate_url, _TXT_BTN)
        button.set_halign(Gtk.Align.CENTER)
        self.pack_start(button, False, False, 0)
