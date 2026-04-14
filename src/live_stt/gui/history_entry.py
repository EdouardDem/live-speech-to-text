"""Single history card — shows an icon, text, and a copy button."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..services import icons

# -- UI texts ----------------------------------------------------------------

_TXT_COPY_TOOLTIP = "Copy to clipboard"


class HistoryEntry(Gtk.ListBoxRow):
    """A card representing one entry in the transcription / processing history.

    Parameters
    ----------
    text:
        The text to display.
    icon_name:
        GTK icon name shown on the left side of the card.
    """

    def __init__(
        self,
        text: str,
        icon_name: str,
    ):
        super().__init__()
        self.set_selectable(False)
        self.set_activatable(False)
        self._text = text

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        frame.get_style_context().add_class("history-card")

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.set_margin_top(8)
        hbox.set_margin_bottom(8)
        hbox.set_margin_start(10)
        hbox.set_margin_end(10)

        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        icon.set_valign(Gtk.Align.START)
        icon.set_margin_top(2)
        hbox.pack_start(icon, False, False, 0)

        # Text label
        label = Gtk.Label(label=text)
        label.set_line_wrap(True)
        label.set_xalign(0)
        label.set_hexpand(True)
        label.set_selectable(True)
        hbox.pack_start(label, True, True, 0)

        # Copy button
        copy_btn = Gtk.Button.new_from_icon_name(
            icons.get("copy"), Gtk.IconSize.SMALL_TOOLBAR
        )
        copy_btn.set_tooltip_text(_TXT_COPY_TOOLTIP)
        copy_btn.set_relief(Gtk.ReliefStyle.NONE)
        copy_btn.set_valign(Gtk.Align.START)
        copy_btn.connect("clicked", self._on_copy)
        hbox.pack_start(copy_btn, False, False, 0)

        frame.add(hbox)
        self.add(frame)
        self.show_all()

    def _on_copy(self, _btn: Gtk.Button) -> None:
        clipboard = Gtk.Clipboard.get_default(self.get_display())
        clipboard.set_text(self._text, -1)
        clipboard.store()
