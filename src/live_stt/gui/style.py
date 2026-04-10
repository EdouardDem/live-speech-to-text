"""CSS styling for the GTK interface."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

CSS = b"""
#status-label {
    font-size: 14px;
    font-weight: bold;
}
#btn-start {
    min-height: 48px;
    font-size: 15px;
}
#btn-translate {
    min-height: 48px;
    font-size: 15px;
}
"""


def apply_css(screen: object) -> None:
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
