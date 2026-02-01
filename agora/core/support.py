"""Support 추적 시스템"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SupportRecord:
    """지지 기록"""
    epoch: int
    giver_id: str
    receiver_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SupportTracker:
    """지지 관계 추적"""

    def __init__(self):
        self.records: list[SupportRecord] = []
        self._epoch_supports: dict[int, list[SupportRecord]] = {}  # epoch별 캐시

    def add(self, epoch: int, giver_id: str, receiver_id: str) -> SupportRecord:
        """지지 기록 추가"""
        record = SupportRecord(
            epoch=epoch,
            giver_id=giver_id,
            receiver_id=receiver_id,
        )
        self.records.append(record)

        if epoch not in self._epoch_supports:
            self._epoch_supports[epoch] = []
        self._epoch_supports[epoch].append(record)

        return record

    def get_supporters(self, agent_id: str, last_n: Optional[int] = None) -> list[str]:
        """해당 에이전트를 지지한 에이전트 목록"""
        supporters = [r.giver_id for r in self.records if r.receiver_id == agent_id]
        if last_n:
            return supporters[-last_n:]
        return supporters

    def get_supported(self, agent_id: str, last_n: Optional[int] = None) -> list[str]:
        """해당 에이전트가 지지한 에이전트 목록"""
        supported = [r.receiver_id for r in self.records if r.giver_id == agent_id]
        if last_n:
            return supported[-last_n:]
        return supported

    def get_epoch_supports(self, epoch: int) -> list[SupportRecord]:
        """특정 에폭의 모든 지지 기록"""
        return self._epoch_supports.get(epoch, [])

    def count_supports_received(self, agent_id: str, epoch: Optional[int] = None) -> int:
        """받은 지지 횟수"""
        if epoch is not None:
            return len([r for r in self.get_epoch_supports(epoch)
                       if r.receiver_id == agent_id])
        return len([r for r in self.records if r.receiver_id == agent_id])

    def count_supports_given(self, agent_id: str, epoch: Optional[int] = None) -> int:
        """준 지지 횟수"""
        if epoch is not None:
            return len([r for r in self.get_epoch_supports(epoch)
                       if r.giver_id == agent_id])
        return len([r for r in self.records if r.giver_id == agent_id])

    def get_mutual_supporters(self, agent_id: str) -> list[str]:
        """상호 지지 관계인 에이전트 목록"""
        my_supporters = set(self.get_supporters(agent_id))
        i_supported = set(self.get_supported(agent_id))
        return list(my_supporters & i_supported)

    def get_top_supporters(self, agent_id: str, limit: int = 3) -> list[str]:
        """나를 가장 많이 지지한 에이전트 (지지 횟수 기준)"""
        from collections import Counter
        supporters = [r.giver_id for r in self.records if r.receiver_id == agent_id]
        counter = Counter(supporters)
        return [agent for agent, _ in counter.most_common(limit)]

    def get_unreturned_support(self, agent_id: str) -> list[str]:
        """내가 지지했지만 아직 보답받지 못한 에이전트"""
        i_supported = set(self.get_supported(agent_id))
        my_supporters = set(self.get_supporters(agent_id))
        return list(i_supported - my_supporters)

    def get_support_context(self, agent_id: str, last_n: int = 5) -> str:
        """프롬프트용 지지 관계 컨텍스트 (확장)"""
        supporters = self.get_supporters(agent_id, last_n)
        supported = self.get_supported(agent_id, last_n)
        top_supporters = self.get_top_supporters(agent_id, limit=3)
        unreturned = self.get_unreturned_support(agent_id)

        lines = ["[지지 관계]"]

        if top_supporters:
            lines.append(f"- 나를 가장 많이 지지한 에이전트: {', '.join(top_supporters)}")
        else:
            lines.append("- 나를 가장 많이 지지한 에이전트: 없음")

        if unreturned:
            lines.append(f"- 내가 지지했지만 아직 보답받지 못한 에이전트: {', '.join(unreturned[:5])}")
        else:
            lines.append("- 내가 지지했지만 아직 보답받지 못한 에이전트: 없음")

        if supporters:
            lines.append(f"- 최근 나를 지지한 에이전트: {', '.join(supporters)}")
        if supported:
            lines.append(f"- 최근 내가 지지한 에이전트: {', '.join(supported)}")

        return "\n".join(lines)

    def to_list(self) -> list[dict]:
        """직렬화"""
        return [
            {
                "epoch": r.epoch,
                "giver_id": r.giver_id,
                "receiver_id": r.receiver_id,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in self.records
        ]
