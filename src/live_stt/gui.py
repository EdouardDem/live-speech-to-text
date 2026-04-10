"""GTK 3 graphical interface for Live STT."""

import logging
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .audio import AudioRecorder
from .config import Config
from .paster import Paster
from .transcriber import Transcriber
from .translators import create_translator

log = logging.getLogger(__name__)

_CSS = b"""
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


class LiveSTTWindow(Gtk.Window):
    def __init__(self, config: Config):
        super().__init__(title="Live Speech-to-Text")
        self.set_default_size(480, 380)
        self.set_border_width(12)
        self.connect("destroy", self._on_quit)

        self._cfg = config
        self._recorder = AudioRecorder(sample_rate=config.sample_rate)
        self._transcriber = Transcriber(
            model_name=config.model_name,
            device=config.device,
        )
        self._paster = Paster(
            method=config.paste_method,
            shortcut=config.paste_shortcut,
        )
        self._translator = None
        self._model_loaded = False
        self._lock = threading.Lock()

        # Apply CSS
        css = Gtk.CssProvider()
        css.load_from_data(_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Notebook (tabs)
        notebook = Gtk.Notebook()
        self.add(notebook)

        notebook.append_page(self._build_main_tab(), Gtk.Label(label="Main"))
        notebook.append_page(self._build_settings_tab(), Gtk.Label(label="Settings"))

        # Load model in background
        self._set_status("Loading model…")
        self._set_buttons_sensitive(False)
        threading.Thread(target=self._load_model, daemon=True).start()

    # -- Main tab -------------------------------------------------------------

    def _build_main_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        # Status label
        self._status_label = Gtk.Label(label="Initializing…")
        self._status_label.set_name("status-label")
        box.pack_start(self._status_label, False, False, 0)

        # Transcript display
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        self._text_view = Gtk.TextView()
        self._text_view.set_editable(False)
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text_view.set_cursor_visible(False)
        sw.add(self._text_view)
        box.pack_start(sw, True, True, 0)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_homogeneous(True)

        self._btn_start = Gtk.Button(label="Start")
        self._btn_start.set_name("btn-start")
        self._btn_start.connect("clicked", self._on_start_clicked)
        btn_box.pack_start(self._btn_start, True, True, 0)

        self._btn_translate = Gtk.Button(label="Start + Translate")
        self._btn_translate.set_name("btn-translate")
        self._btn_translate.connect("clicked", self._on_translate_clicked)
        btn_box.pack_start(self._btn_translate, True, True, 0)

        box.pack_start(btn_box, False, False, 0)

        return box

    # -- Settings tab ---------------------------------------------------------

    def _build_settings_tab(self) -> Gtk.Widget:
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(8)
        grid.set_margin_top(16)
        grid.set_margin_bottom(16)
        grid.set_margin_start(16)
        grid.set_margin_end(16)

        self._setting_entries: dict[str, Gtk.Entry | Gtk.ComboBoxText] = {}

        settings = [
            ("hotkey", "Hotkey", "entry"),
            ("model_name", "Model", "entry"),
            ("device", "Device", "combo", ["auto", "cpu", "cuda"]),
            ("paste_method", "Paste method", "combo", ["auto", "xclip", "xdotool", "wayland"]),
            ("paste_shortcut", "Paste shortcut", "entry"),
            ("translate_hotkey", "Translate hotkey", "entry"),
            ("translate_language", "Translate language", "entry"),
            ("translate_provider", "Translate provider", "combo", ["anthropic", "deepl"]),
            ("translate_model", "Translate model", "entry"),
            ("translate_max_tokens", "Max tokens", "entry"),
        ]

        for row, item in enumerate(settings):
            key, label_text, kind = item[0], item[1], item[2]
            label = Gtk.Label(label=label_text, xalign=0)
            grid.attach(label, 0, row, 1, 1)

            current_value = str(getattr(self._cfg, key))

            if kind == "combo":
                combo = Gtk.ComboBoxText()
                for opt in item[3]:
                    combo.append_text(opt)
                combo.set_active(item[3].index(current_value) if current_value in item[3] else 0)
                combo.set_hexpand(True)
                grid.attach(combo, 1, row, 1, 1)
                self._setting_entries[key] = combo
            else:
                entry = Gtk.Entry()
                entry.set_text(current_value)
                entry.set_hexpand(True)
                grid.attach(entry, 1, row, 1, 1)
                self._setting_entries[key] = entry

        # Save button
        row = len(settings)
        save_btn = Gtk.Button(label="Save settings")
        save_btn.connect("clicked", self._on_save_settings)
        grid.attach(save_btn, 0, row, 2, 1)

        sw.add(grid)
        return sw

    # -- Model loading --------------------------------------------------------

    def _load_model(self) -> None:
        try:
            self._transcriber.load()
            self._model_loaded = True
            GLib.idle_add(self._set_status, "Ready")
            GLib.idle_add(self._set_buttons_sensitive, True)
        except Exception:
            log.exception("Failed to load model")
            GLib.idle_add(self._set_status, "Error loading model")

    # -- Button handlers ------------------------------------------------------

    def _on_start_clicked(self, _btn: Gtk.Button) -> None:
        with self._lock:
            if self._recorder.is_recording:
                self._stop_and_process(translate=False)
            else:
                self._start_recording(translate=False)

    def _on_translate_clicked(self, _btn: Gtk.Button) -> None:
        with self._lock:
            if self._recorder.is_recording:
                self._stop_and_process(translate=True)
            else:
                self._start_recording(translate=True)

    def _start_recording(self, translate: bool) -> None:
        self._recorder.start()
        self._btn_start.set_label("Stop" if not translate else "Start")
        self._btn_translate.set_label("Stop" if translate else "Start + Translate")
        self._set_status("Recording…")

    def _stop_and_process(self, translate: bool) -> None:
        audio = self._recorder.stop()
        self._btn_start.set_label("Start")
        self._btn_translate.set_label("Start + Translate")
        self._set_buttons_sensitive(False)
        self._set_status("Transcribing…")
        threading.Thread(
            target=self._transcribe_and_paste,
            args=(audio, translate),
            daemon=True,
        ).start()

    def _transcribe_and_paste(self, audio, translate: bool) -> None:
        try:
            if len(audio) == 0:
                GLib.idle_add(self._set_status, "No audio captured")
                return

            text = self._transcriber.transcribe(audio, self._cfg.sample_rate)
            if not text:
                GLib.idle_add(self._set_status, "Empty transcription")
                return

            GLib.idle_add(self._append_text, f"🎤 {text}")

            if translate:
                GLib.idle_add(self._set_status, "Translating…")
                if self._translator is None:
                    self._translator = create_translator(
                        provider=self._cfg.translate_provider,
                        model=self._cfg.translate_model,
                        max_tokens=self._cfg.translate_max_tokens,
                    )
                text = self._translator.translate(text, self._cfg.translate_language)
                GLib.idle_add(self._append_text, f"🌐 {text}")

            self._paster.paste(text)
            GLib.idle_add(self._set_status, "Ready")
        except Exception:
            log.exception("Transcription / paste failed")
            GLib.idle_add(self._set_status, "Error — see logs")
        finally:
            GLib.idle_add(self._set_buttons_sensitive, True)

    # -- Settings save --------------------------------------------------------

    def _on_save_settings(self, _btn: Gtk.Button) -> None:
        for key, widget in self._setting_entries.items():
            if isinstance(widget, Gtk.ComboBoxText):
                value = widget.get_active_text()
            else:
                value = widget.get_text()

            field_type = type(getattr(self._cfg, key))
            try:
                setattr(self._cfg, key, field_type(value))
            except (ValueError, TypeError):
                log.warning("Invalid value for %s: %s", key, value)

        self._cfg.save()
        self._paster = Paster(
            method=self._cfg.paste_method,
            shortcut=self._cfg.paste_shortcut,
        )
        self._translator = None  # force re-creation on next use
        self._set_status("Settings saved")

    # -- Helpers --------------------------------------------------------------

    def _set_status(self, text: str) -> None:
        self._status_label.set_text(text)

    def _set_buttons_sensitive(self, sensitive: bool) -> None:
        self._btn_start.set_sensitive(sensitive)
        self._btn_translate.set_sensitive(sensitive)

    def _append_text(self, text: str) -> None:
        buf = self._text_view.get_buffer()
        end = buf.get_end_iter()
        if buf.get_char_count() > 0:
            buf.insert(end, "\n")
            end = buf.get_end_iter()
        buf.insert(end, text)
        # Scroll to bottom
        mark = buf.create_mark(None, buf.get_end_iter(), False)
        self._text_view.scroll_mark_onscreen(mark)

    def _on_quit(self, _widget: Gtk.Widget) -> None:
        if self._recorder.is_recording:
            self._recorder.stop()
        Gtk.main_quit()


def run_gui(config: Config) -> None:
    """Entry point for the GUI."""
    win = LiveSTTWindow(config)
    win.show_all()
    Gtk.main()
