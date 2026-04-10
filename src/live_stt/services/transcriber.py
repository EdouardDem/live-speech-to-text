import logging
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import nemo.collections.asr as nemo_asr

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

    def load(self) -> None:

        device = self._device_pref if self._device_pref != "auto" else None
        log.info("Loading model %s on %s …", self.model_name, self._device_pref)
        self._model = nemo_asr.models.ASRModel.from_pretrained(
            model_name=self.model_name,
            map_location=device,
        )
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
