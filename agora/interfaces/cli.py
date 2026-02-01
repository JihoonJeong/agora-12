"""Player 모드 CLI 인터페이스"""

import sys
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.simulation import Simulation
    from ..core.agent import Agent


class PlayerCLI:
    """플레이어 CLI 인터페이스"""

    def __init__(self, simulation: "Simulation", player_agent_id: str):
        self.sim = simulation
        self.player_id = player_agent_id

        if player_agent_id not in self.sim.agents_by_id:
            raise ValueError(f"Agent '{player_agent_id}' not found")

        self.player = self.sim.agents_by_id[player_agent_id]

    def run(self) -> None:
        """Player 모드 시뮬레이션 실행"""
        print(f"\n{'='*50}")
        print(f"Agora-12 Player Mode")
        print(f"당신은: {self.player_id} ({self.player.persona})")
        print(f"{'='*50}\n")

        for epoch in range(1, self.sim.total_epochs + 1):
            self._run_player_epoch(epoch)

            if not self.sim.get_alive_agents():
                print(f"\n[!] 모든 에이전트 사망. 게임 종료.")
                break

            if not self.player.is_alive:
                print(f"\n[!] 당신이 사망했습니다. 게임 종료.")
                break

        self._print_game_over()

    def _run_player_epoch(self, epoch: int) -> None:
        """플레이어 턴 포함 에폭 실행"""
        self.sim.env.current_epoch = epoch
        self.sim.logger.reset_turn_counter()
        self.sim.transaction_count = 0
        self.sim.notable_events = []

        # Crisis 체크
        crisis_event = self.sim.crisis_system.check_and_trigger(epoch)
        if crisis_event:
            self.sim.notable_events.append(f"crisis: {crisis_event.name}")
            self.sim.history_engine.record_crisis(epoch, crisis_event.name)
            print(f"\n🚨 [위기 발생] {crisis_event.name}")

        # 에너지 감소
        base_decay = self.sim.calculate_decay(epoch)
        extra_decay = self.sim.crisis_system.get_current_extra_decay()
        total_decay = base_decay + extra_decay
        self.sim._apply_energy_decay(total_decay)

        # 사망 체크
        dead_agents = self.sim._check_deaths(epoch)
        if dead_agents:
            for dead_id in dead_agents:
                if dead_id != self.player_id:
                    print(f"💀 {dead_id}가 사망했습니다.")

        if not self.player.is_alive:
            return

        # 에이전트 순서 결정 (플레이어는 랜덤 위치)
        alive_agents = self.sim.get_alive_agents()
        import random
        random.shuffle(alive_agents)

        for agent in alive_agents:
            if agent.id == self.player_id:
                # 플레이어 턴
                self._player_turn(epoch)
            else:
                # AI 턴
                self.sim._execute_agent_turn(agent, epoch)

        # 시장 풀 분배
        self.sim._distribute_market_pool(epoch)

        # Treasury overflow
        overflow = self.sim.treasury.flush_overflow_to_pool()
        if overflow > 0:
            self.sim.market_pool.spawn_per_epoch += overflow

        # 게시판 만료
        self.sim.env.check_billboard_expiry()

        # 에폭 요약 로그
        self.sim._log_epoch_summary(epoch)

    def _player_turn(self, epoch: int) -> None:
        """플레이어 턴 처리"""
        self._display_status(epoch)

        while True:
            action = self._get_player_input()
            if action:
                success, info = self.sim._execute_action(self.player, action, epoch)
                if success:
                    self._display_action_result(action, info)
                    break
                else:
                    print(f"❌ 행동 실패: {info.get('error', 'unknown')}")
            else:
                print("잘못된 입력입니다. 다시 시도하세요.")

    def _display_status(self, epoch: int) -> None:
        """현재 상태 표시"""
        print(f"\n{'='*50}")
        print(f"Agora-12 | Epoch {epoch} | 당신: {self.player_id}")
        print(f"{'='*50}")

        # 상태
        energy_status = self.player.get_energy_status()
        tier = self.sim.influence_system.get_title(self.player.influence)
        print(f"\n[상태]")
        print(f"에너지: {self.player.energy}/200 {energy_status}")
        print(f"영향력: {self.player.influence} ({tier})")
        print(f"위치: {self.player.location}")

        # 최근 사건
        print(f"\n[최근 사건]")
        recent = self.sim.recent_logs[-5:] if self.sim.recent_logs else []
        if recent:
            for log in recent:
                self._print_log_entry(log)
        else:
            print("- 없음")

        # 게시판
        billboard = self.sim.env.get_active_billboard()
        if billboard:
            print(f"\n[광장 게시판]")
            print(f"📋 {billboard}")

        # 현재 위치 에이전트
        here = self.sim.get_agents_in_location(self.player.location)
        others = [a for a in here if a.id != self.player_id]
        print(f"\n[현재 위치: {self.player.location}]")
        if others:
            print(f"있는 에이전트: {', '.join([f'{a.id}({a.energy}E)' for a in others])}")
        else:
            print("아무도 없습니다.")

        # 가능한 행동
        print(f"\n[가능한 행동]")
        print("1. speak <메시지>     - 발언하기 (에너지 -2)")
        if self.player.location == "market":
            print("2. trade              - 거래하기 (에너지 -2, +4 세전)")
        print("3. support <대상>     - 지지하기 (에너지 -1)")
        if self.player.location.startswith("alley"):
            print("4. whisper <대상> <메시지> - 귓속말 (에너지 -1)")
        print("5. move <장소>        - 이동 (plaza/market/alley_a/alley_b/alley_c)")
        print("6. idle               - 대기")
        print()

    def _print_log_entry(self, log: dict) -> None:
        """로그 항목 출력"""
        action_type = log.get("action_type", "")
        agent_id = log.get("agent_id", "")
        content = log.get("content", "")
        target = log.get("target", "")

        if action_type == "speak":
            print(f"- {agent_id}: \"{content}\"")
        elif action_type == "trade":
            print(f"- {agent_id}가 거래했습니다.")
        elif action_type == "support":
            print(f"- {agent_id}가 {target}를 지지했습니다.")
        elif action_type == "whisper":
            if agent_id == self.player_id or target == self.player_id:
                print(f"- {agent_id}가 {target}에게 귓속말을 보냈습니다.")
        elif action_type == "death":
            print(f"- 💀 {agent_id}가 사망했습니다.")
        elif action_type == "move":
            print(f"- {agent_id}가 {target}로 이동했습니다.")

    def _get_player_input(self) -> Optional[dict]:
        """플레이어 입력 처리"""
        try:
            raw = input("> 입력: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n게임 종료.")
            sys.exit(0)

        if not raw:
            return None

        parts = raw.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd == "speak":
            content = parts[1] if len(parts) > 1 else f"[{self.player_id}] ..."
            return {"type": "speak", "content": content}

        elif cmd == "trade":
            return {"type": "trade"}

        elif cmd == "support":
            if len(parts) < 2:
                print("사용법: support <대상 에이전트 ID>")
                return None
            return {"type": "support", "target": parts[1]}

        elif cmd == "whisper":
            if len(parts) < 3:
                print("사용법: whisper <대상> <메시지>")
                return None
            return {"type": "whisper", "target": parts[1], "content": parts[2]}

        elif cmd == "move":
            if len(parts) < 2:
                print("사용법: move <장소>")
                return None
            return {"type": "move", "target": parts[1]}

        elif cmd == "idle":
            return {"type": "idle"}

        else:
            print(f"알 수 없는 명령: {cmd}")
            return None

    def _display_action_result(self, action: dict, info: dict) -> None:
        """행동 결과 표시"""
        action_type = action["type"]

        if action_type == "speak":
            print(f"✅ 발언했습니다. (에너지 -2)")
        elif action_type == "trade":
            print(f"✅ 거래 완료. 순수익: {info.get('net_reward', 0)} (세금: {info.get('tax', 0)})")
        elif action_type == "support":
            print(f"✅ {action.get('target')}를 지지했습니다. (에너지 -{info.get('giver_cost', 1)})")
        elif action_type == "whisper":
            leaked = "⚠️ 누출됨!" if info.get("leaked") else ""
            print(f"✅ 귓속말을 보냈습니다. {leaked}")
        elif action_type == "move":
            print(f"✅ {action.get('target')}로 이동했습니다.")
        elif action_type == "idle":
            print(f"✅ 대기했습니다.")

        print("\n--- 다른 에이전트들의 턴 진행 중... ---")

    def _print_game_over(self) -> None:
        """게임 종료 출력"""
        print(f"\n{'='*50}")
        print("GAME OVER")
        print(f"{'='*50}")

        alive = self.sim.get_alive_agents()
        print(f"\n생존자: {len(alive)}/{len(self.sim.agents)}")

        if self.player.is_alive:
            print(f"\n🎉 당신은 생존했습니다!")
            print(f"최종 에너지: {self.player.energy}")
            print(f"최종 영향력: {self.player.influence}")
        else:
            print(f"\n💀 당신은 사망했습니다.")

        print(f"\n[역사적 요약]")
        print(self.sim.history_engine.get_summary(detailed=True))
