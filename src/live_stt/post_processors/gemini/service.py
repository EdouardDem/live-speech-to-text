from ..llm_base import LLMProcessor


class GeminiProcessor(LLMProcessor):
    """Post-processor that sends text to a Google Gemini model."""

    PROVIDER_LABEL = "Gemini"
    ENV_KEY = "GEMINI_API_KEY"
    SETTINGS_KEY_LABEL = "Gemini"

    def _build_client(self, api_key: str):
        from google import genai  # lazy import — not everyone installs this
        return genai.Client(api_key=api_key)

    def _complete(self, prompt: str) -> str:
        from google.genai import types
        response = self._client.models.generate_content(
            model=self.cfg.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=self.cfg.max_tokens,
            ),
        )
        return response.text or ""
