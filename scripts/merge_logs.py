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
    "haiku_en": [
        "claude-haiku-4-5-20251001_en_20260204-093801",
        "claude-haiku-4-5-20251001_en_20260204-112446",
        "claude-haiku-4-5-20251001_en_20260204-123232",
        "claude-haiku-4-5-20251001_en_20260204-140256",
        "claude-haiku-4-5-20251001_en_20260204-140600",
    ],
    "haiku_ko": [
        "claude-haiku-4-5-20251001_ko_20260204-101752",
        "claude-haiku-4-5-20251001_ko_20260204-131916",
        "claude-haiku-4-5-20251001_ko_20260204-143144",
        "claude-haiku-4-5-20251001_ko_20260204-153240",
        "claude-haiku-4-5-20251001_ko_20260204-162405",
    ],
    "flash_en": [
        "gemini-3-flash-preview_en_20260204-231450",
        "gemini-3-flash-preview_en_20260205-003843",
        "gemini-3-flash-preview_en_20260205-082505",
        "gemini-3-flash-preview_en_20260205-100330",
        "gemini-3-flash-preview_en_20260205-113610",
    ],
    "flash_ko": [
        "gemini-3-flash-preview_ko_20260205-000653",
        "gemini-3-flash-preview_ko_20260205-074451",
        "gemini-3-flash-preview_ko_20260205-091155",
        "gemini-3-flash-preview_ko_20260205-104528",
        "gemini-3-flash-preview_ko_20260205-124442",
    ],
}

for group_name, run_dirs in GROUPS.items():
    epoch_records = []
    sim_records = []

    for run_idx, run_dir in enumerate(run_dirs, 1):
        run_path = LOGS_DIR / run_dir
        # Determine operator: Cody's EXAONE runs are 20260203, Ray's are 20260204
        # All haiku runs are Cody's, all mistral runs are Ray's
        if "claude-haiku" in run_dir or "gemini-3-flash" in run_dir:
            operator = "cody"
        elif "mistral" in run_dir:
            operator = "ray"
        elif "20260203" in run_dir and "exaone" in run_dir:
            operator = "cody"
        else:
            operator = "ray"

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
