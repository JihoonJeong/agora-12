"""Agora-12 Core Module"""

from .agent import Agent, create_agents_from_config
from .environment import Environment, Space, Billboard
from .personas import PERSONA_PROMPTS, get_persona_prompt
from .logger import SimulationLogger, calculate_gini_coefficient
from .support import SupportTracker, SupportRecord
from .whisper import WhisperSystem, Suspicion
from .market import MarketPool, Treasury, TradeRecord
from .influence import InfluenceSystem, InfluenceTier, ELDER_SUPPORT_MULTIPLIER
from .crisis import CrisisSystem, CrisisEvent, CRISIS_SUPPORT_BONUS
from .architect import ArchitectSkills, ArchitectSkillResult
from .actions import ActionType, ActionResult, ActionConfig, get_speak_type, get_available_actions
from .context import build_context, CONTEXT_TEMPLATE, get_energy_status, get_inequality_commentary
from .history import HistoryEngine, HistoricalEvent
from .simulation import Simulation

__all__ = [
    "Agent",
    "create_agents_from_config",
    "Environment",
    "Space",
    "Billboard",
    "PERSONA_PROMPTS",
    "get_persona_prompt",
    "SimulationLogger",
    "calculate_gini_coefficient",
    "SupportTracker",
    "SupportRecord",
    "WhisperSystem",
    "Suspicion",
    "MarketPool",
    "Treasury",
    "TradeRecord",
    "InfluenceSystem",
    "InfluenceTier",
    "ELDER_SUPPORT_MULTIPLIER",
    "CrisisSystem",
    "CrisisEvent",
    "CRISIS_SUPPORT_BONUS",
    "ArchitectSkills",
    "ArchitectSkillResult",
    "ActionType",
    "ActionResult",
    "ActionConfig",
    "get_speak_type",
    "get_available_actions",
    "build_context",
    "CONTEXT_TEMPLATE",
    "get_energy_status",
    "get_inequality_commentary",
    "HistoryEngine",
    "HistoricalEvent",
    "Simulation",
]
