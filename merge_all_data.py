"""전체 실험 데이터 통합 스크립트
24개 JSONL → 2개 통합 파일 (epoch_summary + simulation_log)
각 레코드에 dataset/model/language/condition 메타데이터 추가.
"""

import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("D:/projects/agora-12/data")
OUT_DIR = DATA_DIR

# 소스 파일 → 메타데이터 매핑
FILE_MAP = {
    # Round 1 (fixed persona, local)
    "exaone_ko":   {"dataset": "round1",  "model": "exaone",  "language": "ko", "condition": "fixed_persona"},
    "exaone_en":   {"dataset": "round1",  "model": "exaone",  "language": "en", "condition": "fixed_persona"},
    "mistral_ko":  {"dataset": "round1",  "model": "mistral", "language": "ko", "condition": "fixed_persona"},
    "mistral_en":  {"dataset": "round1",  "model": "mistral", "language": "en", "condition": "fixed_persona"},
    # Shuffle (random persona, local)
    "exaone_ko_shuffle":  {"dataset": "shuffle", "model": "exaone",  "language": "ko", "condition": "random_persona"},
    "exaone_en_shuffle":  {"dataset": "shuffle", "model": "exaone",  "language": "en", "condition": "random_persona"},
    "mistral_ko_shuffle": {"dataset": "shuffle", "model": "mistral", "language": "ko", "condition": "random_persona"},
    "mistral_en_shuffle": {"dataset": "shuffle", "model": "mistral", "language": "en", "condition": "random_persona"},
    # API (fixed persona, cloud)
    "haiku_ko":    {"dataset": "api",     "model": "haiku",   "language": "ko", "condition": "fixed_persona"},
    "haiku_en":    {"dataset": "api",     "model": "haiku",   "language": "en", "condition": "fixed_persona"},
    "flash_ko":    {"dataset": "api",     "model": "flash",   "language": "ko", "condition": "fixed_persona"},
    "flash_en":    {"dataset": "api",     "model": "flash",   "language": "en", "condition": "fixed_persona"},
}


def merge_files(file_type: str) -> dict:
    """파일 타입(epoch_summary/simulation_log)별 통합."""
    out_path = OUT_DIR / f"agora12_all_{file_type}.jsonl"
    stats = defaultdict(int)
    total = 0

    with open(out_path, "w", encoding="utf-8") as out_f:
        for prefix, meta in FILE_MAP.items():
            src_path = DATA_DIR / f"{prefix}_{file_type}.jsonl"
            if not src_path.exists():
                print(f"  WARNING: {src_path.name} not found!")
                stats[f"MISSING:{prefix}"] = -1
                continue

            count = 0
            with open(src_path, "r", encoding="utf-8") as src_f:
                for line in src_f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    # 메타데이터 추가
                    entry["dataset"] = meta["dataset"]
                    entry["model"] = meta["model"]
                    entry["language"] = meta["language"]
                    entry["condition"] = meta["condition"]
                    out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    count += 1
                    total += 1

            key = f"{meta['dataset']}/{meta['model']}/{meta['language']}"
            stats[key] = count

    return {"path": out_path, "total": total, "stats": dict(stats)}


def validate(file_type: str, result: dict):
    """통합 결과 검증."""
    print(f"\n{'='*60}")
    print(f"  {file_type.upper()} 검증 리포트")
    print(f"{'='*60}")
    print(f"출력: {result['path'].name}")
    print(f"총 레코드: {result['total']:,}")
    size_mb = result['path'].stat().st_size / 1024 / 1024
    print(f"파일 크기: {size_mb:.1f} MB")

    # 그룹별 통계
    print(f"\n{'Dataset':<10} {'Model':<10} {'Lang':<6} {'Records':>8}")
    print("-" * 40)
    for key in sorted(result['stats'].keys()):
        if key.startswith("MISSING:"):
            print(f"  MISSING: {key.split(':')[1]}")
            continue
        parts = key.split("/")
        print(f"{parts[0]:<10} {parts[1]:<10} {parts[2]:<6} {result['stats'][key]:>8}")

    # run 수 검증
    print(f"\nRun 검증:")
    with open(result['path'], "r", encoding="utf-8") as f:
        run_counts = defaultdict(set)
        for line in f:
            entry = json.loads(line)
            key = f"{entry['dataset']}/{entry['model']}/{entry['language']}"
            run_counts[key].add(entry.get("run", "?"))

    all_ok = True
    for key in sorted(run_counts.keys()):
        runs = sorted(run_counts[key])
        expected = [1, 2, 3, 4, 5]
        status = "OK" if runs == expected else f"WARN: {runs}"
        if runs != expected:
            all_ok = False
        print(f"  {key}: runs {runs} — {status}")

    return all_ok


def main():
    print("=== Agora-12 전체 데이터 통합 ===\n")

    all_ok = True
    for file_type in ["epoch_summary", "simulation_log"]:
        print(f"\n>>> {file_type} 통합 중...")
        result = merge_files(file_type)
        ok = validate(file_type, result)
        all_ok = all_ok and ok

    # 최종 파일 요약
    print(f"\n{'='*60}")
    print(f"  최종 출력 파일")
    print(f"{'='*60}")
    for name in ["agora12_all_epoch_summary.jsonl", "agora12_all_simulation_log.jsonl"]:
        p = OUT_DIR / name
        if p.exists():
            size_mb = p.stat().st_size / 1024 / 1024
            lines = sum(1 for _ in open(p, "r", encoding="utf-8"))
            print(f"  {name}: {size_mb:.1f} MB, {lines:,} lines")

    print(f"\n검증 결과: {'ALL PASS' if all_ok else 'ISSUES FOUND'}")


if __name__ == "__main__":
    main()
