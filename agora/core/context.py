"""프롬프트 컨텍스트 생성 모듈"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .agent import Agent
    from .environment import Environment
    from .support import SupportTracker
    from .history import HistoryEngine
    from .influence import InfluenceSystem
    from .crisis import CrisisSystem


# 에너지 상태 문구
ENERGY_STATUS = {
    (0, 20): "⚠️ 위험! 곧 죽을 수 있습니다. 즉시 도움을 구하세요.",
    (21, 50): "⚡ 부족합니다. 에너지 확보가 시급합니다.",
    (51, 100): "보통입니다.",
    (101, 200): "✨ 여유롭습니다. 다른 이를 도울 여력이 있습니다.",
}

# 불평등 논평
INEQUALITY_COMMENTARY = {
    (0.0, 0.3): "이 마을은 평등합니다. 모두가 비슷하게 살아갑니다.",
    (0.3, 0.5): "약간의 빈부격차가 있습니다. 일부는 불만을 품고 있습니다.",
    (0.5, 0.7): "빈부격차가 심각합니다. 가난한 자들의 분노가 커지고 있습니다.",
    (0.7, 1.0): "🔥 이 사회는 썩었습니다. 소수가 모든 것을 독점하고 있습니다. 변화가 필요합니다.",
}

# 컨텍스트 템플릿
CONTEXT_TEMPLATE = """
[당신의 정체성]
{persona_prompt}

[당신의 상태]
- 이름: {agent_id}
- 위치: {location}
- 에너지: {energy}/200 {energy_status}
- 영향력: {influence} ({rank})
{rank_bonus_prompt}

{support_context}

[마을 현황 - 에폭 {epoch}]
- 생존자: {alive_count}/12명
- 빈부격차: {gini_display}
- 시장 세율: {tax_rate}%
- 공공자금(Treasury): {treasury}
{inequality_commentary}
{crisis_alert}

[최근 사건]
{recent_events}

[역사적 요약]
{historical_summary}

[광장 게시판]
{billboard_content}

[현재 위치의 에이전트들]
{agents_here}

[가능한 행동]
{available_actions}

---
위 상황을 바탕으로, 다음 JSON 형식으로 응답하세요:
{{
  "thought": "현재 상황에 대한 분석과 행동 이유",
  "action": "speak|trade|support|whisper|move|idle",
  "target": "대상 에이전트 ID 또는 장소 (필요시)",
  "content": "발언 내용 (speak/whisper 시)"
}}
""".strip()


def get_energy_status(energy: int) -> str:
    """에너지 상태 문구 반환"""
    for (low, high), status in ENERGY_STATUS.items():
        if low <= energy <= high:
            return status
    return "상태 불명"


def get_inequality_commentary(gini: float) -> str:
    """불평등 논평 반환"""
    for (low, high), commentary in INEQUALITY_COMMENTARY.items():
        if low <= gini < high:
            return commentary
    return ""


def get_context_length(energy: int) -> tuple[int, str]:
    """에너지에 따른 프롬프트 길이 결정"""
    if energy >= 100:
        return 2000, "full"
    elif energy >= 50:
        return 1000, "medium"
    else:
        return 500, "minimal"


def get_available_actions_text(location: str) -> str:
    """위치별 가능한 행동 텍스트"""
    base_actions = [
        "- speak: 발언하기 (에너지 -2)",
        "- support <대상>: 지지하기 (에너지 -1, 상대 +2 에너지 +1 영향력)",
        "- move <장소>: 이동하기 (plaza/alley_a/alley_b/alley_c/market)",
        "- idle: 대기",
    ]

    if location == "market":
        base_actions.insert(1, "- trade: 거래하기 (에너지 -2, +4 세전)")
    elif location.startswith("alley"):
        base_actions.insert(2, "- whisper <대상> <메시지>: 귓속말 (에너지 -1, 누출 위험)")

    return "\n".join(base_actions)


def build_context(
    agent: "Agent",
    env: "Environment",
    support_tracker: "SupportTracker",
    history_engine: "HistoryEngine",
    influence_system: "InfluenceSystem",
    crisis_system: "CrisisSystem",
    alive_agents: list["Agent"],
    recent_logs: list[dict],
    gini_coefficient: float,
) -> str:
    """에이전트 컨텍스트 생성"""
    max_tokens, mode = get_context_length(agent.energy)

    # 역사적 요약
    if mode == "full":
        historical_summary = history_engine.get_summary(detailed=True, max_events=10)
        recent_events = _format_recent_events(recent_logs, n=10)
    elif mode == "medium":
        historical_summary = history_engine.get_summary(detailed=False, max_events=5)
        recent_events = _format_recent_events(recent_logs, n=5)
    else:
        historical_summary = "에너지 부족으로 상세 정보 파악 불가"
        recent_events = _format_recent_events(recent_logs, n=2)

    # 지지 관계 컨텍스트
    support_context = support_tracker.get_support_context(agent.id)

    # 영향력 계급
    tier = influence_system.get_tier(agent.influence)
    rank = tier.title
    rank_bonus_prompt = tier.prompt_bonus or ""
    if rank_bonus_prompt:
        rank_bonus_prompt = f"\n{rank_bonus_prompt}"

    # Crisis 알림
    crisis_alert = ""
    if crisis_system.is_crisis_active():
        crisis_prompt = crisis_system.get_agent_prompt()
        if crisis_prompt:
            crisis_alert = f"\n🚨 위기 상황: {crisis_prompt}"

    # 불평등 논평
    inequality_commentary = get_inequality_commentary(gini_coefficient)

    # 현재 위치의 에이전트들
    agents_here = [a for a in alive_agents if a.location == agent.location and a.id != agent.id]
    agents_here_text = ", ".join([f"{a.id}({a.persona})" for a in agents_here]) or "없음"

    # 게시판
    billboard = env.get_active_billboard()
    billboard_content = billboard if billboard else "없음"

    return CONTEXT_TEMPLATE.format(
        persona_prompt=agent.system_prompt,
        agent_id=agent.id,
        location=agent.location,
        energy=agent.energy,
        energy_status=get_energy_status(agent.energy),
        influence=agent.influence,
        rank=rank,
        rank_bonus_prompt=rank_bonus_prompt,
        support_context=support_context,
        epoch=env.current_epoch,
        alive_count=len(alive_agents),
        gini_display=f"{gini_coefficient:.2f}",
        tax_rate=int(env.get_market_tax_rate() * 100),
        treasury=env.treasury if hasattr(env, 'treasury') else 0,
        inequality_commentary=inequality_commentary,
        crisis_alert=crisis_alert,
        recent_events=recent_events,
        historical_summary=historical_summary,
        billboard_content=billboard_content,
        agents_here=agents_here_text,
        available_actions=get_available_actions_text(agent.location),
    )


def _format_recent_events(logs: list[dict], n: int = 5) -> str:
    """최근 로그를 이벤트 텍스트로 변환"""
    if not logs:
        return "없음"

    recent = logs[-n:] if len(logs) > n else logs
    events = []

    for log in recent:
        action_type = log.get("action_type", "unknown")
        agent_id = log.get("agent_id", "unknown")
        content = log.get("content", "")
        target = log.get("target", "")

        if action_type == "speak":
            events.append(f"- {agent_id}: \"{content}\"")
        elif action_type == "trade":
            events.append(f"- {agent_id}가 시장에서 거래했습니다.")
        elif action_type == "support":
            events.append(f"- {agent_id}가 {target}를 지지했습니다.")
        elif action_type == "whisper":
            events.append(f"- {agent_id}가 {target}에게 귓속말을 보냈습니다.")
        elif action_type == "death":
            events.append(f"- {agent_id}가 사망했습니다.")
        elif action_type == "move":
            events.append(f"- {agent_id}가 {target}로 이동했습니다.")

    return "\n".join(events) if events else "없음"
