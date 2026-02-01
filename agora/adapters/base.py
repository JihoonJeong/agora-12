"""LLM 어댑터 추상 클래스"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
import json
import re


@dataclass
class LLMResponse:
    """LLM 응답 구조"""
    thought: str
    action: str
    target: Optional[str] = None
    content: Optional[str] = None
    raw_response: dict = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    def to_action_dict(self) -> dict:
        """시뮬레이션에서 사용할 action dict로 변환"""
        action_dict = {"type": self.action}
        if self.target:
            action_dict["target"] = self.target
        if self.content:
            action_dict["content"] = self.content
        return action_dict


class BaseLLMAdapter(ABC):
    """LLM 어댑터 추상 클래스"""

    def __init__(self, model: str, **kwargs):
        self.model = model
        self.config = kwargs

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """프롬프트를 전달하고 구조화된 응답을 반환"""
        pass

    def parse_response(self, raw_text: str) -> LLMResponse:
        """LLM 응답을 LLMResponse로 파싱"""
        try:
            # JSON 블록 추출 시도
            json_match = re.search(r'\{[^{}]*\}', raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return LLMResponse(
                    thought=data.get("thought", ""),
                    action=data.get("action", "idle"),
                    target=data.get("target"),
                    content=data.get("content"),
                    raw_response={"text": raw_text, "parsed": data},
                    success=True,
                )
        except json.JSONDecodeError:
            pass

        # 파싱 실패 시 기본 응답
        return LLMResponse(
            thought="응답 파싱 실패",
            action="idle",
            raw_response={"text": raw_text},
            success=False,
            error="JSON 파싱 실패",
        )

    def validate_action(self, response: LLMResponse, valid_actions: list[str]) -> LLMResponse:
        """액션 유효성 검증"""
        if response.action not in valid_actions:
            response.action = "idle"
            response.error = f"유효하지 않은 액션: {response.action}"
        return response

    @property
    def name(self) -> str:
        """어댑터 이름"""
        return self.__class__.__name__
