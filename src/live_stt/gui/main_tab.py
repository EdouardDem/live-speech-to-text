"""Main tab — record / transcribe / translate controls and history."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .history_entry import HistoryEntry

_BTN_START_LABEL = "Transcribe"
_BTN_TRANSLATE_LABEL = "Translate"
_SCROLL_DELAY = 50


class MainTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(16)
        self.set_margin_end(16)

        # Status label
        self.status_label = Gtk.Label(label="Initializing…")
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

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_homogeneous(True)

        self.btn_start = Gtk.Button(label=_BTN_START_LABEL)
        self.btn_start.set_name("btn-transcribe")
        btn_box.pack_start(self.btn_start, True, True, 0)

        self.btn_translate = Gtk.Button(label=_BTN_TRANSLATE_LABEL)
        self.btn_translate.set_name("btn-translate")
        btn_box.pack_start(self.btn_translate, True, True, 0)

        self.pack_start(btn_box, False, False, 0)

    def set_status(self, text: str) -> None:
        self.status_label.set_text(text)

    def set_buttons_sensitive(self, sensitive: bool) -> None:
        self.btn_start.set_sensitive(sensitive)
        self.btn_translate.set_sensitive(sensitive)

    def set_recording_state(self, recording: bool, translate: bool) -> None:
        if recording:
            self.btn_start.set_label("Stop" if not translate else _BTN_START_LABEL)
            self.btn_translate.set_label("Stop" if translate else _BTN_TRANSLATE_LABEL)
        else:
            self.btn_start.set_label(_BTN_START_LABEL)
            self.btn_translate.set_label(_BTN_TRANSLATE_LABEL)

    def append_entry(self, text: str, entry_type: str = "transcription") -> None:
        """Add a history card to the list.

        Parameters
        ----------
        text:
            The transcribed or translated text.
        entry_type:
            ``"transcription"`` or ``"translation"``.
        """
        entry = HistoryEntry(text, entry_type)
        self._list_box.add(entry)
        # Delay scroll to let GTK finish laying out the new row
        GLib.timeout_add(_SCROLL_DELAY, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> bool:
        adj = self._scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False  # run only once
