"""Environment 클래스 정의"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Space:
    """공간 정의"""
    name: str
    capacity: int
    visibility: str  # "public" or "members_only"
    tax_rate: float = 0.0  # 시장에서만 사용

    def is_public(self) -> bool:
        return self.visibility == "public"


@dataclass
class Billboard:
    """광장 게시판"""
    message: str
    posted_by: str
    posted_at_epoch: int
    expires_at_epoch: int  # 다음 에폭에 만료

    def is_expired(self, current_epoch: int) -> bool:
        return current_epoch >= self.expires_at_epoch


@dataclass
class Environment:
    """시뮬레이션 환경"""

    spaces: dict[str, Space] = field(default_factory=dict)
    treasury: int = 0
    billboard: Optional[Billboard] = None
    current_epoch: int = 0

    @classmethod
    def from_config(cls, config: dict) -> "Environment":
        """설정에서 환경 생성"""
        spaces = {}
        for name, space_config in config.get("spaces", {}).items():
            spaces[name] = Space(
                name=name,
                capacity=space_config.get("capacity", 12),
                visibility=space_config.get("visibility", "public"),
                tax_rate=space_config.get("tax_rate", 0.0),
            )

        treasury_config = config.get("treasury", {})
        initial_treasury = treasury_config.get("initial", 0)

        return cls(spaces=spaces, treasury=initial_treasury)

    def get_space(self, name: str) -> Optional[Space]:
        """공간 조회"""
        return self.spaces.get(name)

    def get_market_tax_rate(self) -> float:
        """시장 세율 조회"""
        market = self.spaces.get("market")
        return market.tax_rate if market else 0.0

    def set_market_tax_rate(self, rate: float) -> bool:
        """시장 세율 조절 (0.0 ~ 0.3)"""
        if not 0.0 <= rate <= 0.3:
            return False
        market = self.spaces.get("market")
        if market:
            market.tax_rate = rate
            return True
        return False

    def add_to_treasury(self, amount: int) -> None:
        """공공 자금 적립"""
        self.treasury += amount

    def withdraw_from_treasury(self, amount: int) -> bool:
        """공공 자금 인출. 성공 여부 반환"""
        if self.treasury >= amount:
            self.treasury -= amount
            return True
        return False

    def post_billboard(self, message: str, posted_by: str) -> None:
        """게시판에 공지 게시 (다음 에폭까지 유지)"""
        self.billboard = Billboard(
            message=message,
            posted_by=posted_by,
            posted_at_epoch=self.current_epoch,
            expires_at_epoch=self.current_epoch + 2,  # 현재 + 다음 에폭까지
        )

    def check_billboard_expiry(self) -> Optional[str]:
        """게시판 만료 체크. 만료된 메시지 반환"""
        if self.billboard and self.billboard.is_expired(self.current_epoch):
            expired_message = self.billboard.message
            self.billboard = None
            return expired_message
        return None

    def get_active_billboard(self) -> Optional[str]:
        """활성 게시판 메시지 반환"""
        if self.billboard and not self.billboard.is_expired(self.current_epoch):
            return self.billboard.message
        return None

    def advance_epoch(self) -> None:
        """에폭 진행"""
        self.current_epoch += 1

    def get_space_names(self) -> list[str]:
        """모든 공간 이름 반환"""
        return list(self.spaces.keys())

    def to_dict(self) -> dict:
        """직렬화용 딕셔너리 변환"""
        return {
            "current_epoch": self.current_epoch,
            "treasury": self.treasury,
            "billboard": self.billboard.message if self.billboard else None,
            "market_tax_rate": self.get_market_tax_rate(),
            "spaces": {name: {"capacity": s.capacity, "visibility": s.visibility}
                      for name, s in self.spaces.items()},
        }
