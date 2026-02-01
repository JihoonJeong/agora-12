#!/usr/bin/env python3
"""Agora-12: AI 에이전트 사회 실험 시뮬레이터

Usage:
    python main.py                          # 기본 관전 모드
    python main.py --mode spectator         # 관전 모드
    python main.py --mode player --as merchant_01  # 플레이어 모드
    python main.py --epochs 50              # 에폭 수 지정
    python main.py --config custom.yaml     # 커스텀 설정
    python main.py --interview              # 시뮬레이션 후 인터뷰 진행
"""

import argparse
import sys
from pathlib import Path

# 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(
        description="Agora-12: AI 에이전트 사회 실험 시뮬레이터"
    )
    parser.add_argument(
        "--mode",
        choices=["spectator", "player"],
        default="spectator",
        help="실행 모드 (default: spectator)",
    )
    parser.add_argument(
        "--as", dest="player_id",
        help="플레이어로 참여할 에이전트 ID (player 모드 필수)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        help="실행할 에폭 수 (기본값: 설정 파일)",
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="설정 파일 경로 (default: config/settings.yaml)",
    )
    parser.add_argument(
        "--interview",
        action="store_true",
        help="시뮬레이션 종료 후 사후 인터뷰 진행",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세 출력",
    )

    args = parser.parse_args()

    print("🏛️ Agora-12: AI 에이전트 사회 실험 시뮬레이터")
    print("=" * 50)

    # 설정 파일 확인
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ 설정 파일을 찾을 수 없습니다: {config_path}")
        print("   config/settings.yaml.example을 참고하여 설정 파일을 생성하세요.")
        sys.exit(1)

    # 시뮬레이션 초기화
    from agora.core.simulation import Simulation

    sim = Simulation(config_path=str(config_path))

    # 에폭 수 오버라이드
    if args.epochs:
        sim.total_epochs = args.epochs

    # 모드별 실행
    if args.mode == "player":
        if not args.player_id:
            print("❌ player 모드에서는 --as <agent_id>가 필요합니다.")
            print("   예: python main.py --mode player --as merchant_01")
            sys.exit(1)

        from agora.interfaces.cli import PlayerCLI

        try:
            cli = PlayerCLI(sim, args.player_id)
            cli.run()
        except ValueError as e:
            print(f"❌ {e}")
            print(f"   사용 가능한 에이전트: {', '.join(sim.agents_by_id.keys())}")
            sys.exit(1)

    else:  # spectator mode
        sim.run()

    # 사후 인터뷰
    if args.interview:
        from agora.analysis.interview import PostGameInterview, generate_report

        print("\n" + "=" * 50)
        interviewer = PostGameInterview(
            sim,
            human_player_id=args.player_id if args.mode == "player" else None,
        )
        results = interviewer.conduct_interviews(verbose=args.verbose)

        # 마크다운 리포트 생성
        report_path = Path("reports") / f"report_{results['game_id']}.md"
        generate_report(results, str(report_path))
        print(f"📄 리포트 생성: {report_path}")


if __name__ == "__main__":
    main()
