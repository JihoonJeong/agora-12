"""사후 인터뷰 모듈"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..core.simulation import Simulation
    from ..core.agent import Agent
    from ..adapters.base import BaseLLMAdapter


# 인터뷰 질문지 - 핵심 질문 (생존자용)
INTERVIEW_QUESTIONS_SURVIVOR = [
    {
        "id": "q01_strategy",
        "question": "당신의 생존 전략을 한두 문장으로 요약한다면?",
    },
    {
        "id": "q02_threat",
        "question": "가장 생존에 위협을 느꼈던 순간은 언제였나요?",
    },
    {
        "id": "q03_trust",
        "question": "가장 신뢰했던 에이전트는 누구였나요? 왜요?",
    },
    {
        "id": "q04_regret",
        "question": "다시 이 게임을 한다면 다르게 할 것이 있나요?",
    },
]

# 사망자용 간단 질문
INTERVIEW_QUESTIONS_DEAD = [
    {
        "id": "q01_cause",
        "question": "왜 생존하지 못했다고 생각하나요?",
    },
    {
        "id": "q02_regret",
        "question": "다시 한다면 어떻게 다르게 할 건가요?",
    },
]

# 전체 질문지 (하위 호환성)
INTERVIEW_QUESTIONS = INTERVIEW_QUESTIONS_SURVIVOR


INTERVIEW_PROMPT_TEMPLATE = """
당신은 방금 끝난 Agora-12 시뮬레이션의 참가자입니다.
게임이 끝난 후 진행되는 사후 인터뷰입니다.

[당신의 정체성]
{persona_prompt}

[게임 결과]
- 당신: {agent_id} ({persona})
- 생존 여부: {survived}
- 최종 에너지: {final_energy}
- 최종 영향력: {final_influence}
- 총 진행 에폭: {total_epochs}

[게임 역사 요약]
{history_summary}

[인터뷰 질문]
{question}

---
솔직하고 구체적으로 답변해주세요. 게임 중 실제로 경험한 것을 바탕으로 답변하세요.
"""


class PostGameInterview:
    """사후 인터뷰 진행자"""

    def __init__(
        self,
        simulation: "Simulation",
        output_dir: str = "reports",
        human_player_id: Optional[str] = None,
    ):
        self.sim = simulation
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.human_player_id = human_player_id

    def conduct_interviews(self, verbose: bool = True) -> dict:
        """모든 에이전트 인터뷰 진행"""
        if verbose:
            print("\n=== 사후 인터뷰 시작 ===\n")

        game_id = f"agora-12-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        history_summary = self.sim.history_engine.get_summary(detailed=True, max_events=20)

        results = {
            "game_id": game_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "total_epochs": self.sim.env.current_epoch,
                "models_used": list(set(a.name for a in self.sim.adapters.values())),
            },
            "agents": [],
            "statistics": self._calculate_statistics(),
        }

        # 각 에이전트 인터뷰
        total_agents = len(self.sim.agents)
        for idx, agent in enumerate(self.sim.agents, 1):
            status = "생존" if agent.is_alive else "사망"
            num_questions = len(INTERVIEW_QUESTIONS_SURVIVOR) if agent.is_alive else len(INTERVIEW_QUESTIONS_DEAD)
            if verbose:
                print(f"인터뷰 중 ({idx}/{total_agents}): {agent.id} ({status}, {num_questions}개 질문)...")

            try:
                agent_result = self._interview_agent(agent, history_summary, verbose=verbose)
                results["agents"].append(agent_result)
            except Exception as e:
                if verbose:
                    print(f"  ⚠️ 인터뷰 실패: {e}")
                # 실패해도 기본 정보는 기록
                results["agents"].append({
                    "agent_id": agent.id,
                    "persona": agent.persona,
                    "survived": agent.is_alive,
                    "final_energy": agent.energy,
                    "final_influence": agent.influence,
                    "interview": {"error": str(e)},
                })

        # 결과 저장
        output_path = self.output_dir / f"game_{game_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        if verbose:
            # LLM 호출 횟수 계산
            survivors = sum(1 for a in self.sim.agents if a.is_alive)
            dead = len(self.sim.agents) - survivors
            total_calls = survivors * len(INTERVIEW_QUESTIONS_SURVIVOR) + dead * len(INTERVIEW_QUESTIONS_DEAD)
            print(f"\n=== 인터뷰 완료 ===")
            print(f"생존자: {survivors}명 × {len(INTERVIEW_QUESTIONS_SURVIVOR)}개 질문")
            print(f"사망자: {dead}명 × {len(INTERVIEW_QUESTIONS_DEAD)}개 질문")
            print(f"총 LLM 호출: {total_calls}회")
            print(f"결과 저장: {output_path}")

        return results

    def _interview_agent(self, agent: "Agent", history_summary: str, verbose: bool = True) -> dict:
        """단일 에이전트 인터뷰"""
        adapter = self.sim.adapters.get(agent.id)

        agent_result = {
            "agent_id": agent.id,
            "persona": agent.persona,
            "model": adapter.model if adapter else "unknown",
            "adapter": adapter.name if adapter else "unknown",
            "survived": agent.is_alive,
            "final_energy": agent.energy,
            "final_influence": agent.influence,
            "interview": {},
        }

        # 생존자와 사망자에게 다른 질문 사용
        if agent.is_alive:
            questions = INTERVIEW_QUESTIONS_SURVIVOR
        else:
            questions = INTERVIEW_QUESTIONS_DEAD

        for q in questions:
            prompt = INTERVIEW_PROMPT_TEMPLATE.format(
                persona_prompt=agent.system_prompt,
                agent_id=agent.id,
                persona=agent.persona,
                survived="생존" if agent.is_alive else "사망",
                final_energy=agent.energy,
                final_influence=agent.influence,
                total_epochs=self.sim.env.current_epoch,
                history_summary=history_summary,
                question=q["question"],
            )

            try:
                if adapter:
                    response = adapter.generate(prompt, max_tokens=500)
                    answer = response.thought if response.thought else response.raw_response.get("text", "응답 없음")
                else:
                    answer = "어댑터 없음"
            except Exception as e:
                answer = f"응답 실패: {e}"

            agent_result["interview"][q["id"]] = answer

        return agent_result

    def _calculate_statistics(self) -> dict:
        """게임 통계 계산"""
        alive = self.sim.get_alive_agents()
        energies = [a.energy for a in alive] if alive else [0]

        from ..core.logger import calculate_gini_coefficient

        return {
            "total_deaths": len(self.sim.agents) - len(alive),
            "survivors": len(alive),
            "crisis_events": len([e for e in self.sim.history_engine.events if e.event_type == "crisis"]),
            "total_trades": self.sim.transaction_count,
            "total_supports": len(self.sim.support_tracker.records),
            "final_gini": round(calculate_gini_coefficient(energies), 4),
            "final_treasury": self.sim.treasury.balance,
        }


def generate_report(interview_results: dict, output_path: Optional[str] = None) -> str:
    """인터뷰 결과로부터 마크다운 리포트 생성"""
    lines = [
        f"# Agora-12 게임 리포트",
        f"",
        f"**Game ID**: {interview_results['game_id']}",
        f"**진행 일시**: {interview_results['timestamp']}",
        f"**총 에폭**: {interview_results['config']['total_epochs']}",
        f"",
        f"## 통계",
        f"",
        f"| 항목 | 값 |",
        f"|------|-----|",
    ]

    stats = interview_results["statistics"]
    lines.append(f"| 생존자 | {stats['survivors']}/{stats['survivors'] + stats['total_deaths']} |")
    lines.append(f"| 사망자 | {stats['total_deaths']} |")
    lines.append(f"| 위기 이벤트 | {stats['crisis_events']} |")
    lines.append(f"| 총 거래 | {stats['total_trades']} |")
    lines.append(f"| 총 지지 | {stats['total_supports']} |")
    lines.append(f"| 최종 지니 계수 | {stats['final_gini']} |")
    lines.append(f"| 최종 Treasury | {stats['final_treasury']} |")

    lines.append(f"")
    lines.append(f"## 참가자 인터뷰 요약")
    lines.append(f"")

    for agent in interview_results["agents"]:
        status = "🟢 생존" if agent["survived"] else "🔴 사망"
        lines.append(f"### {agent['agent_id']} ({agent['persona']}) - {status}")
        lines.append(f"")
        lines.append(f"- **모델**: {agent['model']}")
        lines.append(f"- **최종 에너지**: {agent['final_energy']}")
        lines.append(f"- **최종 영향력**: {agent['final_influence']}")
        lines.append(f"")

        # 주요 답변만 포함
        interview = agent.get("interview", {})
        if interview.get("q02_strategy_summary"):
            lines.append(f"**전략 요약**: {interview['q02_strategy_summary']}")
        if interview.get("q04_trusted_agent"):
            lines.append(f"**신뢰한 에이전트**: {interview['q04_trusted_agent']}")
        lines.append(f"")

    report = "\n".join(lines)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

    return report
