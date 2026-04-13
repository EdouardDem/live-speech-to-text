"""Application — orchestrates services, GUI window, hotkeys, and tray icon."""

import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .gui.window import LiveSTTWindow
from .services.audio import AudioRecorder
from .services.config import Config
from .services.hotkey import HotkeyListener
from .services import logger
from .services.paster import Paster
from .services.transcriber import Transcriber
from .services.translators import TranslatorService
from .services.tray import TrayIcon

log = logger.get(__name__)


class App:
    """Main application — owns every service and the GTK window."""

    def __init__(self, config: Config):
        self._cfg = config
        self._lock = threading.Lock()
        self._model_loaded = False

        # Services
        self._recorder = AudioRecorder(config)
        self._transcriber = Transcriber(config)
        self._paster = Paster(config)
        self._translator_service = TranslatorService(config)
        self._hotkey = HotkeyListener(config, "hotkey", self._on_hotkey_toggle)
        self._translate_hotkey = HotkeyListener(
            config, "translate_hotkey", self._on_hotkey_translate_toggle
        )
        config.subscribe(self._on_config_changed)
        self._tray = TrayIcon(
            on_show_window=lambda: GLib.idle_add(self._show_window),
            on_quit=lambda: GLib.idle_add(self._quit),
        )

        # Window
        self._window = LiveSTTWindow(
            config,
            on_settings_saved=self._on_settings_saved,
            on_start=lambda: self._toggle(translate=False),
            on_translate=lambda: self._toggle(translate=True),
        )

        # Connect loggers to GUI tabs
        logger.set_gui_callback(
            lambda msg: GLib.idle_add(self._window.logs_tab.append, msg)
        )
        logger.set_model_gui_callback(
            lambda msg: GLib.idle_add(self._window.model_logs_tab.append, msg)
        )

    # -- Lifecycle ------------------------------------------------------------

    def run(self) -> None:
        self._tray.start()
        self._hotkey.start()
        self._translate_hotkey.start()
        log.info("Hotkeys active: %s / %s", self._cfg.hotkey, self._cfg.translate_hotkey)
        self._window.show_all()
        threading.Thread(target=self._load_model, daemon=True).start()
        Gtk.main()

    def _load_model(self) -> None:
        try:
            # Intercept NeMo's logger before it produces any output
            logger.capture_nemo_logs()
            self._transcriber.load()
            self._model_loaded = True
            GLib.idle_add(self._window.main_tab.set_status, "Ready")
            GLib.idle_add(self._window.main_tab.set_buttons_sensitive, True)
        except Exception:
            log.exception("Failed to load model")
            GLib.idle_add(self._window.main_tab.set_status, "Error loading model")

    def _show_window(self) -> None:
        self._window.present()

    def _quit(self) -> None:
        log.info("Shutting down…")
        if self._recorder.is_recording:
            self._recorder.stop()
        self._hotkey.stop()
        self._translate_hotkey.stop()
        self._tray.stop()
        Gtk.main_quit()

    # -- Hotkey callbacks (pynput thread → GTK thread) ------------------------

    def _on_hotkey_toggle(self) -> None:
        GLib.idle_add(self._toggle, False)

    def _on_hotkey_translate_toggle(self) -> None:
        GLib.idle_add(self._toggle, True)

    # -- Recording toggle -----------------------------------------------------

    def _toggle(self, translate: bool) -> None:
        with self._lock:
            if not self._model_loaded:
                return
            if self._recorder.is_recording:
                self._stop_and_process(translate)
            else:
                self._start_recording(translate)

    def _start_recording(self, translate: bool) -> None:
        self._recorder.start()
        self._window.main_tab.set_recording_state(True, translate)
        self._window.main_tab.set_status("Recording…")
        self._tray.set_state("recording")

    def _stop_and_process(self, translate: bool) -> None:
        audio = self._recorder.stop()
        self._window.main_tab.set_recording_state(False, translate)
        self._window.main_tab.set_buttons_sensitive(False)
        self._window.main_tab.set_status("Transcribing…")
        self._tray.set_state("transcribing")
        threading.Thread(
            target=self._transcribe_and_paste,
            args=(audio, translate),
            daemon=True,
        ).start()

    def _transcribe_and_paste(self, audio, translate: bool) -> None:
        try:
            if len(audio) == 0:
                GLib.idle_add(self._window.main_tab.set_status, "No audio captured")
                return

            text = self._transcriber.transcribe(audio, self._cfg.sample_rate)
            if not text:
                GLib.idle_add(self._window.main_tab.set_status, "Empty transcription")
                return

            GLib.idle_add(
                self._window.main_tab.append_entry, text, "transcription"
            )

            if translate:
                GLib.idle_add(self._window.main_tab.set_status, "Translating…")
                GLib.idle_add(self._tray.set_state, "translating")
                translated = self._translator_service.translate(text)
                GLib.idle_add(
                    self._window.main_tab.append_entry, translated, "translation"
                )
                text = translated

            self._paster.paste(text)
            GLib.idle_add(self._window.main_tab.set_status, "Ready")
        except Exception:
            log.exception("Transcription / paste failed")
            GLib.idle_add(self._window.main_tab.set_status, "Error — see logs")
        finally:
            GLib.idle_add(self._window.main_tab.set_buttons_sensitive, True)
            GLib.idle_add(self._tray.set_state, "idle")

    # -- Settings -------------------------------------------------------------

    def _on_config_changed(self) -> None:
        logger.set_console_enabled(self._cfg.log_to_console)

    def _on_settings_saved(self) -> None:
        self._window.main_tab.set_status("Settings saved")
