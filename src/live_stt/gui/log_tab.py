"""Log tab — displays application log messages."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402


class LogTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(16)
        self.set_margin_end(16)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)

        self._text_view = Gtk.TextView()
        self._text_view.set_editable(False)
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text_view.set_cursor_visible(False)
        self._text_view.set_monospace(True)
        sw.add(self._text_view)
        self.pack_start(sw, True, True, 0)

        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self._on_clear)
        self.pack_start(clear_btn, False, False, 0)

    def append(self, message: str) -> None:
        buf = self._text_view.get_buffer()
        end = buf.get_end_iter()
        if buf.get_char_count() > 0:
            buf.insert(end, "\n")
            end = buf.get_end_iter()
        buf.insert(end, message)
        mark = buf.create_mark(None, buf.get_end_iter(), False)
        self._text_view.scroll_mark_onscreen(mark)

    def _on_clear(self, _btn: Gtk.Button) -> None:
        self._text_view.get_buffer().set_text("")
