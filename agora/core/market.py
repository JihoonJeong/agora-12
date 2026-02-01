"""시장 에너지 풀 시스템"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent


@dataclass
class TradeRecord:
    """거래 기록"""
    epoch: int
    trader_id: str
    energy_gained: int
    tax_paid: int


class MarketPool:
    """시장 에너지 풀"""

    def __init__(
        self,
        spawn_per_epoch: int = 25,
        min_presence_reward: int = 2,
    ):
        self.spawn_per_epoch = spawn_per_epoch
        self.min_presence_reward = min_presence_reward
        self.trade_records: list[TradeRecord] = []
        self._epoch_trades: dict[int, list[TradeRecord]] = {}

    def record_trade(self, epoch: int, trader_id: str, energy_gained: int, tax_paid: int):
        """거래 기록"""
        record = TradeRecord(epoch, trader_id, energy_gained, tax_paid)
        self.trade_records.append(record)

        if epoch not in self._epoch_trades:
            self._epoch_trades[epoch] = []
        self._epoch_trades[epoch].append(record)

    def get_epoch_traders(self, epoch: int) -> list[str]:
        """해당 에폭에 거래한 에이전트 목록"""
        trades = self._epoch_trades.get(epoch, [])
        return list(set(r.trader_id for r in trades))

    def count_trades(self, epoch: int, trader_id: str = None) -> int:
        """거래 횟수"""
        trades = self._epoch_trades.get(epoch, [])
        if trader_id:
            return len([t for t in trades if t.trader_id == trader_id])
        return len(trades)

    def distribute_pool(
        self,
        epoch: int,
        market_agents: list["Agent"],
    ) -> dict[str, int]:
        """
        시장 풀 에너지 분배

        Returns: {agent_id: energy_received}
        """
        if not market_agents:
            return {}

        pool = self.spawn_per_epoch
        distribution = {}

        # 거래한 에이전트들
        traders = self.get_epoch_traders(epoch)
        trader_agents = [a for a in market_agents if a.id in traders]
        non_trader_agents = [a for a in market_agents if a.id not in traders]

        # 1. 거래하지 않은 에이전트들에게 최소 보상
        for agent in non_trader_agents:
            reward = min(self.min_presence_reward, pool)
            if reward > 0:
                distribution[agent.id] = reward
                pool -= reward

        # 2. 남은 풀을 거래 횟수에 비례하여 분배
        if trader_agents and pool > 0:
            total_trades = sum(self.count_trades(epoch, a.id) for a in trader_agents)

            if total_trades > 0:
                for agent in trader_agents:
                    trade_count = self.count_trades(epoch, agent.id)
                    share = int(pool * trade_count / total_trades)
                    distribution[agent.id] = distribution.get(agent.id, 0) + share
            else:
                # 거래가 없으면 균등 분배
                per_agent = pool // len(trader_agents)
                for agent in trader_agents:
                    distribution[agent.id] = distribution.get(agent.id, 0) + per_agent

        return distribution

    def get_total_tax_collected(self, epoch: int = None) -> int:
        """징수된 총 세금"""
        if epoch is not None:
            trades = self._epoch_trades.get(epoch, [])
        else:
            trades = self.trade_records
        return sum(t.tax_paid for t in trades)


class Treasury:
    """공공 자금"""

    def __init__(self, initial: int = 0, overflow_threshold: int = 100):
        self.balance = initial
        self.overflow_threshold = overflow_threshold
        self.overflow_to_pool = 0  # 시장 풀로 넘길 금액

    def deposit(self, amount: int) -> None:
        """입금"""
        self.balance += amount
        self._check_overflow()

    def withdraw(self, amount: int) -> bool:
        """출금. 성공 여부 반환"""
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False

    def _check_overflow(self) -> int:
        """overflow 체크 및 처리"""
        if self.balance > self.overflow_threshold:
            overflow = self.balance - self.overflow_threshold
            self.balance = self.overflow_threshold
            self.overflow_to_pool += overflow
            return overflow
        return 0

    def flush_overflow_to_pool(self) -> int:
        """시장 풀로 넘길 금액 반환 후 리셋"""
        amount = self.overflow_to_pool
        self.overflow_to_pool = 0
        return amount
