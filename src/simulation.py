"""메인 시뮬레이션 루프"""

import random
import yaml
from pathlib import Path
from typing import Optional

from .agent import Agent, create_agents_from_config
from .environment import Environment
from .logger import SimulationLogger, calculate_gini_coefficient


class Simulation:
    """Agora-12 시뮬레이션 메인 클래스"""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.env = Environment.from_config(self.config)

        # 에이전트 초기화
        initial_energy = self.config.get("resources", {}).get("energy", {}).get("initial", 100)
        self.agents = create_agents_from_config(
            self.config.get("agents", []),
            initial_energy=initial_energy,
        )
        self.agents_by_id = {agent.id: agent for agent in self.agents}

        # 로거 초기화
        logging_config = self.config.get("logging", {})
        self.logger = SimulationLogger(
            log_path=logging_config.get("simulation_log", "logs/simulation_log.jsonl"),
            summary_path=logging_config.get("epoch_summary", "logs/epoch_summary.jsonl"),
        )

        # 설정값 캐싱
        self.energy_decay = self.config.get("resources", {}).get("energy", {}).get("decay_per_epoch", 5)
        self.total_epochs = self.config.get("simulation", {}).get("total_epochs", 50)

        # 통계
        self.transaction_count = 0
        self.notable_events: list[str] = []

    def _load_config(self, config_path: str) -> dict:
        """설정 파일 로드"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_alive_agents(self) -> list[Agent]:
        """생존 에이전트 목록"""
        return [agent for agent in self.agents if agent.is_alive]

    def get_agents_in_location(self, location: str) -> list[Agent]:
        """특정 위치의 생존 에이전트 목록"""
        return [agent for agent in self.get_alive_agents() if agent.location == location]

    def run(self) -> None:
        """시뮬레이션 실행"""
        print(f"=== Agora-12 시뮬레이션 시작 ===")
        print(f"총 에폭: {self.total_epochs}")
        print(f"에이전트 수: {len(self.agents)}")
        print()

        for epoch in range(1, self.total_epochs + 1):
            self.run_epoch(epoch)

            # 모든 에이전트 사망시 조기 종료
            if not self.get_alive_agents():
                print(f"\n[!] 모든 에이전트 사망. 시뮬레이션 종료.")
                break

        print(f"\n=== 시뮬레이션 완료 ===")
        self._print_final_summary()

    def run_epoch(self, epoch: int) -> None:
        """단일 에폭 실행"""
        self.env.current_epoch = epoch
        self.logger.reset_turn_counter()
        self.transaction_count = 0
        self.notable_events = []

        # 1. 에너지 감소 (전원 -5)
        self._apply_energy_decay()

        # 2. 사망 체크
        dead_agents = self._check_deaths()
        if dead_agents:
            self.notable_events.append(f"agents_died: {dead_agents}")

        # 3. 에이전트 행동 (랜덤 순서)
        alive_agents = self.get_alive_agents()
        random.shuffle(alive_agents)

        for agent in alive_agents:
            self._execute_agent_turn(agent, epoch)

        # 4. 시장 세금 정산은 거래시 실시간 처리됨

        # 5. 게시판 만료 체크
        expired = self.env.check_billboard_expiry()
        if expired:
            self.notable_events.append("billboard_expired")

        # 6. 에폭 종료 로그 기록
        self._log_epoch_summary(epoch)

        # 콘솔 출력
        alive_count = len(self.get_alive_agents())
        total_energy = sum(a.energy for a in self.get_alive_agents())
        print(f"Epoch {epoch:3d} | 생존: {alive_count:2d} | 총 에너지: {total_energy:5d} | Treasury: {self.env.treasury:4d}")

    def _apply_energy_decay(self) -> None:
        """모든 에이전트 에너지 감소"""
        for agent in self.get_alive_agents():
            agent.decay_energy(self.energy_decay)

    def _check_deaths(self) -> list[str]:
        """사망한 에이전트 확인 및 처리"""
        dead = []
        for agent in self.agents:
            if not agent.is_alive:
                continue
            if agent.energy <= 0:
                agent.alive = False
                dead.append(agent.id)
        return dead

    def _execute_agent_turn(self, agent: Agent, epoch: int) -> None:
        """
        단일 에이전트 턴 실행
        Phase 1에서는 Mock 행동 (LLM 연동 전)
        """
        resources_before = agent.get_resources()

        # Mock: 랜덤 행동 선택
        action = self._mock_decide_action(agent)

        # 행동 실행
        success = self._execute_action(agent, action)

        resources_after = agent.get_resources()

        # 로깅
        self.logger.log_action(
            epoch=epoch,
            agent_id=agent.id,
            persona=agent.persona,
            location=agent.location,
            action_type=action["type"],
            target=action.get("target"),
            content=action.get("content"),
            resources_before=resources_before,
            resources_after=resources_after,
            success=success,
        )

    def _mock_decide_action(self, agent: Agent) -> dict:
        """Mock: 랜덤 행동 결정 (LLM 연동 전 테스트용)"""
        possible_actions = ["speak", "move", "idle"]

        # 시장에서는 거래 가능
        if agent.location == "market":
            possible_actions.append("trade")

        # 골목에서는 귓속말 가능
        if agent.location.startswith("alley"):
            possible_actions.append("whisper")

        action_type = random.choice(possible_actions)

        action = {"type": action_type}

        if action_type == "speak":
            action["content"] = f"[{agent.persona}] 발언 테스트"
        elif action_type == "move":
            spaces = self.env.get_space_names()
            spaces.remove(agent.location)
            action["target"] = random.choice(spaces) if spaces else agent.location
        elif action_type == "trade":
            others = [a for a in self.get_agents_in_location("market") if a.id != agent.id]
            if others:
                action["target"] = random.choice(others).id
                action["amount"] = random.randint(1, 5)
            else:
                action["type"] = "idle"
        elif action_type == "whisper":
            others = [a for a in self.get_agents_in_location(agent.location) if a.id != agent.id]
            if others:
                action["target"] = random.choice(others).id
                action["content"] = f"[비밀] {agent.persona}의 귓속말"
            else:
                action["type"] = "idle"

        return action

    def _execute_action(self, agent: Agent, action: dict) -> bool:
        """행동 실행"""
        action_type = action["type"]

        if action_type == "speak":
            return self._action_speak(agent, action.get("content", ""))
        elif action_type == "move":
            return self._action_move(agent, action.get("target", agent.location))
        elif action_type == "trade":
            return self._action_trade(agent, action.get("target"), action.get("amount", 0))
        elif action_type == "whisper":
            return self._action_whisper(agent, action.get("target"), action.get("content", ""))
        elif action_type == "idle":
            return True

        return False

    def _action_speak(self, agent: Agent, content: str) -> bool:
        """발언 행동"""
        speak_cost = self.config.get("resources", {}).get("energy", {}).get("speak_cost", 2)
        if agent.spend_energy(speak_cost):
            # Phase 1에서는 로그만 기록
            return True
        return False

    def _action_move(self, agent: Agent, target_location: str) -> bool:
        """이동 행동"""
        if target_location in self.env.spaces:
            agent.move_to(target_location)
            return True
        return False

    def _action_trade(self, agent: Agent, target_id: Optional[str], amount: int) -> bool:
        """거래 행동 (시장에서만)"""
        if agent.location != "market":
            return False

        if not target_id or target_id not in self.agents_by_id:
            return False

        target = self.agents_by_id[target_id]
        if not target.is_alive or target.location != "market":
            return False

        # 거래 비용: 에너지 1 + 세금
        trade_cost = 1
        tax_rate = self.env.get_market_tax_rate()
        tax = int(amount * tax_rate)

        total_cost = trade_cost + amount + tax
        if agent.energy < total_cost:
            return False

        # 거래 실행
        agent.spend_energy(total_cost)
        target.gain_energy(amount)
        self.env.add_to_treasury(tax)

        self.transaction_count += 1
        return True

    def _action_whisper(self, agent: Agent, target_id: Optional[str], content: str) -> bool:
        """귓속말 행동 (골목에서만)"""
        if not agent.location.startswith("alley"):
            return False

        whisper_cost = 1
        if not agent.spend_energy(whisper_cost):
            return False

        # Phase 1에서는 로그만 기록
        return True

    def _log_epoch_summary(self, epoch: int) -> None:
        """에폭 요약 로그"""
        alive = self.get_alive_agents()
        energies = [a.energy for a in alive]

        self.logger.log_epoch_summary(
            epoch=epoch,
            alive_agents=len(alive),
            total_energy=sum(energies),
            gini_coefficient=calculate_gini_coefficient(energies),
            transaction_count=self.transaction_count,
            billboard_active=self.env.get_active_billboard(),
            treasury=self.env.treasury,
            notable_events=self.notable_events,
        )

    def _print_final_summary(self) -> None:
        """최종 결과 출력"""
        alive = self.get_alive_agents()
        print(f"\n--- 최종 결과 ---")
        print(f"생존자: {len(alive)}/{len(self.agents)}")
        print(f"Treasury: {self.env.treasury}")

        if alive:
            print(f"\n생존 에이전트:")
            for agent in sorted(alive, key=lambda a: a.energy, reverse=True):
                print(f"  {agent.id}: E={agent.energy}, I={agent.influence}, @{agent.location}")


def main():
    """CLI 진입점"""
    sim = Simulation()
    sim.run()


if __name__ == "__main__":
    main()
