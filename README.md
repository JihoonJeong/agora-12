# Agora-12: AI Agent Social Experiment Simulator

**English** | [한국어](README_KO.md)

A simulation where 12 AI agents survive in a resource-constrained environment while forming social relationships.

## Overview

Agora-12 is the first experiment of the **AI Ludens** project, exploring the question: *"Can AI agents survive in a resource-limited environment?"*

Each agent starts with 100 energy and must survive 50 turns by choosing actions: **trade**, **speak**, **support**, or **rest**. The experiment investigates emergent social behaviors, cooperation patterns, and survival strategies across different LLM models and languages.

## Key Features

- **12 Personas**: Architect, Influencer, Archivist, Merchant, Jester, Citizen, Observer
- **Resource System**: Energy (survival) and Influence (social status)
- **Actions**: Speak, Move, Trade, Support, Whisper
- **Crisis Events**: Drought, Plague, Famine
- **Multi-LLM Support**: Ollama (local), Claude, GPT, Gemini

## Installation

```bash
git clone https://github.com/JihoonJeong/agora-12.git
cd agora-12
pip install -r requirements.txt
```

### Ollama Setup (Local LLM)

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download installer from https://ollama.com/download
# Or via winget:
winget install Ollama.Ollama

# Start server
ollama serve

# Pull models (separate terminal)
ollama pull mistral:7b
ollama pull exaone3.5:7.8b  # Korean bilingual model
```

## Quick Start

```bash
# Mock mode (test without LLM)
python main.py --epochs 10

# Ollama mode
cp config/settings_benchmark.yaml config/settings.yaml
python main.py --epochs 10

# Player mode (participate as an agent)
python main.py --mode player --as merchant_01

# With post-game interview
python main.py --epochs 50
```

## Configuration

Specify adapters and models in `config/settings.yaml`:

```yaml
# Default adapter
default_adapter: ollama    # mock, ollama, anthropic, openai, google
default_model: mistral:latest

# Per-agent override
agents:
  - id: architect_01
    persona: architect
    adapter: anthropic
    model: claude-3-5-sonnet-20241022
```

## Experiment Results

### Round 1 (Fixed Persona Assignment)

| Model | Language | Survival Rate | Platform |
|-------|----------|---------------|----------|
| EXAONE 3.5 7.8B | KO | 58% | Local |
| EXAONE 3.5 7.8B | EN | 50% | Local |
| Mistral 7B | KO | 38% | Local |
| Mistral 7B | EN | 42% | Local |
| Claude Haiku 4.5 | KO | 72% | API |
| Claude Haiku 4.5 | EN | 60% | API |
| Gemini Flash 3 | KO | 30% | API |
| Gemini Flash 3 | EN | 60% | API |

### Round 2 (Random Persona Shuffle)

Fixed crisis seed + randomized persona assignment to decouple persona effects from starting position effects.

| Model | Language | Survival Rate | Platform |
|-------|----------|---------------|----------|
| EXAONE 3.5 7.8B | KO | 45% | Local (Windows) |
| EXAONE 3.5 7.8B | EN | 33% | Local (Windows) |
| Mistral 7B | KO | 32% | Local (Windows) |
| Mistral 7B | EN | 43% | Local (Windows) |

### Key Findings

- **"The Eloquent Extinction"**: AI agents often choose conversation over survival, leading to collective death
- **Language Effect**: Korean prompts generally yield higher survival rates for Korean-trained models (EXAONE)
- **Model Variance**: Claude Haiku shows highest overall survival; Gemini Flash shows high variance between languages

## Data

All experiment data is available in the `data/` directory:

| File | Description |
|------|-------------|
| `agora12_all_epoch_summary.jsonl` | Consolidated epoch summaries (3,000 records) |
| `agora12_all_simulation_log.jsonl` | Consolidated action logs (24,923 records) |

Each record includes metadata: `dataset`, `model`, `language`, `condition`, `run`.

## Project Structure

```
agora-12/
├── agora/
│   ├── core/           # Core simulation logic
│   ├── adapters/       # LLM adapters (mock, ollama, anthropic, etc.)
│   ├── interfaces/     # CLI interface
│   └── analysis/       # Post-game interview module
├── config/             # Configuration files
├── data/               # Experiment data (JSONL)
├── logs/               # Simulation logs
├── reports/            # Interview reports
├── scripts/            # Utility scripts
└── main.py             # Entry point
```

## Benchmark

### Environment Check

```bash
# macOS/Linux
./scripts/setup_ollama.sh

# Windows (PowerShell)
ollama list
curl http://localhost:11434/api/tags
```

### Run Benchmark

```bash
# macOS/Linux
./scripts/benchmark.sh

# Windows
python main.py --config config/settings_exaone_ko.yaml --epochs 50
```

### Expected Duration

| Hardware | Model | 50 Epochs | Notes |
|----------|-------|-----------|-------|
| RTX 4070 Ti (Windows) | EXAONE 3.5 7.8B | ~35 min | Local, GPU |
| RTX 4070 Ti (Windows) | Mistral 7B | ~25 min | Local, GPU |
| MacBook Air M1 | Mistral 7B | 1-2 hours | Local, CPU |
| API (any) | Haiku/Flash | ~10 min | Cloud |

**Notes**:
- Epochs × surviving agents = total LLM calls (max 600 for 50 epochs)
- Interview adds ~17 calls per survivor
- GPU acceleration significantly reduces local model runtime

## Output Files

| File | Description |
|------|-------------|
| `logs/{run_id}/simulation_log.jsonl` | All action logs |
| `logs/{run_id}/epoch_summary.jsonl` | Per-epoch summary |
| `logs/{run_id}/metadata.json` | Run metadata (seed, persona map) |
| `logs/{run_id}/report_*.md` | Interview report |

## Testing

```bash
pytest -v
```

## Team (The Dual Lab)

### Moderator
- **JJ** (Human): Project lead

### Windows Lab
- **Theo** (Claude): Planning, logical design, data interpretation
- **Cas** (Gemini): Behavioral ecology, outlier analysis, red teaming
- **Ray** (Claude Code): Engineering, local model experiments

### Mac Lab
- **Luca** (Claude): Theoretical framework, discussion
- **Gem** (Gemini): Statistical analysis, visualization
- **Cody** (Claude Code): Engineering, API model experiments

## License

MIT
