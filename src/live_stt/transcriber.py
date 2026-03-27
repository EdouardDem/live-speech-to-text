import logging
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

log = logging.getLogger(__name__)


class Transcriber:
    """Wraps an NVIDIA NeMo ASR model (Parakeet) for offline transcription."""

    def __init__(
        self,
        model_name: str = "nvidia/parakeet-tdt-0.6b-v3",
        device: str = "auto",
    ):
        self.model_name = model_name
        self._device_pref = device
        self._model = None

    def _resolve_device(self) -> str:
        if self._device_pref != "auto":
            return self._device_pref
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def load(self) -> None:
        import nemo.collections.asr as nemo_asr

        device = self._resolve_device()
        log.info("Loading model %s on %s …", self.model_name, device)
        self._model = nemo_asr.models.ASRModel.from_pretrained(
            model_name=self.model_name,
        )
        if device == "cuda":
            self._model = self._model.cuda()
        self._model.eval()
        log.info("Model ready.")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if self._model is None:
            self.load()

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = Path(tmp.name)
        tmp.close()
        try:
            sf.write(str(tmp_path), audio, sample_rate)
            output = self._model.transcribe([str(tmp_path)])
            first = output[0]
            return (first.text if hasattr(first, "text") else str(first)).strip()
        finally:
            tmp_path.unlink(missing_ok=True)
