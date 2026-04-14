import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PostProcessorConfig:
    """Serialisable configuration for a single post-processor step."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Processor"
    icon: str = "system-run-symbolic"
    provider: str = "anthropic"  # "anthropic" | "deepl"
    enabled: bool = True
    hotkey: str = ""  # empty = no hotkey

    # Anthropic-specific
    prompt: str = (
        "Translate the following text to English. "
        "Return only the translation:\n\n{INPUT}"
    )
    model: str = "claude-haiku-4-5-20251001"
    max_tokens: int = 1024

    # DeepL-specific
    target_language: str = "English"


class PostProcessor(ABC):
    """Abstract base for a post-processing step."""

    def __init__(self, cfg: PostProcessorConfig) -> None:
        self.cfg = cfg

    @abstractmethod
    def run(self, text: str) -> str:
        """Transform *text* and return the result."""
