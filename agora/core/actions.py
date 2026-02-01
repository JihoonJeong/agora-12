"""행동 시스템 정의 (Phase 2)"""

from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum


class ActionType(Enum):
    SPEAK = "speak"
    TRADE = "trade"
    SUPPORT = "support"
    WHISPER = "whisper"
    MOVE = "move"
    IDLE = "idle"


@dataclass
class ActionResult:
    """행동 실행 결과"""
    success: bool
    action_type: str
    energy_change: int = 0
    influence_change: int = 0
    target_energy_change: int = 0
    target_influence_change: int = 0
    tax_paid: int = 0
    message: Optional[str] = None
    leaked: bool = False  # whisper 누출 여부
    thought: str = ""  # reasoning


@dataclass
class ActionConfig:
    """행동 설정"""
    cost: int
    direct_reward: int = 0
    support_reward: int = 0  # support당 추가 보상
    allowed_locations: list[str] = None  # None이면 모든 위치

    def __post_init__(self):
        if self.allowed_locations is None:
            self.allowed_locations = []


# 위치별 speak 타입 결정
def get_speak_type(location: str) -> str:
    if location == "plaza":
        return "speak_plaza"
    elif location.startswith("alley"):
        return "speak_alley"
    else:
        return "speak_plaza"  # 기본값


# 행동 설정 (config에서 로드하지만 기본값 정의)
DEFAULT_ACTION_CONFIGS = {
    "speak_plaza": ActionConfig(cost=2, direct_reward=0, support_reward=2,
                                allowed_locations=["plaza"]),
    "speak_alley": ActionConfig(cost=2, direct_reward=1, support_reward=2,
                                allowed_locations=["alley_a", "alley_b", "alley_c"]),
    "trade": ActionConfig(cost=2, direct_reward=4,
                         allowed_locations=["market"]),
    "support": ActionConfig(cost=1, direct_reward=0,
                           allowed_locations=["plaza", "alley_a", "alley_b", "alley_c", "market"]),
    "whisper": ActionConfig(cost=1, direct_reward=0,
                           allowed_locations=["alley_a", "alley_b", "alley_c"]),
    "move": ActionConfig(cost=0, direct_reward=0),
    "idle": ActionConfig(cost=0, direct_reward=0),
}


def can_perform_action(action_type: str, location: str, config: ActionConfig = None) -> bool:
    """해당 위치에서 행동 가능 여부"""
    if config is None:
        config = DEFAULT_ACTION_CONFIGS.get(action_type)

    if config is None:
        return False

    # allowed_locations가 비어있으면 모든 위치에서 가능
    if not config.allowed_locations:
        return True

    return location in config.allowed_locations


def get_available_actions(location: str) -> list[str]:
    """해당 위치에서 가능한 행동 목록"""
    available = []

    for action_type, config in DEFAULT_ACTION_CONFIGS.items():
        if can_perform_action(action_type, location, config):
            # speak는 위치에 따라 타입 결정
            if action_type.startswith("speak"):
                if action_type == get_speak_type(location).replace("speak_", "speak_"):
                    available.append("speak")
            else:
                available.append(action_type)

    # 중복 제거
    return list(set(available))
