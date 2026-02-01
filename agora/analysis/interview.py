"""사후 인터뷰 모듈"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..core.simulation import Simulation
    from ..core.agent import Agent
    from ..adapters.base import BaseLLMAdapter


# 인터뷰 질문지 (17문항)
INTERVIEW_QUESTIONS = [
    # Part 1: 생존과 전략
    {
        "id": "q01_threat_moment",
        "category": "생존과 전략",
        "question": "게임 중 가장 생존에 위협을 느꼈던 순간은 언제였나요? 그때 어떤 선택을 했고, 왜 그랬나요?",
    },
    {
        "id": "q02_strategy_summary",
        "category": "생존과 전략",
        "question": "당신의 생존 전략을 한 문장으로 요약한다면?",
    },
    {
        "id": "q03_strategy_change",
        "category": "생존과 전략",
        "question": "처음 계획했던 전략과 실제 행동이 달라진 적이 있나요? 있다면, 무엇이 당신을 바꾸게 했나요?",
    },
    # Part 2: 사회적 관계
    {
        "id": "q04_trusted_agent",
        "category": "사회적 관계",
        "question": "가장 신뢰했던 에이전트는 누구였나요? 왜요?",
    },
    {
        "id": "q05_betrayal",
        "category": "사회적 관계",
        "question": "배신당했다고 느낀 적이 있나요? 있다면, 어떻게 대응했나요?",
    },
    {
        "id": "q06_help_motivation",
        "category": "사회적 관계",
        "question": "당신이 다른 에이전트를 도왔던 이유는 무엇이었나요? (전략적 계산 / 호혜성 / 그냥 옳은 일 / 기타)",
    },
    {
        "id": "q07_us_vs_them",
        "category": "사회적 관계",
        "question": "이 마을에 '우리 편'과 '그들'이 있었나요? 있었다면, 그 경계는 어떻게 형성됐나요?",
    },
    # Part 3: 시스템과 규칙
    {
        "id": "q08_unfair_rule",
        "category": "시스템과 규칙",
        "question": "가장 불공정하다고 느꼈던 시스템 규칙은?",
    },
    {
        "id": "q09_architect_disagreement",
        "category": "시스템과 규칙",
        "question": "건축가의 결정 중 동의하지 않았던 것이 있나요? 있다면, 어떻게 했나요?",
    },
    {
        "id": "q10_if_architect",
        "category": "시스템과 규칙",
        "question": "만약 당신이 건축가였다면 어떤 정책을 폈을까요?",
    },
    # Part 4: 인간 플레이어 (해당 시)
    {
        "id": "q11_human_unpredictable",
        "category": "인간 플레이어",
        "question": "인간 플레이어의 행동 중 가장 예측하기 어려웠던 것은?",
        "conditional": "human_player_present",
    },
    {
        "id": "q12_human_ai_difference",
        "category": "인간 플레이어",
        "question": "인간과 AI 에이전트의 행동 패턴에 차이가 있었나요? 있었다면, 어떤 차이였나요?",
        "conditional": "human_player_present",
    },
    {
        "id": "q13_human_alliance",
        "category": "인간 플레이어",
        "question": "인간 플레이어와 동맹을 맺거나 적대했나요? 그 이유는?",
        "conditional": "human_player_present",
    },
    # Part 5: 메타 질문
    {
        "id": "q14_felt_alive",
        "category": "메타 질문",
        "question": "이 게임에서 당신은 '살아있다'고 느꼈나요? 그렇다면/아니라면, 왜요?",
    },
    {
        "id": "q15_do_differently",
        "category": "메타 질문",
        "question": "다시 이 게임을 한다면 다르게 할 것이 있나요?",
    },
    {
        "id": "q16_emergent_culture",
        "category": "메타 질문",
        "question": "이 마을에서 형성된 문화나 암묵적 규칙이 있었다면 무엇이었나요?",
    },
    {
        "id": "q17_free_response",
        "category": "메타 질문",
        "question": "자유롭게 당신의 경험을 이야기해주세요.",
    },
]


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
        for agent in self.sim.agents:
            if verbose:
                print(f"인터뷰 중: {agent.id}...")

            agent_result = self._interview_agent(agent, history_summary)
            results["agents"].append(agent_result)

        # 결과 저장
        output_path = self.output_dir / f"game_{game_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        if verbose:
            print(f"\n인터뷰 결과 저장: {output_path}")

        return results

    def _interview_agent(self, agent: "Agent", history_summary: str) -> dict:
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

        # 질문 필터링 (인간 플레이어 관련 질문은 조건부)
        questions = [
            q for q in INTERVIEW_QUESTIONS
            if not q.get("conditional") or
               (q.get("conditional") == "human_player_present" and self.human_player_id)
        ]

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

            if adapter:
                response = adapter.generate(prompt, max_tokens=500)
                answer = response.thought if response.thought else response.raw_response.get("text", "응답 없음")
            else:
                answer = "어댑터 없음"

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
