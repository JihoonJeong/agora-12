"""Round 2 데이터 병합 스크립트
각 조건(모델×언어)별 5 runs를 하나의 JSONL로 합침.
기존 data/ 형식과 동일: run, run_id, operator 필드 추가.
이름에 'shuffle' 포함하여 Round 2 특성(persona 랜덤 배정) 표시.
"""

import json
from pathlib import Path
from collections import defaultdict

LOGS_DIR = Path("D:/projects/agora-12/logs")
DATA_DIR = Path("D:/projects/agora-12/data")

# Round 2 풀 런만 선별 (50 epochs, persona_assignment=random)
ROUND2_RUNS = {
    "exaone_ko": [
        "exaone3.5-7.8b_ko_20260205-013434",
        "exaone3.5-7.8b_ko_20260205-021111",
        "exaone3.5-7.8b_ko_20260205-024802",
        "exaone3.5-7.8b_ko_20260205-032750",
        "exaone3.5-7.8b_ko_20260205-040422",
    ],
    "exaone_en": [
        "exaone3.5-7.8b_en_20260205-044502",
        "exaone3.5-7.8b_en_20260205-051703",
        "exaone3.5-7.8b_en_20260205-054435",
        "exaone3.5-7.8b_en_20260205-061718",
        "exaone3.5-7.8b_en_20260205-064444",
    ],
    "mistral_ko": [
        "mistral-7b_ko_20260205-071508",
        "mistral-7b_ko_20260205-074442",
        "mistral-7b_ko_20260205-081131",
        "mistral-7b_ko_20260205-083356",
        "mistral-7b_ko_20260205-090052",
    ],
    "mistral_en": [
        "mistral-7b_en_20260205-092723",
        "mistral-7b_en_20260205-095241",
        "mistral-7b_en_20260205-101838",
        "mistral-7b_en_20260205-104557",
        "mistral-7b_en_20260205-111605",
    ],
}

OPERATOR = "ray"


def merge_jsonl(condition: str, run_ids: list[str], file_type: str) -> int:
    """JSONL 파일들을 합침. run/run_id/operator 필드 추가."""
    filename_map = {
        "epoch_summary": "epoch_summary.jsonl",
        "simulation_log": "simulation_log.jsonl",
    }
    src_filename = filename_map[file_type]
    out_filename = f"{condition}_shuffle_{file_type}.jsonl"
    out_path = DATA_DIR / out_filename

    total_lines = 0
    with open(out_path, "w", encoding="utf-8") as out_f:
        for run_num, run_id in enumerate(run_ids, 1):
            src_path = LOGS_DIR / run_id / src_filename
            if not src_path.exists():
                print(f"  WARNING: {src_path} not found, skipping")
                continue

            with open(src_path, "r", encoding="utf-8") as src_f:
                for line in src_f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    entry["run"] = run_num
                    entry["run_id"] = run_id
                    entry["operator"] = OPERATOR
                    out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    total_lines += 1

    return total_lines


def main():
    DATA_DIR.mkdir(exist_ok=True)

    print("=== Round 2 데이터 병합 ===\n")

    for condition, run_ids in ROUND2_RUNS.items():
        print(f"{condition}:")
        for file_type in ["epoch_summary", "simulation_log"]:
            count = merge_jsonl(condition, run_ids, file_type)
            out_name = f"{condition}_shuffle_{file_type}.jsonl"
            print(f"  {out_name}: {count} lines")
        print()

    # 생성된 파일 목록
    print("=== 생성된 파일 ===")
    for f in sorted(DATA_DIR.glob("*shuffle*")):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
