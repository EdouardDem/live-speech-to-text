from ..llm_base import LLMProcessor


class OpenAIProcessor(LLMProcessor):
    """Post-processor that sends text to an OpenAI chat model."""

    PROVIDER_LABEL = "OpenAI"
    ENV_KEY = "OPENAI_API_KEY"
    SETTINGS_KEY_LABEL = "OpenAI"

    def _build_client(self, api_key: str):
        import openai  # lazy import — not everyone installs this
        return openai.OpenAI(api_key=api_key)

    def _complete(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.cfg.model,
            max_tokens=self.cfg.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
