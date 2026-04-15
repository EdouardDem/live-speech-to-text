"""Application — orchestrates services, GUI window, hotkeys, and tray icon."""

import threading
import time

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .gui.window import LiveSTTWindow
from .post_processors import PostProcessorRegistry
from .services.audio import AudioRecorder
from .services.config import Config
from .services.hotkey import HotkeyListener
from .services import logger, icons
from .services.paster import Paster
from .services.transcriber import Transcriber
from .services.tray import TrayIcon

log = logger.get(__name__)

class App:
    """Main application — owns every service and the GTK window."""

    def __init__(self, config: Config):
        self._cfg = config
        self._lock = threading.Lock()
        self._model_loaded = False
        self._record_started_at: float | None = None
        self._progress_source: int | None = None

        # Services
        self._recorder = AudioRecorder(config)
        self._transcriber = Transcriber(config)
        self._paster = Paster(config)
        self._registry = PostProcessorRegistry(config)
        self._hotkey = HotkeyListener(config, "hotkey", self._on_hotkey_toggle)
        self._tray = TrayIcon(
            on_show_window=lambda: GLib.idle_add(self._show_window),
            on_quit=lambda: GLib.idle_add(self._quit),
        )

        config.subscribe({"log_to_console"}, self._on_config_changed)

        # Window
        self._window = LiveSTTWindow(
            config,
            self._registry,
            on_settings_saved=self._on_settings_saved,
            on_start=lambda: self._toggle(),
        )

        # Keep the main-tab processor section in sync with config changes.
        config.subscribe({"post_processors"}, self._on_processors_changed)
        # Initial population of the toggle section
        GLib.idle_add(
            self._window.main_tab.rebuild_processors,
            self._registry.get_all(),
            self._on_processor_switch,
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
        log.info("Hotkey active: %s", self._cfg.hotkey)
        self._window.show_all()
        threading.Thread(target=self._load_model, daemon=True).start()
        Gtk.main()

    def _load_model(self) -> None:
        try:
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
        self._tray.stop()
        Gtk.main_quit()

    # -- Hotkey callback (pynput thread → GTK thread) -------------------------

    def _on_hotkey_toggle(self) -> None:
        GLib.idle_add(self._toggle)

    # -- Recording toggle -----------------------------------------------------

    def _toggle(self) -> None:
        with self._lock:
            if not self._model_loaded:
                return
            if self._recorder.is_recording:
                self._stop_and_process()
            else:
                self._start_recording()

    def _start_recording(self) -> None:
        self._recorder.start()
        self._record_started_at = time.monotonic()
        self._window.main_tab.set_recording_state(True)
        self._window.main_tab.set_status("Recording…")
        self._tray.set_state("recording")
        self._window.main_tab.set_stop_countdown(self._cfg.max_recording_seconds)
        self._progress_source = GLib.timeout_add(500, self._tick_recording_progress)

    def _tick_recording_progress(self) -> bool:
        if not self._recorder.is_recording or self._record_started_at is None:
            return False
        limit = self._cfg.max_recording_seconds
        remaining = limit - (time.monotonic() - self._record_started_at)
        self._window.main_tab.set_stop_countdown(remaining)
        if remaining <= 0:
            log.info("Recording auto-stopped after %d seconds", limit)
            self._progress_source = None
            self._toggle()
            return False
        return True

    def _stop_and_process(self) -> None:
        if self._progress_source is not None:
            GLib.source_remove(self._progress_source)
            self._progress_source = None
        self._record_started_at = None
        audio = self._recorder.stop()
        self._window.main_tab.set_recording_state(False)
        self._window.main_tab.set_buttons_sensitive(False)
        self._window.main_tab.set_status("Transcribing…")
        self._tray.set_state("transcribing")
        threading.Thread(
            target=self._transcribe_and_process,
            args=(audio,),
            daemon=True,
        ).start()

    def _transcribe_and_process(self, audio) -> None:
        try:
            if len(audio) == 0:
                GLib.idle_add(self._window.main_tab.set_status, "No audio captured")
                return

            text = self._transcriber.transcribe(audio, self._cfg.sample_rate)
            if not text:
                GLib.idle_add(self._window.main_tab.set_status, "Empty transcription")
                return

            GLib.idle_add(
                self._window.main_tab.append_entry, text, icons.get("microphone")
            )

            enabled = [p for p in self._registry.get_all() if p.enabled]
            if enabled:
                GLib.idle_add(self._window.main_tab.set_status, "Processing…")
                GLib.idle_add(self._tray.set_state, "processing")

                def on_step(result: str, _name: str, icon: str) -> None:
                    GLib.idle_add(
                        self._window.main_tab.append_entry, result, icon, 1
                    )

                text = self._registry.run_pipeline(text, on_step)

            self._paster.paste(text)
            GLib.idle_add(self._window.main_tab.set_status, "Ready")
        except Exception:
            log.exception("Transcription / processing failed")
            GLib.idle_add(self._window.main_tab.set_status, "Error — see logs")
        finally:
            GLib.idle_add(self._window.main_tab.set_buttons_sensitive, True)
            GLib.idle_add(self._tray.set_state, "idle")

    # -- Processor toggles (GTK main-tab switches) ----------------------------

    def _on_processor_switch(self, proc_id: str, enabled: bool) -> None:
        self._registry.set_enabled(proc_id, enabled)

    def _on_processors_changed(self, _changed: set[str]) -> None:
        GLib.idle_add(
            self._window.main_tab.rebuild_processors,
            self._registry.get_all(),
            self._on_processor_switch,
        )

    # -- Settings -------------------------------------------------------------

    def _on_config_changed(self, _changed: set[str]) -> None:
        logger.set_console_enabled(self._cfg.log_to_console)

    def _on_settings_saved(self) -> None:
        self._window.main_tab.set_status("Settings saved")
