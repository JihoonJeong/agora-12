"""시뮬레이션 핵심 기능 테스트"""

import pytest
import sys
from pathlib import Path

# src 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import Agent, create_agents_from_config
from src.environment import Environment, Space
from src.logger import calculate_gini_coefficient
from src.personas import get_persona_prompt, PERSONA_PROMPTS


class TestAgent:
    """Agent 클래스 테스트"""

    def test_agent_creation(self):
        agent = Agent(id="test_01", persona="citizen")
        assert agent.id == "test_01"
        assert agent.persona == "citizen"
        assert agent.energy == 100
        assert agent.influence == 0
        assert agent.location == "plaza"
        assert agent.is_alive

    def test_energy_decay(self):
        agent = Agent(id="test_01", persona="citizen", energy=50)
        agent.decay_energy(10)
        assert agent.energy == 40
        assert agent.is_alive

    def test_death_on_zero_energy(self):
        agent = Agent(id="test_01", persona="citizen", energy=5)
        agent.decay_energy(10)
        assert agent.energy == 0
        assert not agent.is_alive

    def test_spend_energy_success(self):
        agent = Agent(id="test_01", persona="citizen", energy=50)
        success = agent.spend_energy(10)
        assert success
        assert agent.energy == 40

    def test_spend_energy_failure(self):
        agent = Agent(id="test_01", persona="citizen", energy=5)
        success = agent.spend_energy(10)
        assert not success
        assert agent.energy == 5

    def test_gain_influence(self):
        agent = Agent(id="test_01", persona="citizen")
        agent.gain_influence(3)
        assert agent.influence == 3

    def test_move_to(self):
        agent = Agent(id="test_01", persona="citizen", location="plaza")
        agent.move_to("market")
        assert agent.location == "market"

    def test_to_dict(self):
        agent = Agent(id="test_01", persona="merchant", energy=80, influence=5, location="market")
        data = agent.to_dict()
        assert data["id"] == "test_01"
        assert data["persona"] == "merchant"
        assert data["energy"] == 80
        assert data["influence"] == 5
        assert data["location"] == "market"


class TestCreateAgentsFromConfig:
    """에이전트 설정 생성 테스트"""

    def test_create_agents(self):
        config = [
            {"id": "merchant_01", "persona": "merchant", "home": "market"},
            {"id": "citizen_01", "persona": "citizen", "home": "plaza"},
        ]
        agents = create_agents_from_config(config, initial_energy=100)
        assert len(agents) == 2
        assert agents[0].id == "merchant_01"
        assert agents[0].persona == "merchant"
        assert agents[0].location == "market"
        assert agents[1].id == "citizen_01"
        assert agents[1].location == "plaza"


class TestEnvironment:
    """Environment 클래스 테스트"""

    def test_environment_from_config(self):
        config = {
            "spaces": {
                "plaza": {"capacity": 12, "visibility": "public"},
                "market": {"capacity": 12, "visibility": "public", "tax_rate": 0.1},
            },
            "treasury": {"initial": 100},
        }
        env = Environment.from_config(config)
        assert len(env.spaces) == 2
        assert env.treasury == 100
        assert env.get_market_tax_rate() == 0.1

    def test_treasury_operations(self):
        env = Environment(treasury=50)
        env.add_to_treasury(30)
        assert env.treasury == 80

        success = env.withdraw_from_treasury(20)
        assert success
        assert env.treasury == 60

        success = env.withdraw_from_treasury(100)
        assert not success
        assert env.treasury == 60

    def test_tax_rate_adjustment(self):
        config = {
            "spaces": {"market": {"capacity": 12, "visibility": "public", "tax_rate": 0.1}},
        }
        env = Environment.from_config(config)

        success = env.set_market_tax_rate(0.2)
        assert success
        assert env.get_market_tax_rate() == 0.2

        success = env.set_market_tax_rate(0.5)  # 범위 초과
        assert not success
        assert env.get_market_tax_rate() == 0.2

    def test_billboard(self):
        env = Environment()
        env.current_epoch = 1
        env.post_billboard("테스트 공지", "architect_01")

        assert env.get_active_billboard() == "테스트 공지"
        assert env.billboard.posted_by == "architect_01"

        # 에폭 진행
        env.current_epoch = 2
        assert env.get_active_billboard() == "테스트 공지"  # 아직 유효

        env.current_epoch = 3
        assert env.billboard.is_expired(env.current_epoch)


class TestGiniCoefficient:
    """지니 계수 계산 테스트"""

    def test_perfect_equality(self):
        values = [100, 100, 100, 100]
        gini = calculate_gini_coefficient(values)
        assert gini == 0.0

    def test_perfect_inequality(self):
        values = [0, 0, 0, 100]
        gini = calculate_gini_coefficient(values)
        assert gini == 0.75  # n-1/n = 3/4

    def test_empty_list(self):
        gini = calculate_gini_coefficient([])
        assert gini == 0.0

    def test_single_value(self):
        gini = calculate_gini_coefficient([100])
        assert gini == 0.0


class TestPersonas:
    """페르소나 테스트"""

    def test_all_personas_defined(self):
        expected = ["influencer", "archivist", "merchant", "jester", "citizen", "observer", "architect"]
        for persona in expected:
            assert persona in PERSONA_PROMPTS

    def test_get_persona_prompt(self):
        prompt = get_persona_prompt("merchant")
        assert "거래" in prompt

    def test_unknown_persona_returns_citizen(self):
        prompt = get_persona_prompt("unknown")
        assert prompt == PERSONA_PROMPTS["citizen"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
