import os

from ..base import PostProcessor, PostProcessorConfig
from ...services import logger

log = logger.get(__name__)


class AnthropicProcessor(PostProcessor):
    """Post-processor that sends text to a Claude model via the Anthropic API."""

    def __init__(self, cfg: PostProcessorConfig, api_key: str = "") -> None:
        super().__init__(cfg)
        import anthropic  # lazy import — not everyone installs this

        key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Set it in Settings → API Keys or via ANTHROPIC_API_KEY."
            )
        self._client = anthropic.Anthropic(api_key=key)

    def run(self, text: str) -> str:
        prompt = self.cfg.prompt.replace("{INPUT}", text)
        log.debug("[%s] → Claude (%s): %s…", self.cfg.name, self.cfg.model, prompt[:80])
        response = self._client.messages.create(
            model=self.cfg.model,
            max_tokens=self.cfg.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.content[0].text.strip()
        log.debug("[%s] ← %s…", self.cfg.name, result[:80])
        return result
