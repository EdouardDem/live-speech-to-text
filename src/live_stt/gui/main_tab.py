"""Main tab — record / transcribe controls, post-processor toggles, history."""

from collections.abc import Callable

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .history_entry import HistoryEntry

# -- UI texts ----------------------------------------------------------------

_TXT_BTN_TRANSCRIBE = "Record"
_TXT_BTN_STOP = "Stop"
_TXT_STATUS_INIT = "Initializing\u2026"
_TXT_FRAME_PROCESSORS = "Post-processors"

_SCROLL_DELAY = 50


class MainTab(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(16)
        self.set_margin_end(16)

        # Status label
        self.status_label = Gtk.Label(label=_TXT_STATUS_INIT)
        self.status_label.set_name("status-label")
        self.pack_start(self.status_label, False, False, 0)

        # History list
        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scroll.set_vexpand(True)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._scroll.add(self._list_box)
        self.pack_start(self._scroll, True, True, 0)

        # Post-processor toggles section (rebuilt dynamically)
        self._processors_frame = Gtk.Frame(label=_TXT_FRAME_PROCESSORS)
        self._processors_frame.set_shadow_type(Gtk.ShadowType.NONE)
        self._processors_frame.set_no_show_all(True)

        self._processors_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=8
        )
        self._processors_box.set_margin_top(4)
        self._processors_box.set_margin_bottom(4)
        self._processors_box.set_margin_start(8)
        self._processors_box.set_margin_end(8)
        self._processors_frame.add(self._processors_box)
        self.pack_start(self._processors_frame, False, False, 0)

        # Transcribe button
        self.btn_start = Gtk.Button(label=_TXT_BTN_TRANSCRIBE)
        self.btn_start.set_name("btn-transcribe")
        self.pack_start(self.btn_start, False, False, 0)

        # Enabled post-processors summary (italic, below the record button)
        self._enabled_label = Gtk.Label()
        self._enabled_label.set_xalign(0.5)
        self._enabled_label.set_no_show_all(True)
        self.pack_start(self._enabled_label, False, False, 0)

    # -- Processor toggles ----------------------------------------------------

    def rebuild_processors(
        self,
        processors: list,
        on_toggle: Callable[[str, bool], None],
    ) -> None:
        """Rebuild the post-processor toggle section.

        *processors* is a list of ``PostProcessorConfig`` objects.
        *on_toggle(proc_id, enabled)* is called when a switch changes.
        """
        self._processors_box.foreach(self._processors_box.remove)

        for cfg in processors:
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            row.set_margin_start(4)
            row.set_margin_end(4)

            icon = Gtk.Image.new_from_icon_name(cfg.icon, Gtk.IconSize.LARGE_TOOLBAR)
            icon.set_margin_bottom(2)
            row.pack_start(icon, False, False, 0)

            label = Gtk.Label(label=cfg.name)
            label.set_max_width_chars(12)
            label.set_ellipsize(3)  # Pango.EllipsizeMode.END
            row.pack_start(label, False, False, 0)

            switch = Gtk.Switch()
            switch.set_active(cfg.enabled)
            switch.set_halign(Gtk.Align.CENTER)
            switch.connect(
                "notify::active",
                lambda sw, _, pid=cfg.id: on_toggle(pid, sw.get_active()),
            )
            row.pack_start(switch, False, False, 0)

            self._processors_box.pack_start(row, False, False, 0)

        if processors:
            self._processors_frame.show_all()
        else:
            self._processors_frame.hide()

        enabled_names = [p.name for p in processors if p.enabled]
        if enabled_names:
            markup = "<i>" + GLib.markup_escape_text(
                " → ".join(enabled_names)
            ) + "</i>"
            self._enabled_label.set_markup(markup)
            self._enabled_label.show()
        else:
            self._enabled_label.hide()

    # -- Status / sensitivity -------------------------------------------------

    def set_status(self, text: str) -> None:
        self.status_label.set_text(text)

    def set_buttons_sensitive(self, sensitive: bool) -> None:
        self.btn_start.set_sensitive(sensitive)
        for child in self._processors_box.get_children():
            child.set_sensitive(sensitive)

    def set_recording_state(self, recording: bool) -> None:
        if recording:
            self.btn_start.set_label(_TXT_BTN_STOP)
            self.btn_start.get_style_context().add_class("recording")
        else:
            self.btn_start.set_label(_TXT_BTN_TRANSCRIBE)
            self.btn_start.get_style_context().remove_class("recording")

    # -- History --------------------------------------------------------------

    def append_entry(
        self,
        text: str,
        icon_name: str,
        indent_level: int = 0,
    ) -> None:
        """Add a history card."""
        entry = HistoryEntry(text, icon_name, indent_level=indent_level)
        self._list_box.add(entry)
        GLib.timeout_add(_SCROLL_DELAY, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> bool:
        adj = self._scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False
