"""OpenAI LLM 어댑터 (GPT 및 호환 API)"""

import os
from typing import Optional

from .base import BaseLLMAdapter, LLMResponse


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI GPT 어댑터 (및 호환 API)"""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url  # OpenAI 호환 API용 (예: Together, Groq)

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """OpenAI API를 통해 응답 생성"""
        if not self.api_key:
            return LLMResponse(
                thought="OPENAI_API_KEY가 설정되지 않았습니다",
                action="idle",
                raw_response={"error": "no_api_key"},
                success=False,
                error="API 키 없음",
            )

        try:
            from openai import OpenAI

            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            client = OpenAI(**client_kwargs)

            response = client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            raw_text = response.choices[0].message.content
            return self.parse_response(raw_text)

        except ImportError:
            return LLMResponse(
                thought="openai 패키지가 설치되지 않았습니다",
                action="idle",
                raw_response={"error": "import_error"},
                success=False,
                error="pip install openai 필요",
            )
        except Exception as e:
            return LLMResponse(
                thought=f"OpenAI API 오류: {str(e)}",
                action="idle",
                raw_response={"error": str(e)},
                success=False,
                error=str(e),
            )
