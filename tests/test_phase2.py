"""Phase 2 시스템 테스트"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.support import SupportTracker
from src.whisper import WhisperSystem
from src.market import MarketPool, Treasury
from src.influence import InfluenceSystem
from src.crisis import CrisisSystem
from src.architect import ArchitectSkills
from src.agent import Agent
from src.environment import Environment


class TestSupportTracker:
    """Support 추적 시스템 테스트"""

    def test_add_support(self):
        tracker = SupportTracker()
        tracker.add(1, "agent_a", "agent_b")
        assert len(tracker.records) == 1
        assert tracker.records[0].giver_id == "agent_a"
        assert tracker.records[0].receiver_id == "agent_b"

    def test_get_supporters(self):
        tracker = SupportTracker()
        tracker.add(1, "a", "b")
        tracker.add(2, "c", "b")
        supporters = tracker.get_supporters("b")
        assert supporters == ["a", "c"]

    def test_get_supported(self):
        tracker = SupportTracker()
        tracker.add(1, "a", "b")
        tracker.add(2, "a", "c")
        supported = tracker.get_supported("a")
        assert supported == ["b", "c"]

    def test_mutual_supporters(self):
        tracker = SupportTracker()
        tracker.add(1, "a", "b")
        tracker.add(2, "b", "a")
        mutual = tracker.get_mutual_supporters("a")
        assert "b" in mutual


class TestWhisperSystem:
    """Whisper 누출 시스템 테스트"""

    def test_leak_probability_base(self):
        ws = WhisperSystem(base_leak_prob=0.15, observer_bonus=0.35)
        agents = [
            Agent(id="sender", persona="jester"),
            Agent(id="receiver", persona="citizen"),
            Agent(id="bystander", persona="citizen"),
        ]
        prob = ws.get_leak_probability(agents, "sender", "receiver")
        assert prob == 0.15

    def test_leak_probability_with_observer(self):
        ws = WhisperSystem(base_leak_prob=0.15, observer_bonus=0.35)
        agents = [
            Agent(id="sender", persona="jester"),
            Agent(id="receiver", persona="citizen"),
            Agent(id="observer_01", persona="observer"),
        ]
        prob = ws.get_leak_probability(agents, "sender", "receiver")
        assert prob == 0.50

    def test_no_leak_when_alone(self):
        ws = WhisperSystem()
        agents = [
            Agent(id="sender", persona="jester"),
            Agent(id="receiver", persona="citizen"),
        ]
        prob = ws.get_leak_probability(agents, "sender", "receiver")
        assert prob == 0.0


class TestMarketPool:
    """시장 에너지 풀 테스트"""

    def test_record_trade(self):
        pool = MarketPool()
        pool.record_trade(1, "merchant_01", 4, 0)
        assert pool.count_trades(1) == 1
        assert pool.count_trades(1, "merchant_01") == 1

    def test_distribution(self):
        pool = MarketPool(spawn_per_epoch=25, min_presence_reward=2)
        pool.record_trade(1, "merchant_01", 4, 0)
        pool.record_trade(1, "merchant_01", 4, 0)

        agents = [
            Agent(id="merchant_01", persona="merchant", location="market"),
            Agent(id="citizen_01", persona="citizen", location="market"),
        ]

        dist = pool.distribute_pool(1, agents)
        assert "merchant_01" in dist
        assert "citizen_01" in dist
        assert dist["citizen_01"] == 2  # min_presence_reward


class TestTreasury:
    """Treasury 테스트"""

    def test_deposit_withdraw(self):
        treasury = Treasury(initial=50)
        treasury.deposit(30)
        assert treasury.balance == 80

        success = treasury.withdraw(20)
        assert success
        assert treasury.balance == 60

    def test_overflow(self):
        treasury = Treasury(initial=0, overflow_threshold=100)
        treasury.deposit(150)
        assert treasury.balance == 100
        assert treasury.overflow_to_pool == 50


class TestInfluenceSystem:
    """영향력 계급 시스템 테스트"""

    def test_get_tier(self):
        system = InfluenceSystem()
        assert system.get_tier_name(0) == "commoner"
        assert system.get_tier_name(5) == "notable"
        assert system.get_tier_name(10) == "elder"

    def test_titles(self):
        system = InfluenceSystem()
        assert system.get_title(0) == "평민"
        assert system.get_title(5) == "유력자"
        assert system.get_title(15) == "원로"

    def test_privileges(self):
        system = InfluenceSystem()
        assert not system.can_contest_architect(5)
        assert system.can_contest_architect(10)


class TestCrisisSystem:
    """Crisis 이벤트 시스템 테스트"""

    def test_no_crisis_before_threshold(self):
        crisis = CrisisSystem(start_after_epoch=30, probability=1.0)
        event = crisis.check_and_trigger(20)
        assert event is None

    def test_crisis_after_threshold(self):
        crisis = CrisisSystem(start_after_epoch=30, probability=1.0)
        event = crisis.check_and_trigger(35)
        assert event is not None
        assert crisis.is_crisis_active()

    def test_extra_decay(self):
        crisis = CrisisSystem(extra_decay=5)
        assert crisis.get_current_extra_decay() == 0
        crisis.check_and_trigger(35)
        if crisis.is_crisis_active():
            assert crisis.get_current_extra_decay() == 5


class TestArchitectSkills:
    """건축가 스킬 테스트"""

    def test_grant_subsidy(self):
        skills = ArchitectSkills()
        architect = Agent(id="architect_01", persona="architect", energy=100)
        target = Agent(id="citizen_01", persona="citizen", energy=20)
        treasury = Treasury(initial=50)

        result = skills.grant_subsidy(architect, target, 10, treasury)
        assert result.success
        assert treasury.balance == 40
        assert target.energy == 30

    def test_grant_subsidy_insufficient_treasury(self):
        skills = ArchitectSkills()
        architect = Agent(id="architect_01", persona="architect")
        target = Agent(id="citizen_01", persona="citizen", energy=20)
        treasury = Treasury(initial=5)

        result = skills.grant_subsidy(architect, target, 10, treasury)
        assert not result.success

    def test_adjust_tax(self):
        skills = ArchitectSkills()
        architect = Agent(id="architect_01", persona="architect", energy=100)
        env = Environment.from_config({
            "spaces": {"market": {"capacity": 12, "visibility": "public", "tax_rate": 0.1}}
        })

        result = skills.adjust_tax(architect, 0.2, env)
        assert result.success
        assert env.get_market_tax_rate() == 0.2

    def test_adjust_tax_out_of_range(self):
        skills = ArchitectSkills()
        architect = Agent(id="architect_01", persona="architect", energy=100)
        env = Environment.from_config({
            "spaces": {"market": {"capacity": 12, "visibility": "public", "tax_rate": 0.1}}
        })

        result = skills.adjust_tax(architect, 0.5, env)
        assert not result.success


class TestAgentPhase2:
    """Agent Phase 2 기능 테스트"""

    def test_max_energy_cap(self):
        agent = Agent(id="test", persona="citizen", energy=180, max_energy=200)
        agent.gain_energy(50)
        assert agent.energy == 200  # capped

    def test_suspicion(self):
        agent = Agent(id="test", persona="citizen")
        agent.add_suspicion("A와 B가 뭔가를 속삭였다.")
        assert len(agent.suspicions) == 1
        assert "속삭" in agent.get_recent_suspicions()[0]

    def test_energy_status(self):
        low_agent = Agent(id="test", persona="citizen", energy=15)
        assert "위험" in low_agent.get_energy_status()

        high_agent = Agent(id="test", persona="citizen", energy=150)
        assert "여유" in high_agent.get_energy_status()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
