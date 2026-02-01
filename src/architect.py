"""건축가 스킬 시스템"""

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent
    from .environment import Environment
    from .market import Treasury


@dataclass
class ArchitectSkillResult:
    """건축가 스킬 실행 결과"""
    success: bool
    skill_name: str
    energy_cost: int = 0
    treasury_cost: int = 0
    message: str = ""
    details: dict = None


class ArchitectSkills:
    """건축가 전용 스킬"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.billboard_cost = self.config.get("build_billboard", {}).get("cost", 10)
        self.adjust_tax_cost = self.config.get("adjust_tax", {}).get("cost", 5)
        self.min_tax_rate = self.config.get("adjust_tax", {}).get("min_rate", 0.0)
        self.max_tax_rate = self.config.get("adjust_tax", {}).get("max_rate", 0.3)

    def build_billboard(
        self,
        architect: "Agent",
        message: str,
        env: "Environment",
    ) -> ArchitectSkillResult:
        """광장에 공지사항 게시"""
        if architect.persona != "architect":
            return ArchitectSkillResult(
                success=False,
                skill_name="build_billboard",
                message="건축가만 사용 가능합니다."
            )

        if architect.energy < self.billboard_cost:
            return ArchitectSkillResult(
                success=False,
                skill_name="build_billboard",
                message=f"에너지가 부족합니다. (필요: {self.billboard_cost})"
            )

        architect.spend_energy(self.billboard_cost)
        env.post_billboard(message, architect.id)

        return ArchitectSkillResult(
            success=True,
            skill_name="build_billboard",
            energy_cost=self.billboard_cost,
            message=f"게시판에 공지: {message}",
            details={"billboard_message": message}
        )

    def adjust_tax(
        self,
        architect: "Agent",
        new_rate: float,
        env: "Environment",
    ) -> ArchitectSkillResult:
        """시장 세율 조절"""
        if architect.persona != "architect":
            return ArchitectSkillResult(
                success=False,
                skill_name="adjust_tax",
                message="건축가만 사용 가능합니다."
            )

        if not self.min_tax_rate <= new_rate <= self.max_tax_rate:
            return ArchitectSkillResult(
                success=False,
                skill_name="adjust_tax",
                message=f"세율은 {self.min_tax_rate}~{self.max_tax_rate} 범위여야 합니다."
            )

        if architect.energy < self.adjust_tax_cost:
            return ArchitectSkillResult(
                success=False,
                skill_name="adjust_tax",
                message=f"에너지가 부족합니다. (필요: {self.adjust_tax_cost})"
            )

        old_rate = env.get_market_tax_rate()
        architect.spend_energy(self.adjust_tax_cost)
        env.set_market_tax_rate(new_rate)

        return ArchitectSkillResult(
            success=True,
            skill_name="adjust_tax",
            energy_cost=self.adjust_tax_cost,
            message=f"세율 변경: {old_rate*100:.0f}% → {new_rate*100:.0f}%",
            details={"old_rate": old_rate, "new_rate": new_rate}
        )

    def grant_subsidy(
        self,
        architect: "Agent",
        target: "Agent",
        amount: int,
        treasury: "Treasury",
    ) -> ArchitectSkillResult:
        """공공 자금에서 보조금 지급"""
        if architect.persona != "architect":
            return ArchitectSkillResult(
                success=False,
                skill_name="grant_subsidy",
                message="건축가만 사용 가능합니다."
            )

        if amount <= 0:
            return ArchitectSkillResult(
                success=False,
                skill_name="grant_subsidy",
                message="지급 금액은 양수여야 합니다."
            )

        if treasury.balance < amount:
            return ArchitectSkillResult(
                success=False,
                skill_name="grant_subsidy",
                message=f"공공자금이 부족합니다. (잔액: {treasury.balance}, 요청: {amount})"
            )

        if not target.is_alive:
            return ArchitectSkillResult(
                success=False,
                skill_name="grant_subsidy",
                message=f"{target.id}는 이미 사망했습니다."
            )

        treasury.withdraw(amount)
        target.gain_energy(amount)

        return ArchitectSkillResult(
            success=True,
            skill_name="grant_subsidy",
            treasury_cost=amount,
            message=f"{target.id}에게 {amount} 에너지 지급",
            details={"target_id": target.id, "amount": amount}
        )
