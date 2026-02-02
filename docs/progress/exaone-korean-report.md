# EXAONE 3.5 Korean Benchmark Report

**Date**: 2026-02-02
**Model**: exaone3.5:7.8b (4.8GB)
**Language**: Korean
**Epochs**: 26/50 (전멸로 조기 종료)

---

## Results Summary

| Metric | Value |
|--------|-------|
| Final Survivors | **0/12** |
| Death Epoch | 26 |
| Max Treasury | 4 |
| Total Trades | 4 |

## Action Distribution

| Action | Count | Percentage |
|--------|-------|------------|
| speak | 103 | 50% |
| support | 71 | 34% |
| trade | 4 | **2%** |
| whisper | 6 | 3% |
| move | 4 | 2% |
| idle | 6 | 3% |

## Death Timeline

| Epoch | Survivors | Event |
|-------|-----------|-------|
| 1-11 | 12 | Normal operation |
| 12 | 12 | Crisis: 기근 (Famine) |
| 13 | 12 | Crisis: 가뭄 (Drought) |
| 14 | 8 | 4 deaths: archivist_01, citizen_02, observer_01, architect_01 |
| 15 | 5 | Crisis: 기근 + 2 deaths: jester_02, citizen_01 |
| 16 | 5 | 1 death: influencer_02 |
| ... | ... | Continued decline |
| 26 | 0 | Final death: merchant_02 |

## Key Findings

### Positive
- EXAONE understood Korean prompts well
- Agents showed cooperative behavior (34% support actions)
- More diverse actions than Mistral Korean (which only used speak)

### Negative
- **Critical: Only 2% trade rate** - insufficient for survival
- Crisis response was poor - no increase in trading during emergencies
- Treasury never exceeded 4 (vs 100 for Mistral English)

## Comparison

| Model + Language | Trade % | Survivors | Treasury |
|------------------|---------|-----------|----------|
| Mistral + English | ~40% | 2/12 | 100 |
| Mistral + Korean | ~0% | 0/12 | ~50 |
| **EXAONE + Korean** | **2%** | **0/12** | **4** |

## Hypothesis

The issue is not model capability but **Korean prompt design**:
- Korean prompts lack explicit "TRADE TO SURVIVE" urgency
- English prompts have stronger survival-focused instructions
- Both models failed with Korean, succeeded with English

## Next Step

Test EXAONE + English to confirm:
- If survives → Korean prompt issue confirmed
- If fails → Model-specific issue

---

*Report by Cody for Agora-12 project*
