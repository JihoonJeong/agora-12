"""로깅 시스템"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any


class SimulationLogger:
    """시뮬레이션 로그 기록"""

    def __init__(self, log_path: str, summary_path: str):
        self.log_path = Path(log_path)
        self.summary_path = Path(summary_path)

        # 디렉토리 생성
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)

        # 파일 초기화 (기존 내용 삭제)
        self.log_path.write_text("")
        self.summary_path.write_text("")

        self._turn_counter = 0

    def reset_turn_counter(self) -> None:
        """에폭 시작시 턴 카운터 리셋"""
        self._turn_counter = 0

    def log_action(
        self,
        epoch: int,
        agent_id: str,
        persona: str,
        location: str,
        action_type: str,
        target: Optional[str],
        content: Optional[str],
        resources_before: dict,
        resources_after: dict,
        success: bool,
        extra: Optional[dict] = None,
    ) -> None:
        """행동 로그 기록"""
        self._turn_counter += 1

        log_entry = {
            "epoch": epoch,
            "turn": self._turn_counter,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            "persona": persona,
            "location": location,
            "action_type": action_type,
            "target": target,
            "content": content,
            "resources_before": resources_before,
            "resources_after": resources_after,
            "success": success,
        }

        if extra:
            log_entry.update(extra)

        self._append_jsonl(self.log_path, log_entry)

    def log_epoch_summary(
        self,
        epoch: int,
        alive_agents: int,
        total_energy: int,
        gini_coefficient: float,
        transaction_count: int,
        billboard_active: Optional[str],
        treasury: int,
        notable_events: list[str],
    ) -> None:
        """에폭 요약 로그 기록"""
        summary = {
            "epoch": epoch,
            "alive_agents": alive_agents,
            "total_energy": total_energy,
            "gini_coefficient": round(gini_coefficient, 4),
            "transaction_count": transaction_count,
            "billboard_active": billboard_active,
            "treasury": treasury,
            "notable_events": notable_events,
        }

        self._append_jsonl(self.summary_path, summary)

    def _append_jsonl(self, path: Path, data: dict) -> None:
        """JSONL 파일에 한 줄 추가"""
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")


def calculate_gini_coefficient(values: list[int]) -> float:
    """지니 계수 계산 (0: 완전평등, 1: 완전불평등)"""
    if not values or len(values) == 0:
        return 0.0

    n = len(values)
    if n == 1:
        return 0.0

    sorted_values = sorted(values)
    total = sum(sorted_values)

    if total == 0:
        return 0.0

    cumulative = 0
    gini_sum = 0

    for i, value in enumerate(sorted_values):
        cumulative += value
        gini_sum += (2 * (i + 1) - n - 1) * value

    return gini_sum / (n * total)
