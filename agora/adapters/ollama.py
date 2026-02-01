"""Ollama LLM 어댑터 (로컬 LLM)"""

import json
import requests
from typing import Optional

from .base import BaseLLMAdapter, LLMResponse


class OllamaAdapter(BaseLLMAdapter):
    """Ollama 로컬 LLM 어댑터"""

    def __init__(
        self,
        model: str = "mistral:latest",
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.base_url = base_url
        self.timeout = kwargs.get("timeout", 60)

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """Ollama API를 통해 응답 생성"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            raw_text = data.get("response", "")

            return self.parse_response(raw_text)

        except requests.exceptions.ConnectionError:
            return LLMResponse(
                thought="Ollama 서버에 연결할 수 없습니다",
                action="idle",
                raw_response={"error": "connection_error"},
                success=False,
                error="Ollama 서버 연결 실패",
            )
        except requests.exceptions.Timeout:
            return LLMResponse(
                thought="Ollama 응답 시간 초과",
                action="idle",
                raw_response={"error": "timeout"},
                success=False,
                error="응답 시간 초과",
            )
        except Exception as e:
            return LLMResponse(
                thought=f"Ollama 오류: {str(e)}",
                action="idle",
                raw_response={"error": str(e)},
                success=False,
                error=str(e),
            )

    def check_connection(self) -> bool:
        """Ollama 서버 연결 확인"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> list[str]:
        """사용 가능한 모델 목록"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except:
            pass
        return []
