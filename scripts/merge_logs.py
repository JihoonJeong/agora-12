"""Merge experiment logs by model+language into single JSONL files."""
import json
from pathlib import Path

LOGS_DIR = Path("logs")
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

GROUPS = {
    "exaone_en": [
        "exaone3.5-7.8b_en_20260203-120209",
        "exaone3.5-7.8b_en_20260203-232315",
        "exaone3.5-7.8b_en_20260204-103310",
        "exaone3.5-7.8b_en_20260204-121001",
        "exaone3.5-7.8b_en_20260204-132107",
    ],
    "exaone_ko": [
        "exaone3.5-7.8b_ko_20260203-014802",
        "exaone3.5-7.8b_ko_20260203-172425",
        "exaone3.5-7.8b_ko_20260204-111736",
        "exaone3.5-7.8b_ko_20260204-124925",
        "exaone3.5-7.8b_ko_20260204-140213",
    ],
    "mistral_en": [
        "mistral-7b_en_20260203-190004",
        "mistral-7b_en_20260203-203316",
        "mistral-7b_en_20260203-215007",
        "mistral-7b_en_20260203-235602",
        "mistral-7b_en_20260204-011321",
    ],
    "mistral_ko": [
        "mistral-7b_ko_20260203-195835",
        "mistral-7b_ko_20260203-210736",
        "mistral-7b_ko_20260203-225737",
        "mistral-7b_ko_20260204-003408",
        "mistral-7b_ko_20260204-080129",
    ],
}

for group_name, run_dirs in GROUPS.items():
    epoch_records = []
    sim_records = []

    for run_idx, run_dir in enumerate(run_dirs, 1):
        run_path = LOGS_DIR / run_dir
        lab = "mac" if "20260203" in run_dir and "exaone" in run_dir else "windows"
        # Cody's EXAONE runs are 20260203, Ray's are 20260204
        operator = "cody" if lab == "mac" else "ray"

        # epoch_summary
        ep_file = run_path / "epoch_summary.jsonl"
        if ep_file.exists():
            with open(ep_file, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    record["run"] = run_idx
                    record["run_id"] = run_dir
                    record["operator"] = operator
                    epoch_records.append(record)

        # simulation_log
        sim_file = run_path / "simulation_log.jsonl"
        if sim_file.exists():
            with open(sim_file, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    record["run"] = run_idx
                    record["run_id"] = run_dir
                    record["operator"] = operator
                    sim_records.append(record)

    # Write merged files
    ep_out = OUTPUT_DIR / f"{group_name}_epoch_summary.jsonl"
    with open(ep_out, "w", encoding="utf-8") as f:
        for r in epoch_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    sim_out = OUTPUT_DIR / f"{group_name}_simulation_log.jsonl"
    with open(sim_out, "w", encoding="utf-8") as f:
        for r in sim_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{group_name}: {len(epoch_records)} epoch records, {len(sim_records)} sim records -> {ep_out}, {sim_out}")

print(f"\nDone. Merged files in {OUTPUT_DIR}/")
