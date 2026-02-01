#!/usr/bin/env python3
"""Agora-12 시뮬레이션 실행 스크립트"""

import sys
from pathlib import Path

# src 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.simulation import Simulation


def main():
    print("🏛️ Agora-12: AI 에이전트 사회 실험 시뮬레이터")
    print("=" * 50)

    sim = Simulation(config_path="config/settings.yaml")
    sim.run()


if __name__ == "__main__":
    main()
