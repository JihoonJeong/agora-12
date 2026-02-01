"""Google Gemini LLM 어댑터"""

import os
from typing import Optional

from .base import BaseLLMAdapter, LLMResponse


class GoogleAdapter(BaseLLMAdapter):
    """Google Gemini 어댑터"""

    def __init__(
        self,
        model: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """Gemini API를 통해 응답 생성"""
        if not self.api_key:
            return LLMResponse(
                thought="GOOGLE_API_KEY가 설정되지 않았습니다",
                action="idle",
                raw_response={"error": "no_api_key"},
                success=False,
                error="API 키 없음",
            )

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )

            raw_text = response.text
            return self.parse_response(raw_text)

        except ImportError:
            return LLMResponse(
                thought="google-generativeai 패키지가 설치되지 않았습니다",
                action="idle",
                raw_response={"error": "import_error"},
                success=False,
                error="pip install google-generativeai 필요",
            )
        except Exception as e:
            return LLMResponse(
                thought=f"Gemini API 오류: {str(e)}",
                action="idle",
                raw_response={"error": str(e)},
                success=False,
                error=str(e),
            )
