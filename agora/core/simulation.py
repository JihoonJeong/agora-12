"""메인 시뮬레이션 루프 (Phase 3 - LLM 통합)"""

import random
import math
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .agent import Agent, create_agents_from_config
from .environment import Environment
from .logger import SimulationLogger, calculate_gini_coefficient
from .support import SupportTracker
from .whisper import WhisperSystem
from .market import MarketPool, Treasury
from .influence import InfluenceSystem, ELDER_SUPPORT_MULTIPLIER
from .crisis import CrisisSystem, CRISIS_SUPPORT_BONUS
from .architect import ArchitectSkills
from .actions import get_speak_type, get_available_actions
from .context import build_context
from .history import HistoryEngine

from ..adapters import create_adapter, BaseLLMAdapter, LLMResponse


class Simulation:
    """Agora-12 시뮬레이션 메인 클래스 (Phase 3)"""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.env = Environment.from_config(self.config)

        # 언어 설정 (기본값: ko)
        self.language = self.config.get("language", "ko")

        # 에이전트 초기화
        energy_config = self.config.get("resources", {}).get("energy", {})
        initial_energy = energy_config.get("initial", 100)
        max_energy = energy_config.get("max_cap", 200)

        self.agents = create_agents_from_config(
            self.config.get("agents", []),
            initial_energy=initial_energy,
            max_energy=max_energy,
            language=self.language,
        )
        self.agents_by_id = {agent.id: agent for agent in self.agents}

        # LLM 어댑터 초기화
        self.adapters: dict[str, BaseLLMAdapter] = {}
        self._init_adapters()

        # 로거 초기화 - 실험별 고유 디렉토리 생성
        model_name = self.config.get("default_model", "unknown").replace(":", "-").replace("/", "-")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_id = f"{model_name}_{self.language}_{timestamp}"
        self.run_dir = Path("logs") / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.logger = SimulationLogger(
            log_path=str(self.run_dir / "simulation_log.jsonl"),
            summary_path=str(self.run_dir / "epoch_summary.jsonl"),
        )

        # Phase 2 시스템 초기화
        self.support_tracker = SupportTracker()

        whisper_config = self.config.get("actions", {}).get("whisper", {})
        self.whisper_system = WhisperSystem(
            base_leak_prob=whisper_config.get("base_leak_probability", 0.15),
            observer_bonus=whisper_config.get("observer_bonus", 0.35),
        )

        market_config = self.config.get("market", {}).get("pool", {})
        self.market_pool = MarketPool(
            spawn_per_epoch=market_config.get("spawn_per_epoch", 25),
            min_presence_reward=market_config.get("min_presence_reward", 2),
        )

        treasury_config = self.config.get("treasury", {})
        self.treasury = Treasury(
            initial=treasury_config.get("initial", 0),
            overflow_threshold=treasury_config.get("overflow_threshold", 100),
        )

        influence_config = self.config.get("influence_tiers", {})
        self.influence_system = InfluenceSystem.from_config(influence_config) if influence_config else InfluenceSystem()

        crisis_config = self.config.get("crisis", {})
        self.crisis_system = CrisisSystem.from_config(crisis_config) if crisis_config else CrisisSystem()

        architect_config = self.config.get("architect_skills", {})
        self.architect_skills = ArchitectSkills(architect_config)

        # Phase 3: 역사 엔진
        self.history_engine = HistoryEngine()

        # 설정값 캐싱
        decay_config = energy_config.get("decay", {})
        self.base_decay = decay_config.get("base", 5)
        self.decay_acceleration = decay_config.get("acceleration", 0.5)
        self.total_epochs = self.config.get("simulation", {}).get("total_epochs", 100)

        # 행동 설정
        self.action_config = self.config.get("actions", {})

        # 통계
        self.transaction_count = 0
        self.notable_events: list[str] = []
        self.recent_logs: list[dict] = []  # 최근 로그 (컨텍스트용)

    def _load_config(self, config_path: str) -> dict:
        """설정 파일 로드"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _init_adapters(self) -> None:
        """에이전트별 LLM 어댑터 초기화"""
        agents_config = self.config.get("agents", [])
        default_adapter = self.config.get("default_adapter", "mock")
        default_model = self.config.get("default_model", "mock")

        # 어댑터별 글로벌 설정
        ollama_config = self.config.get("ollama", {})
        anthropic_config = self.config.get("anthropic", {})
        google_config = self.config.get("google", {})

        for agent_config in agents_config:
            agent_id = agent_config["id"]
            adapter_type = agent_config.get("adapter", default_adapter)
            model = agent_config.get("model", default_model)

            # 어댑터별 추가 설정
            extra_kwargs = {}
            if adapter_type == "ollama":
                extra_kwargs = {
                    "base_url": ollama_config.get("base_url", "http://localhost:11434"),
                    "timeout": ollama_config.get("timeout", 60),
                }
            elif adapter_type == "anthropic":
                if anthropic_config.get("api_key"):
                    extra_kwargs["api_key"] = anthropic_config["api_key"]
                if anthropic_config.get("max_tokens"):
                    extra_kwargs["max_tokens"] = anthropic_config["max_tokens"]
            elif adapter_type == "google":
                if google_config.get("api_key"):
                    extra_kwargs["api_key"] = google_config["api_key"]

            self.adapters[agent_id] = create_adapter(
                adapter_type,
                model=model,
                persona=agent_config.get("persona", "citizen"),
                agent_id=agent_id,
                **extra_kwargs,
            )

    def get_alive_agents(self) -> list[Agent]:
        """생존 에이전트 목록"""
        return [agent for agent in self.agents if agent.is_alive]

    def get_agents_in_location(self, location: str) -> list[Agent]:
        """특정 위치의 생존 에이전트 목록"""
        return [agent for agent in self.get_alive_agents() if agent.location == location]

    def calculate_decay(self, epoch: int) -> int:
        """에폭별 decay 계산"""
        acceleration = math.floor(epoch / 10) * self.decay_acceleration
        return int(self.base_decay + acceleration)

    def run(self, callback=None) -> None:
        """시뮬레이션 실행"""
        print(f"=== Agora-12 시뮬레이션 시작 (Phase 3) ===")
        print(f"총 에폭: {self.total_epochs}")
        print(f"에이전트 수: {len(self.agents)}")
        print()

        for epoch in range(1, self.total_epochs + 1):
            self.run_epoch(epoch)

            if callback:
                callback(epoch, self)

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

        # 0. Crisis 이벤트 체크
        crisis_event = self.crisis_system.check_and_trigger(epoch)
        if crisis_event:
            self.notable_events.append(f"crisis: {crisis_event.name}")
            self.history_engine.record_crisis(epoch, crisis_event.name)
            crisis_billboard = self.crisis_system.get_billboard_message()
            if crisis_billboard:
                self.env.post_billboard(crisis_billboard, "SYSTEM")

        # 1. 에너지 감소
        base_decay = self.calculate_decay(epoch)
        extra_decay = self.crisis_system.get_current_extra_decay()
        total_decay = base_decay + extra_decay
        self._apply_energy_decay(total_decay)

        # 2. 사망 체크
        dead_agents = self._check_deaths(epoch)
        if dead_agents:
            self.notable_events.append(f"deaths: {dead_agents}")

        # 3. 에이전트 행동 (랜덤 순서)
        alive_agents = self.get_alive_agents()
        random.shuffle(alive_agents)

        for agent in alive_agents:
            self._execute_agent_turn(agent, epoch)

        # 4. 시장 에너지 풀 분배
        self._distribute_market_pool(epoch)

        # 5. Treasury overflow 처리
        overflow = self.treasury.flush_overflow_to_pool()
        if overflow > 0:
            self.market_pool.spawn_per_epoch += overflow
            self.notable_events.append(f"treasury_overflow: {overflow}")

        # 6. 게시판 만료 체크
        expired = self.env.check_billboard_expiry()
        if expired:
            self.notable_events.append("billboard_expired")

        # 7. 에폭 종료 로그 기록
        self._log_epoch_summary(epoch)

        # 콘솔 출력
        alive_count = len(self.get_alive_agents())
        total_energy = sum(a.energy for a in self.get_alive_agents())
        crisis_str = f" [CRISIS: {crisis_event.name}]" if crisis_event else ""
        print(f"Epoch {epoch:3d} | 생존: {alive_count:2d} | 에너지: {total_energy:5d} | Treasury: {self.treasury.balance:4d}{crisis_str}")

    def _apply_energy_decay(self, amount: int) -> None:
        """모든 에이전트 에너지 감소"""
        for agent in self.get_alive_agents():
            agent.decay_energy(amount)

    def _check_deaths(self, epoch: int) -> list[str]:
        """사망한 에이전트 확인 및 처리"""
        dead = []
        for agent in self.agents:
            if not agent.alive:  # Check alive, not is_alive (which includes energy check)
                continue
            if agent.energy <= 0:
                agent.alive = False
                dead.append(agent.id)
                self.history_engine.record_death(epoch, agent.id)
                self.logger.log_action(
                    epoch=epoch,
                    agent_id=agent.id,
                    persona=agent.persona,
                    location=agent.location,
                    action_type="death",
                    target=None,
                    content="에너지 고갈로 사망",
                    resources_before={"energy": 0, "influence": agent.influence},
                    resources_after={"energy": 0, "influence": agent.influence},
                    success=True,
                    extra={"thought": "..."},
                )
        return dead

    def _distribute_market_pool(self, epoch: int) -> None:
        """시장 에너지 풀 분배"""
        market_agents = self.get_agents_in_location("market")
        if not market_agents:
            return

        distribution = self.market_pool.distribute_pool(epoch, market_agents)

        for agent_id, amount in distribution.items():
            agent = self.agents_by_id.get(agent_id)
            if agent and agent.is_alive:
                agent.gain_energy(amount)

    def _execute_agent_turn(self, agent: Agent, epoch: int) -> None:
        """단일 에이전트 턴 실행"""
        resources_before = agent.get_resources()

        # LLM을 통한 행동 결정
        adapter = self.adapters.get(agent.id)
        if adapter:
            gini = calculate_gini_coefficient([a.energy for a in self.get_alive_agents()])
            context = build_context(
                agent=agent,
                env=self.env,
                support_tracker=self.support_tracker,
                history_engine=self.history_engine,
                influence_system=self.influence_system,
                crisis_system=self.crisis_system,
                alive_agents=self.get_alive_agents(),
                recent_logs=self.recent_logs,
                gini_coefficient=gini,
                language=self.language,
            )

            response = adapter.generate(context)
            action = response.to_action_dict()
            thought = response.thought
        else:
            action = {"type": "idle"}
            thought = "어댑터 없음"

        # 행동 실행
        success, extra_info = self._execute_action(agent, action, epoch)

        resources_after = agent.get_resources()

        # 로깅
        log_entry = {
            "epoch": epoch,
            "agent_id": agent.id,
            "persona": agent.persona,
            "location": agent.location,
            "action_type": action["type"],
            "target": action.get("target"),
            "content": action.get("content"),
            "resources_before": resources_before,
            "resources_after": resources_after,
            "success": success,
        }
        self.recent_logs.append(log_entry)
        if len(self.recent_logs) > 50:
            self.recent_logs = self.recent_logs[-50:]

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
            extra={"thought": thought, **extra_info},
        )

    def _execute_action(self, agent: Agent, action: dict, epoch: int) -> tuple[bool, dict]:
        """행동 실행"""
        action_type = action["type"]

        if action_type == "speak":
            return self._action_speak(agent, action.get("content", ""), epoch)
        elif action_type == "move":
            return self._action_move(agent, action.get("target", agent.location))
        elif action_type == "trade":
            return self._action_trade(agent, epoch)
        elif action_type == "support":
            return self._action_support(agent, action.get("target"), epoch)
        elif action_type == "whisper":
            return self._action_whisper(agent, action.get("target"), action.get("content", ""), epoch)
        elif action_type == "architect_skill":
            return self._action_architect_skill(agent, action, epoch)
        elif action_type == "idle":
            return True, {}

        return False, {}

    def _action_speak(self, agent: Agent, content: str, epoch: int) -> tuple[bool, dict]:
        """발언 행동"""
        speak_type = get_speak_type(agent.location)
        config = self.action_config.get(speak_type, {})

        cost = config.get("cost", 2)
        direct_reward = config.get("direct_reward", 0)

        if not agent.spend_energy(cost):
            return False, {}

        if direct_reward > 0:
            agent.gain_energy(direct_reward)

        return True, {"speak_type": speak_type}

    def _action_move(self, agent: Agent, target_location: str) -> tuple[bool, dict]:
        """이동 행동"""
        if target_location in self.env.spaces:
            old_location = agent.location
            agent.move_to(target_location)
            return True, {"from": old_location, "to": target_location}
        return False, {}

    def _action_trade(self, agent: Agent, epoch: int) -> tuple[bool, dict]:
        """거래 행동"""
        if agent.location != "market":
            return False, {"error": "not_in_market"}

        config = self.action_config.get("trade", {})
        cost = config.get("cost", 2)
        reward = config.get("direct_reward", 4)

        if not agent.spend_energy(cost):
            return False, {"error": "insufficient_energy"}

        tax_rate = self.env.get_market_tax_rate()
        if tax_rate == 0:
            tax = 0
        else:
            tax = max(1, round(reward * tax_rate))
        net_reward = reward - tax

        agent.gain_energy(net_reward)
        self.treasury.deposit(tax)

        self.market_pool.record_trade(epoch, agent.id, net_reward, tax)
        self.transaction_count += 1

        return True, {"gross_reward": reward, "tax": tax, "net_reward": net_reward}

    def _action_support(self, agent: Agent, target_id: Optional[str], epoch: int) -> tuple[bool, dict]:
        """지지 행동"""
        if not target_id or target_id not in self.agents_by_id:
            return False, {"error": "invalid_target"}

        target = self.agents_by_id[target_id]
        if not target.is_alive:
            return False, {"error": "target_dead"}

        if target.location != agent.location:
            return False, {"error": "different_location"}

        config = self.action_config.get("support", {})
        cost = config.get("cost", 1)
        base_energy = config.get("receiver_energy", 2)
        base_influence = config.get("receiver_influence", 1)

        if not agent.spend_energy(cost):
            return False, {"error": "insufficient_energy"}

        receiver_energy = base_energy
        receiver_influence = base_influence
        bonuses = []

        if self.influence_system.get_tier_name(agent.influence) == "elder":
            receiver_energy = int(base_energy * ELDER_SUPPORT_MULTIPLIER)
            bonuses.append("elder_bonus")
            if agent.location == "plaza":
                self.notable_events.append(f"elder_support: {agent.id}->{target.id}")

        if self.crisis_system.is_crisis_active():
            receiver_energy += CRISIS_SUPPORT_BONUS["energy"]
            receiver_influence += CRISIS_SUPPORT_BONUS["influence"]
            bonuses.append("crisis_bonus")

        target.gain_energy(receiver_energy)
        target.gain_influence(receiver_influence)

        self.support_tracker.add(epoch, agent.id, target.id)

        # 상호 지지 체크 및 기록
        if agent.id in self.support_tracker.get_supporters(target.id):
            self.history_engine.record_auto(
                epoch, "mutual_support",
                agent_a=agent.id, agent_b=target.id
            )

        return True, {
            "giver_cost": cost,
            "receiver_energy": receiver_energy,
            "receiver_influence": receiver_influence,
            "bonuses": bonuses,
        }

    def _action_whisper(self, agent: Agent, target_id: Optional[str], content: str, epoch: int) -> tuple[bool, dict]:
        """귓속말 행동"""
        if not agent.location.startswith("alley"):
            return False, {"error": "not_in_alley"}

        if not target_id or target_id not in self.agents_by_id:
            return False, {"error": "invalid_target"}

        target = self.agents_by_id[target_id]
        if not target.is_alive or target.location != agent.location:
            return False, {"error": "target_not_available"}

        config = self.action_config.get("whisper", {})
        cost = config.get("cost", 1)

        if not agent.spend_energy(cost):
            return False, {"error": "insufficient_energy"}

        agents_here = self.get_agents_in_location(agent.location)
        leaked, observers = self.whisper_system.process_whisper(
            agent, target, content, agent.location, agents_here, epoch
        )

        if leaked:
            self.notable_events.append(f"whisper_leaked: {agent.id}->{target_id}")
            self.history_engine.record_auto(
                epoch, "whisper_leaked",
                sender=agent.id, receiver=target_id
            )

        return True, {"leaked": leaked, "observers": observers}

    def _action_architect_skill(self, agent: Agent, action: dict, epoch: int) -> tuple[bool, dict]:
        """건축가 스킬 실행"""
        skill = action.get("skill")

        if skill == "grant_subsidy":
            target_id = action.get("target")
            amount = action.get("amount", 0)

            if not target_id or target_id not in self.agents_by_id:
                return False, {"error": "invalid_target"}

            target = self.agents_by_id[target_id]
            result = self.architect_skills.grant_subsidy(agent, target, amount, self.treasury)

            if result.success:
                self.notable_events.append(f"subsidy: {target_id} +{amount}")
                self.history_engine.record_auto(
                    epoch, "subsidy_granted",
                    agent_id=target_id, amount=amount
                )

            return result.success, {"skill_result": result.message}

        elif skill == "adjust_tax":
            new_rate = action.get("new_rate", 0.1)
            old_rate = self.env.get_market_tax_rate()
            result = self.architect_skills.adjust_tax(agent, new_rate, self.env)

            if result.success:
                self.notable_events.append(f"tax_adjusted: {new_rate*100:.0f}%")
                self.history_engine.record_tax_change(epoch, old_rate, new_rate)

            return result.success, {"skill_result": result.message}

        elif skill == "build_billboard":
            message = action.get("message", "")
            result = self.architect_skills.build_billboard(agent, message, self.env)
            return result.success, {"skill_result": result.message}

        return False, {"error": "unknown_skill"}

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
            treasury=self.treasury.balance,
            notable_events=self.notable_events,
        )

    def _print_final_summary(self) -> None:
        """최종 결과 출력"""
        alive = self.get_alive_agents()
        print(f"\n--- 최종 결과 ---")
        print(f"생존자: {len(alive)}/{len(self.agents)}")
        print(f"Treasury: {self.treasury.balance}")

        if alive:
            print(f"\n생존 에이전트:")
            for agent in sorted(alive, key=lambda a: a.energy, reverse=True):
                tier = self.influence_system.get_title(agent.influence)
                adapter_name = self.adapters[agent.id].name if agent.id in self.adapters else "unknown"
                print(f"  {agent.id}: E={agent.energy}, I={agent.influence} ({tier}), @{agent.location} [{adapter_name}]")

        print(f"\n역사적 요약:")
        print(self.history_engine.get_summary(detailed=True))


def main():
    """CLI 진입점"""
    sim = Simulation()
    sim.run()


if __name__ == "__main__":
    main()
