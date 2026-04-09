from dataclasses import asdict, dataclass, fields
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "live-stt" / "config.yaml"


@dataclass
class Config:
    hotkey: str = "<ctrl>+<shift>+z"
    model_name: str = "nvidia/parakeet-tdt-0.6b-v3"
    sample_rate: int = 16000
    device: str = "auto"  # auto | cpu | cuda
    paste_method: str = "auto"  # auto | xclip | xdotool | wayland
    translate_hotkey: str = "<ctrl>+<shift>+t"
    translate_language: str = "English"
    translate_model: str = "claude-3-5-haiku-latest"
    translate_max_tokens: int = 1024

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        p = Path(path) if path else DEFAULT_CONFIG_PATH
        if p.exists():
            data = yaml.safe_load(p.read_text()) or {}
            valid_keys = {f.name for f in fields(cls)}
            return cls(**{k: v for k, v in data.items() if k in valid_keys})
        return cls()

    def save(self, path: str | Path | None = None) -> None:
        p = Path(path) if path else DEFAULT_CONFIG_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.dump(asdict(self), default_flow_style=False, sort_keys=False))
