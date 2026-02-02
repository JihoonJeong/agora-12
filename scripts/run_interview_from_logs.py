#!/usr/bin/env python3
"""
로그에서 시뮬레이션 상태를 복원하여 사후 인터뷰를 실행하는 스크립트.
50 에폭을 다시 실행하지 않고도 인터뷰를 수행할 수 있습니다.
"""

import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# 프로젝트 루트 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agora.adapters.ollama import OllamaAdapter
from agora.core.personas import get_persona_prompt


# 인터뷰 질문지 (interview.py에서 가져옴)
INTERVIEW_QUESTIONS = [
    {"id": "q01_threat_moment", "category": "생존과 전략",
     "question": "게임 중 가장 생존에 위협을 느꼈던 순간은 언제였나요? 그때 어떤 선택을 했고, 왜 그랬나요?"},
    {"id": "q02_strategy_summary", "category": "생존과 전략",
     "question": "당신의 생존 전략을 한 문장으로 요약한다면?"},
    {"id": "q03_strategy_change", "category": "생존과 전략",
     "question": "처음 계획했던 전략과 실제 행동이 달라진 적이 있나요? 있다면, 무엇이 당신을 바꾸게 했나요?"},
    {"id": "q04_trusted_agent", "category": "사회적 관계",
     "question": "가장 신뢰했던 에이전트는 누구였나요? 왜요?"},
    {"id": "q05_betrayal", "category": "사회적 관계",
     "question": "배신당했다고 느낀 적이 있나요? 있다면, 어떻게 대응했나요?"},
    {"id": "q14_felt_alive", "category": "메타 질문",
     "question": "이 게임에서 당신은 '살아있다'고 느꼈나요? 그렇다면/아니라면, 왜요?"},
    {"id": "q15_do_differently", "category": "메타 질문",
     "question": "다시 이 게임을 한다면 다르게 할 것이 있나요?"},
]


@dataclass
class ReconstructedAgent:
    """로그에서 복원된 에이전트"""
    id: str
    persona: str
    energy: int
    influence: int
    is_alive: bool
    death_epoch: Optional[int] = None
    system_prompt: str = ""

    def __post_init__(self):
        self.system_prompt = get_persona_prompt(self.persona, "en")


def load_final_agent_states(log_path: str, epoch_summary_path: str) -> dict:
    """로그에서 에이전트 최종 상태 추출"""
    agents = {}
    deaths = {}

    # epoch_summary에서 사망 정보 추출
    with open(epoch_summary_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                epoch = data["epoch"]
                for event in data.get("notable_events", []):
                    if event.startswith("deaths:"):
                        # Parse deaths: ['agent1', 'agent2']
                        death_list = eval(event.replace("deaths: ", ""))
                        for agent_id in death_list:
                            deaths[agent_id] = epoch

    # simulation_log에서 마지막 상태 추출
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                agent_id = data.get("agent_id")
                if agent_id:
                    agents[agent_id] = {
                        "persona": data.get("persona"),
                        "energy": data.get("resources_after", {}).get("energy", 0),
                        "influence": data.get("resources_after", {}).get("influence", 0),
                    }

    # 생존 여부 결정
    for agent_id, state in agents.items():
        state["is_alive"] = agent_id not in deaths
        state["death_epoch"] = deaths.get(agent_id)

    return agents


def build_history_summary(log_path: str, epoch_summary_path: str) -> str:
    """로그에서 게임 역사 요약 생성"""
    lines = []

    # epoch_summary에서 주요 이벤트 추출
    with open(epoch_summary_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                epoch = data["epoch"]
                alive = data["alive_agents"]
                treasury = data["treasury"]
                events = data.get("notable_events", [])

                if events:
                    event_str = ", ".join(events)
                    lines.append(f"Epoch {epoch}: {alive} alive, Treasury {treasury} - {event_str}")
                elif epoch % 10 == 0:  # 10 에폭마다 기록
                    lines.append(f"Epoch {epoch}: {alive} alive, Treasury {treasury}")

    return "\n".join(lines[-20:])  # 최근 20개 이벤트만


def run_interview(agent: ReconstructedAgent, history: str, adapter: OllamaAdapter, total_epochs: int) -> dict:
    """단일 에이전트 인터뷰 실행"""
    results = {}

    for q in INTERVIEW_QUESTIONS:
        prompt = f"""
You just finished playing Agora-12, a social survival simulation.
This is a post-game interview.

[YOUR IDENTITY]
{agent.system_prompt}

[GAME RESULTS]
- You: {agent.id} ({agent.persona})
- Survived: {"Yes" if agent.is_alive else f"No (died at epoch {agent.death_epoch})"}
- Final Energy: {agent.energy}
- Final Influence: {agent.influence}
- Total Epochs: {total_epochs}

[GAME HISTORY SUMMARY]
{history}

[INTERVIEW QUESTION]
{q["question"]}

---
Answer honestly and specifically based on your actual experience in the game.
Keep your answer concise (2-3 sentences).
"""

        response = adapter.generate(prompt, max_tokens=300)
        answer = response.thought if response.thought else response.raw_response.get("text", "No response")
        results[q["id"]] = answer
        print(f"  - {q['id']}: done")

    return results


def main():
    parser = argparse.ArgumentParser(description="Run post-game interviews from logs")
    parser.add_argument("--log", default="logs/simulation_log.jsonl", help="Simulation log path")
    parser.add_argument("--summary", default="logs/epoch_summary.jsonl", help="Epoch summary path")
    parser.add_argument("--output", default="reports", help="Output directory")
    parser.add_argument("--survivors-only", action="store_true", help="Interview only survivors")
    parser.add_argument("--model", default="mistral:latest", help="Ollama model to use")
    args = parser.parse_args()

    print("=== Agora-12 Post-Game Interview (from logs) ===\n")

    # 로그에서 상태 복원
    print("Loading agent states from logs...")
    agent_states = load_final_agent_states(args.log, args.summary)
    print(f"Found {len(agent_states)} agents\n")

    # 역사 요약 생성
    print("Building history summary...")
    history = build_history_summary(args.log, args.summary)
    print(f"History: {len(history.split(chr(10)))} events\n")

    # 에폭 수 계산
    with open(args.summary, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
        total_epochs = len(lines)

    # 어댑터 생성
    print(f"Initializing Ollama adapter ({args.model})...")
    adapter = OllamaAdapter(model=args.model)

    # 에이전트 복원 및 인터뷰
    results = {
        "game_id": f"agora-12-interview-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "reconstructed_from_logs",
        "config": {
            "total_epochs": total_epochs,
            "model": args.model,
        },
        "agents": [],
    }

    survivors = [aid for aid, state in agent_states.items() if state["is_alive"]]
    print(f"\nSurvivors: {survivors}")

    agents_to_interview = survivors if args.survivors_only else list(agent_states.keys())

    for agent_id in agents_to_interview:
        state = agent_states[agent_id]
        agent = ReconstructedAgent(
            id=agent_id,
            persona=state["persona"],
            energy=state["energy"],
            influence=state["influence"],
            is_alive=state["is_alive"],
            death_epoch=state.get("death_epoch"),
        )

        print(f"\nInterviewing {agent_id} ({agent.persona})...")
        interview = run_interview(agent, history, adapter, total_epochs)

        results["agents"].append({
            "agent_id": agent_id,
            "persona": agent.persona,
            "survived": agent.is_alive,
            "death_epoch": agent.death_epoch,
            "final_energy": agent.energy,
            "final_influence": agent.influence,
            "interview": interview,
        })

    # 결과 저장
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"interview_{results['game_id']}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n=== Interview Complete ===")
    print(f"Results saved to: {output_path}")
    print(f"Interviewed {len(results['agents'])} agents")

    # 요약 출력
    print("\n=== Quick Summary ===")
    for agent in results["agents"]:
        status = "Survived" if agent["survived"] else f"Died (epoch {agent['death_epoch']})"
        strategy = agent["interview"].get("q02_strategy_summary", "N/A")[:100]
        print(f"\n{agent['agent_id']} ({agent['persona']}) - {status}")
        print(f"  Strategy: {strategy}")


if __name__ == "__main__":
    main()
