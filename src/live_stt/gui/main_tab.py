"""Main tab — record / transcribe / translate controls and transcript log."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402


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

        # Transcript display
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_cursor_visible(False)
        sw.add(self.text_view)
        self.pack_start(sw, True, True, 0)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_homogeneous(True)

        self.btn_start = Gtk.Button(label="Start")
        self.btn_start.set_name("btn-start")
        btn_box.pack_start(self.btn_start, True, True, 0)

        self.btn_translate = Gtk.Button(label="Start + Translate")
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
            self.btn_start.set_label("Stop" if not translate else "Start")
            self.btn_translate.set_label("Stop" if translate else "Start + Translate")
        else:
            self.btn_start.set_label("Start")
            self.btn_translate.set_label("Start + Translate")

    def append_text(self, text: str) -> None:
        buf = self.text_view.get_buffer()
        end = buf.get_end_iter()
        if buf.get_char_count() > 0:
            buf.insert(end, "\n")
            end = buf.get_end_iter()
        buf.insert(end, text)
        mark = buf.create_mark(None, buf.get_end_iter(), False)
        self.text_view.scroll_mark_onscreen(mark)
