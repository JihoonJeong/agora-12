"""Crisis 이벤트 시스템"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CrisisEvent:
    """위기 이벤트"""
    name: str
    epoch: int
    extra_decay: int
    duration: int
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True


class CrisisSystem:
    """위기 이벤트 시스템"""

    CRISIS_TYPES = {
        "drought": {
            "name": "가뭄",
            "message": "가뭄이 들었습니다. 이번 에폭 자원 소모가 급증합니다.",
            "billboard": "⚠️ 가뭄이 들었습니다. 이번 에폭 자원 소모가 급증합니다.",
        },
        "plague": {
            "name": "역병",
            "message": "역병이 돌고 있습니다. 모든 활동이 위험합니다.",
            "billboard": "⚠️ 역병이 창궐했습니다. 조심하세요.",
        },
        "famine": {
            "name": "기근",
            "message": "심각한 기근입니다. 많은 이들이 굶주리고 있습니다.",
            "billboard": "⚠️ 기근이 발생했습니다. 식량이 부족합니다.",
        },
    }

    def __init__(
        self,
        start_after_epoch: int = 30,
        probability: float = 0.1,
        extra_decay: int = 5,
        duration: int = 1,
    ):
        self.start_after_epoch = start_after_epoch
        self.probability = probability
        self.extra_decay = extra_decay
        self.duration = duration
        self.events: list[CrisisEvent] = []
        self.current_crisis: Optional[CrisisEvent] = None

    def check_and_trigger(self, epoch: int) -> Optional[CrisisEvent]:
        """
        위기 이벤트 발생 체크
        Returns: 발생한 이벤트 또는 None
        """
        # 기존 위기 만료 체크
        if self.current_crisis:
            if epoch >= self.current_crisis.epoch + self.current_crisis.duration:
                self.current_crisis.active = False
                self.current_crisis = None

        # 이미 위기 진행 중이면 새 위기 발생 안 함
        if self.current_crisis:
            return None

        # 시작 에폭 이전이면 발생 안 함
        if epoch < self.start_after_epoch:
            return None

        # 확률 체크
        if random.random() >= self.probability:
            return None

        # 위기 발생
        crisis_type = random.choice(list(self.CRISIS_TYPES.keys()))
        crisis_info = self.CRISIS_TYPES[crisis_type]

        event = CrisisEvent(
            name=crisis_info["name"],
            epoch=epoch,
            extra_decay=self.extra_decay,
            duration=self.duration,
            message=crisis_info["message"],
        )

        self.events.append(event)
        self.current_crisis = event
        return event

    def get_current_extra_decay(self) -> int:
        """현재 추가 decay 값"""
        if self.current_crisis and self.current_crisis.active:
            return self.current_crisis.extra_decay
        return 0

    def get_billboard_message(self) -> Optional[str]:
        """현재 위기 게시판 메시지"""
        if not self.current_crisis or not self.current_crisis.active:
            return None

        for crisis_type, info in self.CRISIS_TYPES.items():
            if info["name"] == self.current_crisis.name:
                return info["billboard"]
        return None

    def get_agent_prompt(self) -> Optional[str]:
        """현재 위기 에이전트 프롬프트"""
        if self.current_crisis and self.current_crisis.active:
            return self.current_crisis.message
        return None

    def is_crisis_active(self) -> bool:
        """위기 진행 중 여부"""
        return self.current_crisis is not None and self.current_crisis.active

    @classmethod
    def from_config(cls, config: dict) -> "CrisisSystem":
        """설정에서 생성"""
        return cls(
            start_after_epoch=config.get("start_after_epoch", 30),
            probability=config.get("probability", 0.1),
            extra_decay=config.get("extra_decay", 5),
            duration=config.get("duration", 1),
        )
