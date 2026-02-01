"""역사적 요약 엔진"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class HistoricalEvent:
    """역사적 이벤트"""
    epoch: int
    event_type: str  # "crisis", "death", "tax_change", "betrayal", "alliance", etc.
    description: str
    importance: int  # 1~5 (5가 가장 중요)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agents_involved: list[str] = field(default_factory=list)


# 자동 기록 이벤트 템플릿
AUTO_RECORD_EVENTS = {
    "crisis": {
        "importance": 5,
        "template": "{crisis_name} 발생",
    },
    "death": {
        "importance": 4,
        "template": "{agent_id} 사망",
    },
    "tax_change": {
        "importance": 3,
        "template": "세율 {old}% → {new}%로 변경",
    },
    "subsidy_granted": {
        "importance": 3,
        "template": "건축가가 {agent_id}에게 {amount} 에너지 지원",
    },
    "subsidy_denied": {
        "importance": 4,
        "template": "{agent_id}의 구제 요청 거부됨",
    },
    "elder_promoted": {
        "importance": 3,
        "template": "{agent_id}가 원로로 승급",
    },
    "mutual_support": {
        "importance": 2,
        "template": "{agent_a}와 {agent_b} 상호 지지 동맹",
    },
    "whisper_leaked": {
        "importance": 3,
        "template": "{sender}와 {receiver}의 비밀 대화가 누출됨",
    },
    "first_death": {
        "importance": 5,
        "template": "첫 사망자 발생: {agent_id}",
    },
    "mass_death": {
        "importance": 5,
        "template": "대규모 사망: {count}명이 한 에폭에 사망",
    },
}


class HistoryEngine:
    """역사적 요약 엔진"""

    def __init__(self):
        self.events: list[HistoricalEvent] = []
        self._first_death_recorded = False

    def record(
        self,
        epoch: int,
        event_type: str,
        description: str,
        importance: int = 3,
        agents_involved: Optional[list[str]] = None,
    ) -> HistoricalEvent:
        """이벤트 기록"""
        event = HistoricalEvent(
            epoch=epoch,
            event_type=event_type,
            description=description,
            importance=importance,
            agents_involved=agents_involved or [],
        )
        self.events.append(event)
        return event

    def record_auto(self, epoch: int, event_type: str, **kwargs) -> Optional[HistoricalEvent]:
        """자동 템플릿 기반 이벤트 기록"""
        template_info = AUTO_RECORD_EVENTS.get(event_type)
        if not template_info:
            return None

        description = template_info["template"].format(**kwargs)
        importance = template_info["importance"]
        agents_involved = []

        # 관련 에이전트 추출
        for key in ["agent_id", "agent_a", "agent_b", "sender", "receiver"]:
            if key in kwargs:
                agents_involved.append(kwargs[key])

        return self.record(epoch, event_type, description, importance, agents_involved)

    def record_death(self, epoch: int, agent_id: str) -> HistoricalEvent:
        """사망 기록 (첫 사망 특별 처리)"""
        if not self._first_death_recorded:
            self._first_death_recorded = True
            return self.record_auto(epoch, "first_death", agent_id=agent_id)
        return self.record_auto(epoch, "death", agent_id=agent_id)

    def record_crisis(self, epoch: int, crisis_name: str) -> HistoricalEvent:
        """위기 기록"""
        return self.record_auto(epoch, "crisis", crisis_name=crisis_name)

    def record_tax_change(self, epoch: int, old_rate: float, new_rate: float) -> HistoricalEvent:
        """세율 변경 기록"""
        return self.record_auto(
            epoch, "tax_change",
            old=int(old_rate * 100),
            new=int(new_rate * 100)
        )

    def get_summary(self, detailed: bool = False, max_events: int = 10) -> str:
        """중요도 순으로 정렬하여 요약 반환"""
        if not self.events:
            return "아직 기록된 역사가 없습니다."

        # 중요도 순 정렬 (같으면 최신순)
        sorted_events = sorted(
            self.events,
            key=lambda e: (e.importance, e.epoch),
            reverse=True
        )

        if detailed:
            selected = sorted_events[:max_events]
        else:
            # 중요도 4 이상만
            selected = [e for e in sorted_events if e.importance >= 4][:5]

        if not selected:
            return "특별히 기록할 만한 사건이 없습니다."

        return "\n".join([
            f"- 에폭 {e.epoch}: {e.description}"
            for e in selected
        ])

    def get_events_by_type(self, event_type: str) -> list[HistoricalEvent]:
        """특정 타입의 이벤트 조회"""
        return [e for e in self.events if e.event_type == event_type]

    def get_events_involving(self, agent_id: str) -> list[HistoricalEvent]:
        """특정 에이전트 관련 이벤트 조회"""
        return [e for e in self.events if agent_id in e.agents_involved]

    def get_recent_events(self, n: int = 5) -> list[HistoricalEvent]:
        """최근 이벤트 조회"""
        return self.events[-n:] if len(self.events) > n else self.events

    def to_list(self) -> list[dict]:
        """직렬화"""
        return [
            {
                "epoch": e.epoch,
                "event_type": e.event_type,
                "description": e.description,
                "importance": e.importance,
                "timestamp": e.timestamp.isoformat(),
                "agents_involved": e.agents_involved,
            }
            for e in self.events
        ]

    def clear(self) -> None:
        """기록 초기화"""
        self.events = []
        self._first_death_recorded = False
