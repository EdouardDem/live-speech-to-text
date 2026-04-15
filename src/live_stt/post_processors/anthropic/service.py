from ..llm_base import LLMProcessor


class AnthropicProcessor(LLMProcessor):
    """Post-processor that sends text to a Claude model via the Anthropic API."""

    PROVIDER_LABEL = "Claude"
    ENV_KEY = "ANTHROPIC_API_KEY"
    SETTINGS_KEY_LABEL = "Anthropic"

    def _build_client(self, api_key: str):
        import anthropic  # lazy import — not everyone installs this
        return anthropic.Anthropic(api_key=api_key)

    def _complete(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self.cfg.model,
            max_tokens=self.cfg.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
