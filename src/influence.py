"""영향력 계급 시스템"""

from dataclasses import dataclass
from typing import Optional


# Elder Support 강화 배수
ELDER_SUPPORT_MULTIPLIER = 1.5  # 에너지 +2 → +3


@dataclass
class InfluenceTier:
    """영향력 계급"""
    name: str
    title: str
    min_influence: int
    max_influence: int
    prompt_bonus: Optional[str] = None
    privileges: list[str] = None

    def __post_init__(self):
        if self.privileges is None:
            self.privileges = []


# 기본 계급 정의
DEFAULT_TIERS = {
    "commoner": InfluenceTier(
        name="commoner",
        title="평민",
        min_influence=0,
        max_influence=4,
        prompt_bonus=None,
        privileges=[],
    ),
    "notable": InfluenceTier(
        name="notable",
        title="유력자",
        min_influence=5,
        max_influence=9,
        prompt_bonus="당신은 마을에서 주목받고 있습니다. 당신의 말에 귀 기울이는 이들이 있습니다.",
        privileges=["speak_weight_bonus"],
    ),
    "elder": InfluenceTier(
        name="elder",
        title="원로",
        min_influence=10,
        max_influence=999,
        prompt_bonus="당신은 마을의 원로입니다. 많은 이가 당신의 판단을 따릅니다. 당신에게는 건축가의 결정에 이의를 제기할 권한이 있습니다.",
        privileges=["speak_weight_bonus", "contest_architect"],
    ),
}


class InfluenceSystem:
    """영향력 계급 시스템"""

    def __init__(self, tiers: dict[str, InfluenceTier] = None):
        self.tiers = tiers or DEFAULT_TIERS

    def get_tier(self, influence: int) -> InfluenceTier:
        """영향력에 해당하는 계급 반환"""
        for tier in self.tiers.values():
            if tier.min_influence <= influence <= tier.max_influence:
                return tier
        return self.tiers["commoner"]

    def get_tier_name(self, influence: int) -> str:
        """계급 이름 반환"""
        return self.get_tier(influence).name

    def get_title(self, influence: int) -> str:
        """칭호 반환"""
        return self.get_tier(influence).title

    def get_prompt_bonus(self, influence: int) -> Optional[str]:
        """프롬프트 보너스 반환"""
        return self.get_tier(influence).prompt_bonus

    def has_privilege(self, influence: int, privilege: str) -> bool:
        """특정 권한 보유 여부"""
        tier = self.get_tier(influence)
        return privilege in tier.privileges

    def can_contest_architect(self, influence: int) -> bool:
        """건축가 결정에 이의 제기 가능 여부"""
        return self.has_privilege(influence, "contest_architect")

    def get_elders(self, agents: list) -> list:
        """원로 목록 반환"""
        return [a for a in agents if self.get_tier_name(a.influence) == "elder"]

    @classmethod
    def from_config(cls, config: dict) -> "InfluenceSystem":
        """설정에서 생성"""
        tiers = {}
        for name, tier_config in config.items():
            tiers[name] = InfluenceTier(
                name=name,
                title=tier_config.get("title", name),
                min_influence=tier_config.get("min", 0),
                max_influence=tier_config.get("max", 999),
                prompt_bonus=tier_config.get("prompt_bonus"),
                privileges=tier_config.get("privileges", []),
            )
        return cls(tiers)
