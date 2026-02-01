"""Anthropic Claude LLM 어댑터"""

import os
from typing import Optional

from .base import BaseLLMAdapter, LLMResponse


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic Claude 어댑터"""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.max_tokens = kwargs.get("max_tokens", 1000)

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """Claude API를 통해 응답 생성"""
        if not self.api_key:
            return LLMResponse(
                thought="ANTHROPIC_API_KEY가 설정되지 않았습니다",
                action="idle",
                raw_response={"error": "no_api_key"},
                success=False,
                error="API 키 없음",
            )

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            raw_text = message.content[0].text
            return self.parse_response(raw_text)

        except ImportError:
            return LLMResponse(
                thought="anthropic 패키지가 설치되지 않았습니다",
                action="idle",
                raw_response={"error": "import_error"},
                success=False,
                error="pip install anthropic 필요",
            )
        except Exception as e:
            return LLMResponse(
                thought=f"Claude API 오류: {str(e)}",
                action="idle",
                raw_response={"error": str(e)},
                success=False,
                error=str(e),
            )
