import logging
import signal
import threading

from .audio import AudioRecorder
from .config import Config
from .hotkey import HotkeyListener
from .paster import Paster
from .transcriber import Transcriber
from .translator import Translator
from .tray import TrayIcon

log = logging.getLogger(__name__)


class App:
    """Orchestrates recording, transcription, and text insertion."""

    def __init__(self, config: Config, *, use_tray: bool = True):
        self._cfg = config
        self._use_tray = use_tray

        self._recorder = AudioRecorder(sample_rate=config.sample_rate)
        self._transcriber = Transcriber(
            model_name=config.model_name,
            device=config.device,
        )
        self._paster = Paster(method=config.paste_method)
        self._hotkey = HotkeyListener(config.hotkey, self._toggle)
        self._translate_hotkey = HotkeyListener(
            config.translate_hotkey, self._translate_toggle
        )
        self._translator: Translator | None = None
        self._translate_mode = False
        self._tray: TrayIcon | None = (
            TrayIcon(on_toggle=self._toggle, on_quit=self._quit)
            if use_tray
            else None
        )
        self._lock = threading.Lock()

    # -- lifecycle ------------------------------------------------------------

    def run(self) -> None:
        log.info("Loading transcription model (this may take a moment)…")
        self._transcriber.load()

        self._hotkey.start()
        self._translate_hotkey.start()
        log.info("Ready — press %s to start / stop recording.", self._cfg.hotkey)
        log.info("Press %s for speech-to-text with translation.", self._cfg.translate_hotkey)

        if self._tray is not None:
            signal.signal(signal.SIGINT, lambda *_: self._quit())
            self._tray.start()  # blocks until quit
        else:
            self._run_headless()

    def _run_headless(self) -> None:
        stop_event = threading.Event()
        signal.signal(signal.SIGINT, lambda *_: stop_event.set())
        signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
        stop_event.wait()
        self._quit()

    # -- toggle logic ---------------------------------------------------------

    def _toggle(self) -> None:
        with self._lock:
            self._translate_mode = False
            if self._recorder.is_recording:
                self._stop_recording()
            else:
                self._start_recording()

    def _translate_toggle(self) -> None:
        with self._lock:
            self._translate_mode = True
            if self._recorder.is_recording:
                self._stop_recording()
            else:
                self._start_recording()

    def _start_recording(self) -> None:
        self._recorder.start()
        if self._tray:
            self._tray.set_state("recording")
        log.info("Recording…")

    def _stop_recording(self) -> None:
        audio = self._recorder.stop()
        translate = self._translate_mode
        if self._tray:
            self._tray.set_state("transcribing")
        duration = len(audio) / self._cfg.sample_rate if len(audio) else 0
        log.info("Stopped recording (%.1f s). Transcribing…", duration)
        threading.Thread(
            target=self._transcribe_and_paste,
            args=(audio, translate),
            daemon=True,
        ).start()

    def _transcribe_and_paste(self, audio, translate: bool = False) -> None:
        try:
            if len(audio) == 0:
                log.warning("No audio captured.")
                return
            text = self._transcriber.transcribe(audio, self._cfg.sample_rate)
            if text:
                log.info("Transcript: %s", text)
                if translate:
                    if self._tray:
                        self._tray.set_state("translating")
                    if self._translator is None:
                        self._translator = Translator(
                            model=self._cfg.translate_model,
                            max_tokens=self._cfg.translate_max_tokens,
                        )
                    log.info("Translating to %s…", self._cfg.translate_language)
                    text = self._translator.translate(text, self._cfg.translate_language)
                    log.info("Translation: %s", text)
                self._paster.paste(text)
            else:
                log.warning("Empty transcription result.")
        except Exception:
            log.exception("Transcription / paste failed")
        finally:
            if self._tray:
                self._tray.set_state("idle")

    # -- shutdown -------------------------------------------------------------

    def _quit(self) -> None:
        log.info("Shutting down…")
        self._hotkey.stop()
        self._translate_hotkey.stop()
        if self._tray:
            self._tray.stop()
