"""Round 2 풀 실험 오케스트레이터
4 조건 × 5 runs = 20 runs
- EXAONE KO/EN + Mistral KO/EN
- random_seed: 42, persona_assignment: random
- 인터뷰 포함
"""

import subprocess
import sys
import time
from datetime import datetime

CONDITIONS = [
    ("EXAONE KO", "config/settings_exaone_ko.yaml"),
    ("EXAONE EN", "config/settings_exaone_en.yaml"),
    ("Mistral KO", "config/settings_mistral_ko.yaml"),
    ("Mistral EN", "config/settings_mistral_en.yaml"),
]

RUNS_PER_CONDITION = 5


def run_experiment(label: str, config_path: str, run_num: int) -> dict:
    """단일 실험 실행"""
    start = time.time()
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {label} - Run {run_num}/5 시작")
    print(f"{'='*60}")

    result = subprocess.run(
        [sys.executable, "-X", "utf8", "main.py",
         "--config", config_path],
        capture_output=False,
        text=True,
    )

    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    status = "SUCCESS" if result.returncode == 0 else f"FAIL (code {result.returncode})"

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {label} Run {run_num} - {status} ({minutes}m {seconds}s)")
    return {"label": label, "run": run_num, "status": status, "elapsed": elapsed}


def main():
    total_start = time.time()
    results = []
    total_runs = len(CONDITIONS) * RUNS_PER_CONDITION
    current = 0

    print(f"{'='*60}")
    print(f"Agora-12 Round 2 풀 실험")
    print(f"조건: {len(CONDITIONS)}개, 각 {RUNS_PER_CONDITION}회 = 총 {total_runs} runs")
    print(f"시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    for label, config_path in CONDITIONS:
        for run_num in range(1, RUNS_PER_CONDITION + 1):
            current += 1
            print(f"\n>>> 진행률: {current}/{total_runs}")
            result = run_experiment(label, config_path, run_num)
            results.append(result)

    # 최종 요약
    total_elapsed = time.time() - total_start
    total_min = int(total_elapsed // 60)
    total_sec = int(total_elapsed % 60)

    print(f"\n{'='*60}")
    print(f"Round 2 풀 실험 완료")
    print(f"총 소요: {total_min}m {total_sec}s")
    print(f"{'='*60}")
    print(f"\n{'Label':<15} {'Run':<5} {'Status':<15} {'Time':<10}")
    print("-" * 45)
    for r in results:
        m = int(r['elapsed'] // 60)
        s = int(r['elapsed'] % 60)
        print(f"{r['label']:<15} {r['run']:<5} {r['status']:<15} {m}m {s}s")

    success = sum(1 for r in results if r['status'] == 'SUCCESS')
    print(f"\n성공: {success}/{total_runs}")


if __name__ == "__main__":
    main()
