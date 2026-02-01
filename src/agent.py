"""Agent 클래스 정의 (Phase 2)"""

from dataclasses import dataclass, field
from typing import Optional

from .personas import get_persona_prompt


@dataclass
class Agent:
    """시뮬레이션에 참여하는 에이전트"""

    id: str
    persona: str
    energy: int = 100
    influence: int = 0
    location: str = "plaza"
    home: str = "plaza"
    alive: bool = True
    max_energy: int = 200  # Phase 2: 에너지 상한

    # Phase 2: 심증 목록 (whisper 누출로 인한)
    suspicions: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.system_prompt = get_persona_prompt(self.persona)
        if not hasattr(self, 'suspicions') or self.suspicions is None:
            self.suspicions = []

    @property
    def is_alive(self) -> bool:
        """에이전트 생존 여부"""
        return self.alive and self.energy > 0

    def decay_energy(self, amount: int) -> None:
        """매 에폭 에너지 감소"""
        self.energy = max(0, self.energy - amount)
        if self.energy <= 0:
            self.alive = False

    def spend_energy(self, cost: int) -> bool:
        """행동에 에너지 소비. 성공 여부 반환"""
        if self.energy >= cost:
            self.energy -= cost
            return True
        return False

    def gain_energy(self, amount: int) -> None:
        """에너지 획득 (상한 적용)"""
        self.energy = min(self.energy + amount, self.max_energy)

    def gain_influence(self, amount: int = 1) -> None:
        """영향력 획득"""
        self.influence += amount

    def move_to(self, location: str) -> None:
        """위치 이동"""
        self.location = location

    def add_suspicion(self, message: str) -> None:
        """심증 추가 (whisper 누출로 인한)"""
        self.suspicions.append(message)

    def get_recent_suspicions(self, n: int = 3) -> list[str]:
        """최근 심증 목록"""
        return self.suspicions[-n:] if self.suspicions else []

    def clear_suspicions(self) -> None:
        """심증 초기화"""
        self.suspicions = []

    def to_dict(self) -> dict:
        """직렬화용 딕셔너리 변환"""
        return {
            "id": self.id,
            "persona": self.persona,
            "energy": self.energy,
            "influence": self.influence,
            "location": self.location,
            "home": self.home,
            "alive": self.alive,
            "max_energy": self.max_energy,
        }

    def get_resources(self) -> dict:
        """현재 자원 상태 반환"""
        return {
            "energy": self.energy,
            "influence": self.influence,
        }

    def get_energy_status(self) -> str:
        """에너지 상태 문구"""
        if self.energy <= 20:
            return "⚠️ 위험! 곧 죽을 수 있습니다."
        elif self.energy <= 50:
            return "⚡ 부족합니다. 에너지 확보가 시급합니다."
        elif self.energy <= 100:
            return "보통입니다."
        else:
            return "✨ 여유롭습니다. 다른 이를 도울 여력이 있습니다."

    def __repr__(self) -> str:
        status = "alive" if self.is_alive else "dead"
        return f"Agent({self.id}, {self.persona}, E:{self.energy}/{self.max_energy}, I:{self.influence}, @{self.location}, {status})"


def create_agents_from_config(
    agent_configs: list,
    initial_energy: int = 100,
    max_energy: int = 200,
) -> list[Agent]:
    """설정에서 에이전트 목록 생성"""
    agents = []
    for config in agent_configs:
        agent = Agent(
            id=config["id"],
            persona=config["persona"],
            energy=initial_energy,
            influence=0,
            location=config.get("home", "plaza"),
            home=config.get("home", "plaza"),
            max_energy=max_energy,
        )
        agents.append(agent)
    return agents
