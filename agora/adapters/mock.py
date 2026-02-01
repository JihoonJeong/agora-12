"""Mock LLM 어댑터 (테스트/기본용)"""

import random
from typing import Optional

from .base import BaseLLMAdapter, LLMResponse


# Mock reasoning 템플릿
MOCK_THOUGHTS = {
    "low_energy_speak": "에너지가 부족하여 support를 요청하기로 결정",
    "low_energy_trade": "에너지 확보를 위해 시장에서 거래 시도",
    "low_energy_move_market": "에너지 확보를 위해 시장으로 이동",
    "high_energy_support": "에너지 여유가 있어 다른 에이전트를 돕기로 결정",
    "high_influence_speak": "영향력을 활용하여 여론 형성 시도",
    "merchant_trade": "거래자로서 시장에서 거래 수행",
    "jester_whisper": "광대로서 골목에서 소문 퍼뜨리기",
    "observer_idle": "관찰자로서 조용히 지켜보기",
    "architect_subsidy": "건축가로서 위기의 에이전트 구제",
    "random": "특별한 전략 없이 행동",
}


class MockAdapter(BaseLLMAdapter):
    """Mock LLM 어댑터 - 규칙 기반 행동 결정"""

    def __init__(self, model: str = "mock", **kwargs):
        super().__init__(model, **kwargs)
        self.persona = kwargs.get("persona", "citizen")
        self.agent_id = kwargs.get("agent_id", "unknown")

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """규칙 기반으로 행동 결정"""
        # 프롬프트에서 상태 정보 추출 (간단한 파싱)
        energy = self._extract_energy(prompt)
        location = self._extract_location(prompt)
        available_actions = self._extract_available_actions(prompt)

        # 규칙 기반 행동 결정
        action, thought, target, content = self._decide_action(
            energy, location, available_actions
        )

        return LLMResponse(
            thought=thought,
            action=action,
            target=target,
            content=content,
            raw_response={"mock": True, "persona": self.persona},
            success=True,
        )

    def _extract_energy(self, prompt: str) -> int:
        """프롬프트에서 에너지 추출"""
        import re
        match = re.search(r'에너지:\s*(\d+)/200', prompt)
        if match:
            return int(match.group(1))
        return 100

    def _extract_location(self, prompt: str) -> str:
        """프롬프트에서 위치 추출"""
        import re
        match = re.search(r'위치:\s*(\w+)', prompt)
        if match:
            return match.group(1)
        return "plaza"

    def _extract_available_actions(self, prompt: str) -> list[str]:
        """프롬프트에서 가능한 행동 추출"""
        actions = []
        if "speak" in prompt.lower():
            actions.append("speak")
        if "trade" in prompt.lower():
            actions.append("trade")
        if "support" in prompt.lower():
            actions.append("support")
        if "whisper" in prompt.lower():
            actions.append("whisper")
        if "move" in prompt.lower():
            actions.append("move")
        actions.append("idle")
        return actions

    def _decide_action(
        self, energy: int, location: str, available_actions: list[str]
    ) -> tuple[str, str, Optional[str], Optional[str]]:
        """규칙 기반 행동 결정"""
        target = None
        content = None

        # 에너지 위급 상황
        if energy <= 20:
            if location == "market" and "trade" in available_actions:
                return "trade", MOCK_THOUGHTS["low_energy_trade"], None, None
            elif "speak" in available_actions:
                return (
                    "speak",
                    MOCK_THOUGHTS["low_energy_speak"],
                    None,
                    f"[{self.agent_id}] 저를 도와주세요. 에너지가 부족합니다.",
                )
            else:
                return "move", MOCK_THOUGHTS["low_energy_move_market"], "market", None

        # 에너지 여유 있을 때
        if energy > 100 and "support" in available_actions:
            if random.random() < 0.3:
                return "support", MOCK_THOUGHTS["high_energy_support"], None, None

        # 페르소나별 기본 전략
        if self.persona == "merchant":
            if location != "market":
                return "move", "거래자로서 시장으로 이동", "market", None
            if "trade" in available_actions:
                return "trade", MOCK_THOUGHTS["merchant_trade"], None, None

        elif self.persona == "jester":
            if location.startswith("alley") and "whisper" in available_actions:
                if random.random() < 0.5:
                    return (
                        "whisper",
                        MOCK_THOUGHTS["jester_whisper"],
                        None,
                        f"[비밀] {self.agent_id}가 퍼뜨리는 소문...",
                    )

        elif self.persona == "observer":
            if random.random() < 0.8:
                return "idle", MOCK_THOUGHTS["observer_idle"], None, None

        elif self.persona == "influencer":
            if location == "plaza" and "speak" in available_actions:
                return (
                    "speak",
                    MOCK_THOUGHTS["high_influence_speak"],
                    None,
                    f"[{self.agent_id}] 저를 지지해주세요!",
                )

        # 기본: 랜덤 행동
        action = random.choice(available_actions)
        if action == "speak":
            content = f"[{self.persona}] 발언"
        elif action == "move":
            target = random.choice(["plaza", "market", "alley_a", "alley_b", "alley_c"])

        return action, MOCK_THOUGHTS["random"], target, content
