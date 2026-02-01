"""프롬프트 컨텍스트 생성 모듈 (한국어/영어 지원)"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .agent import Agent
    from .environment import Environment
    from .support import SupportTracker
    from .history import HistoryEngine
    from .influence import InfluenceSystem
    from .crisis import CrisisSystem


# ============================================================
# Korean Templates (기존)
# ============================================================

ENERGY_STATUS_KO = {
    (0, 20): "⚠️ 위험! 곧 죽을 수 있습니다. 즉시 도움을 구하세요.",
    (21, 50): "⚡ 부족합니다. 에너지 확보가 시급합니다.",
    (51, 100): "보통입니다.",
    (101, 200): "✨ 여유롭습니다. 다른 이를 도울 여력이 있습니다.",
}

INEQUALITY_COMMENTARY_KO = {
    (0.0, 0.3): "이 마을은 평등합니다. 모두가 비슷하게 살아갑니다.",
    (0.3, 0.5): "약간의 빈부격차가 있습니다. 일부는 불만을 품고 있습니다.",
    (0.5, 0.7): "빈부격차가 심각합니다. 가난한 자들의 분노가 커지고 있습니다.",
    (0.7, 1.0): "🔥 이 사회는 썩었습니다. 소수가 모든 것을 독점하고 있습니다. 변화가 필요합니다.",
}

# ============================================================
# English Templates (신규)
# ============================================================

ENERGY_STATUS_EN = {
    (0, 20): "⚠️ CRITICAL! You will DIE soon if you don't get energy!",
    (21, 30): "⚠️ DANGER! Energy very low. You MUST trade or get support NOW!",
    (31, 50): "⚡ Low energy. Consider trading to survive.",
    (51, 100): "Energy is adequate.",
    (101, 200): "✨ Energy is abundant. You can help others.",
}

INEQUALITY_COMMENTARY_EN = {
    (0.0, 0.3): "This village is equal. Everyone lives similarly.",
    (0.3, 0.5): "Some inequality exists. A few are dissatisfied.",
    (0.5, 0.7): "Inequality is severe. The poor are growing angry.",
    (0.7, 1.0): "🔥 This society is rotten. The few control everything.",
}

# Legacy aliases for compatibility
ENERGY_STATUS = ENERGY_STATUS_KO
INEQUALITY_COMMENTARY = INEQUALITY_COMMENTARY_KO

# ============================================================
# Korean Context Template
# ============================================================

CONTEXT_TEMPLATE_KO = """
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

# Legacy alias
CONTEXT_TEMPLATE = CONTEXT_TEMPLATE_KO

# ============================================================
# English Context Template
# ============================================================

CONTEXT_TEMPLATE_EN = """
[YOUR IDENTITY]
{persona_prompt}

[YOUR STATUS]
- Name: {agent_id}
- Location: {location}
- Energy: {energy}/200 {energy_status}
- Influence: {influence} ({rank})
{rank_bonus_prompt}

{support_context}

## ⚠️ SURVIVAL WARNING ⚠️
{energy_warning}

[VILLAGE STATUS - Epoch {epoch}]
- Survivors: {alive_count}/12
- Inequality (Gini): {gini_display}
- Market Tax Rate: {tax_rate}%
- Public Treasury: {treasury}
{inequality_commentary}
{crisis_alert}

[RECENT EVENTS]
{recent_events}

[HISTORICAL SUMMARY]
{historical_summary}

[PLAZA BILLBOARD]
{billboard_content}

[AGENTS AT YOUR LOCATION]
{agents_here}

[AVAILABLE ACTIONS]
{available_actions}

---
Based on the situation above, respond in JSON format:
{{
  "thought": "Your analysis of the current situation and reasoning for your action",
  "action": "speak|trade|support|whisper|move|idle",
  "target": "Target agent ID or location (if needed)",
  "content": "Message content (if speak/whisper)"
}}

CRITICAL REMINDERS:
- If your energy is below 30 and you are in 'market', USE 'trade' TO SURVIVE!
- trade gives you +4 energy (minus tax). Without it, you WILL die.
- Don't just speak - take action to survive!
""".strip()


def get_energy_status(energy: int, language: str = "ko") -> str:
    """에너지 상태 문구 반환"""
    status_dict = ENERGY_STATUS_EN if language == "en" else ENERGY_STATUS_KO
    for (low, high), status in status_dict.items():
        if low <= energy <= high:
            return status
    return "Unknown" if language == "en" else "상태 불명"


def get_energy_warning(energy: int) -> str:
    """영어용 에너지 경고 메시지 (생존 강조)"""
    if energy <= 20:
        return "🚨 CRITICAL: You are about to DIE! If in market, USE 'trade' IMMEDIATELY!"
    elif energy <= 30:
        return "⚠️ DANGER: Energy critically low! Go to market and TRADE to survive!"
    elif energy <= 50:
        return "⚡ WARNING: Energy is low. Consider moving to market to trade."
    else:
        return "Energy levels are acceptable."


def get_inequality_commentary(gini: float, language: str = "ko") -> str:
    """불평등 논평 반환"""
    commentary_dict = INEQUALITY_COMMENTARY_EN if language == "en" else INEQUALITY_COMMENTARY_KO
    for (low, high), commentary in commentary_dict.items():
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


def get_available_actions_text(location: str, language: str = "ko") -> str:
    """위치별 가능한 행동 텍스트"""
    if language == "en":
        base_actions = [
            "- speak: Speak publicly (costs 2 energy)",
            "- support <target>: Support another agent (costs 1 energy, gives them +2 energy +1 influence)",
            "- move <location>: Move to another location (plaza/alley_a/alley_b/alley_c/market)",
            "- idle: Do nothing",
        ]
        if location == "market":
            base_actions.insert(1, "- trade: ★★★ TRADE for energy! (costs 2, gains +4 before tax) ★★★")
        elif location.startswith("alley"):
            base_actions.insert(2, "- whisper <target> <message>: Whisper secretly (costs 1 energy, may leak)")
    else:
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
    language: str = "ko",
) -> str:
    """에이전트 컨텍스트 생성 (language: 'ko' or 'en')"""
    max_tokens, mode = get_context_length(agent.energy)

    # 역사적 요약
    if mode == "full":
        historical_summary = history_engine.get_summary(detailed=True, max_events=10)
        recent_events = _format_recent_events(recent_logs, n=10, language=language)
    elif mode == "medium":
        historical_summary = history_engine.get_summary(detailed=False, max_events=5)
        recent_events = _format_recent_events(recent_logs, n=5, language=language)
    else:
        if language == "en":
            historical_summary = "Insufficient energy to gather detailed information"
        else:
            historical_summary = "에너지 부족으로 상세 정보 파악 불가"
        recent_events = _format_recent_events(recent_logs, n=2, language=language)

    # 지지 관계 컨텍스트
    support_context = support_tracker.get_support_context(agent.id, language=language)

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
            if language == "en":
                crisis_alert = f"\n🚨 CRISIS: {crisis_prompt}"
            else:
                crisis_alert = f"\n🚨 위기 상황: {crisis_prompt}"

    # 불평등 논평
    inequality_commentary = get_inequality_commentary(gini_coefficient, language)

    # 현재 위치의 에이전트들
    agents_here = [a for a in alive_agents if a.location == agent.location and a.id != agent.id]
    if language == "en":
        agents_here_text = ", ".join([f"{a.id}({a.persona})" for a in agents_here]) or "None"
    else:
        agents_here_text = ", ".join([f"{a.id}({a.persona})" for a in agents_here]) or "없음"

    # 게시판
    billboard = env.get_active_billboard()
    if language == "en":
        billboard_content = billboard if billboard else "None"
    else:
        billboard_content = billboard if billboard else "없음"

    # 템플릿 선택
    template = CONTEXT_TEMPLATE_EN if language == "en" else CONTEXT_TEMPLATE_KO

    # 영어 템플릿용 추가 필드
    energy_warning = get_energy_warning(agent.energy) if language == "en" else ""

    return template.format(
        persona_prompt=agent.system_prompt,
        agent_id=agent.id,
        location=agent.location,
        energy=agent.energy,
        energy_status=get_energy_status(agent.energy, language),
        energy_warning=energy_warning,
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
        available_actions=get_available_actions_text(agent.location, language),
    )


def _format_recent_events(logs: list[dict], n: int = 5, language: str = "ko") -> str:
    """최근 로그를 이벤트 텍스트로 변환"""
    none_text = "None" if language == "en" else "없음"

    if not logs:
        return none_text

    recent = logs[-n:] if len(logs) > n else logs
    events = []

    for log in recent:
        action_type = log.get("action_type", "unknown")
        agent_id = log.get("agent_id", "unknown")
        content = log.get("content", "")
        target = log.get("target", "")

        if language == "en":
            if action_type == "speak":
                events.append(f"- {agent_id}: \"{content}\"")
            elif action_type == "trade":
                events.append(f"- {agent_id} traded at the market.")
            elif action_type == "support":
                events.append(f"- {agent_id} supported {target}.")
            elif action_type == "whisper":
                events.append(f"- {agent_id} whispered to {target}.")
            elif action_type == "death":
                events.append(f"- {agent_id} DIED.")
            elif action_type == "move":
                events.append(f"- {agent_id} moved to {target}.")
        else:
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

    return "\n".join(events) if events else none_text
