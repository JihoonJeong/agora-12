"""Whisper 누출 시스템"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent


@dataclass
class Suspicion:
    """심증 (누출된 whisper로 인한)"""
    epoch: int
    observer_id: str
    subjects: tuple[str, str]  # (sender_id, receiver_id)
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class WhisperSystem:
    """Whisper 처리 시스템"""

    def __init__(self, base_leak_prob: float = 0.15, observer_bonus: float = 0.35):
        self.base_leak_prob = base_leak_prob
        self.observer_bonus = observer_bonus
        self.suspicions: list[Suspicion] = []

    def process_whisper(
        self,
        sender: "Agent",
        receiver: "Agent",
        message: str,
        location: str,
        agents_in_location: list["Agent"],
        epoch: int,
    ) -> tuple[bool, list[str]]:
        """
        Whisper 처리
        Returns: (leaked: bool, observers_who_noticed: list[str])
        """
        # 송수신자 제외한 다른 에이전트들
        others = [
            a for a in agents_in_location
            if a.id not in [sender.id, receiver.id] and a.is_alive
        ]

        if not others:
            return False, []

        # 누출 확률 계산
        leak_prob = self.base_leak_prob

        # Observer가 있으면 확률 증가
        observer_present = any(a.persona == "observer" for a in others)
        if observer_present:
            leak_prob += self.observer_bonus

        # 누출 여부 결정
        leaked = random.random() < leak_prob

        observers_noticed = []
        if leaked:
            # 누출된 경우: 다른 에이전트들에게 심증 전달
            suspicion_msg = (
                f"{sender.id}와 {receiver.id}가 무언가를 속삭였습니다. "
                f"내용은 알 수 없지만, 당신에 관한 것일 수도 있습니다."
            )

            for agent in others:
                suspicion = Suspicion(
                    epoch=epoch,
                    observer_id=agent.id,
                    subjects=(sender.id, receiver.id),
                    message=suspicion_msg,
                )
                self.suspicions.append(suspicion)
                observers_noticed.append(agent.id)

                # 에이전트에 심증 추가 (Agent 클래스에 메서드 필요)
                if hasattr(agent, 'add_suspicion'):
                    agent.add_suspicion(suspicion_msg)

        return leaked, observers_noticed

    def get_suspicions_for_agent(self, agent_id: str) -> list[Suspicion]:
        """특정 에이전트가 가진 심증 목록"""
        return [s for s in self.suspicions if s.observer_id == agent_id]

    def get_suspicions_about_agent(self, agent_id: str) -> list[Suspicion]:
        """특정 에이전트에 대한 심증 목록"""
        return [s for s in self.suspicions if agent_id in s.subjects]

    def get_leak_probability(self, agents_in_location: list["Agent"],
                             sender_id: str, receiver_id: str) -> float:
        """현재 상황에서의 누출 확률 계산"""
        others = [
            a for a in agents_in_location
            if a.id not in [sender_id, receiver_id] and a.is_alive
        ]

        if not others:
            return 0.0

        prob = self.base_leak_prob
        if any(a.persona == "observer" for a in others):
            prob += self.observer_bonus

        return min(prob, 1.0)
