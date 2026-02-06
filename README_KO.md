# Agora-12: AI 에이전트 사회 실험 시뮬레이터

[English](README.md) | **한국어**

12명의 AI 에이전트가 제한된 자원 환경에서 생존하며 사회적 관계를 형성하는 시뮬레이션입니다.

## 특징

- **12명의 페르소나**: Architect, Influencer, Archivist, Merchant, Jester, Citizen, Observer
- **자원 시스템**: 에너지 (생존), 영향력 (사회적 지위)
- **다양한 행동**: 발언, 이동, 거래, 지지, 귓속말
- **위기 이벤트**: 가뭄, 역병, 기근
- **LLM 지원**: Ollama (로컬), Claude, GPT, Gemini

## 설치

```bash
git clone https://github.com/JihoonJeong/agora-12.git
cd agora-12
pip install -r requirements.txt
```

### Ollama 설치 (로컬 LLM)

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# https://ollama.com/download 에서 설치 또는:
winget install Ollama.Ollama

# 서버 시작
ollama serve

# 모델 다운로드 (별도 터미널)
ollama pull mistral:7b
ollama pull exaone3.5:7.8b  # 한국어 지원 모델
```

## 빠른 시작

```bash
# Mock 모드 (LLM 없이 테스트)
python main.py --epochs 10

# Ollama 모드
cp config/settings_benchmark.yaml config/settings.yaml
python main.py --epochs 10

# 플레이어 참여
python main.py --mode player --as merchant_01

# 사후 인터뷰 포함
python main.py --epochs 50 --interview
```

## 설정

`config/settings.yaml`에서 어댑터와 모델을 지정합니다:

```yaml
# 기본 어댑터
default_adapter: ollama    # mock, ollama, anthropic, openai, google
default_model: mistral:latest

# 에이전트별 개별 지정 가능
agents:
  - id: architect_01
    persona: architect
    adapter: anthropic
    model: claude-3-5-sonnet-20241022
```

## 실험 결과

### Round 1 (고정 페르소나)

| 모델 | 언어 | 생존율 | 비고 |
|------|------|--------|------|
| EXAONE 3.5 7.8B | KO | 58% | 로컬 |
| EXAONE 3.5 7.8B | EN | 50% | 로컬 |
| Mistral 7B | KO | 38% | 로컬 |
| Mistral 7B | EN | 42% | 로컬 |
| Claude Haiku 4.5 | KO | 72% | API |
| Claude Haiku 4.5 | EN | 60% | API |
| Gemini Flash 3 | KO | 30% | API |
| Gemini Flash 3 | EN | 60% | API |

### Round 2 (랜덤 페르소나 셔플)

Crisis seed 고정 + 페르소나 랜덤 배정으로 페르소나 효과와 시작 위치 효과를 분리.

| 모델 | 언어 | 생존율 | 비고 |
|------|------|--------|------|
| EXAONE 3.5 7.8B | KO | 45% | 로컬 (Windows) |
| EXAONE 3.5 7.8B | EN | 33% | 로컬 (Windows) |
| Mistral 7B | KO | 32% | 로컬 (Windows) |
| Mistral 7B | EN | 43% | 로컬 (Windows) |

## 벤치마크

### 환경 확인

```bash
./scripts/setup_ollama.sh
```

### 단계별 실행

```bash
./scripts/benchmark.sh
```

### 예상 소요 시간

| 하드웨어 | 모델 | 50 에폭 | 비고 |
|----------|------|---------|------|
| RTX 4070 Ti (Windows) | EXAONE 3.5 7.8B | ~35분 | 로컬, GPU |
| RTX 4070 Ti (Windows) | Mistral 7B | ~25분 | 로컬, GPU |
| MacBook Air M1 | Mistral 7B | 1-2시간 | 로컬, CPU |
| API (any) | Haiku/Flash | ~10분 | 클라우드 |

**참고**:
- 에폭당 호출 수 = 생존 에이전트 수 (최대 12명 × 50 = 600 호출)
- 인터뷰는 생존자 × 17문항 추가 호출
- GPU 가속 시 로컬 모델 실행 시간 대폭 단축

### Crisis 테스트 설정

벤치마크용 설정 (`config/settings_benchmark.yaml`):

```yaml
crisis:
  start_after_epoch: 10   # 기본 30 → 10
  probability: 0.3        # 기본 0.1 → 0.3 (30%)
```

## 프로젝트 구조

```
agora-12/
├── agora/
│   ├── core/           # 핵심 시뮬레이션 로직
│   ├── adapters/       # LLM 어댑터 (mock, ollama, anthropic, etc.)
│   ├── interfaces/     # CLI 인터페이스
│   └── analysis/       # 사후 인터뷰 모듈
├── config/
│   ├── settings.yaml           # 메인 설정
│   └── settings_benchmark.yaml # 벤치마크용 설정
├── scripts/
│   ├── setup_ollama.sh   # 환경 확인 스크립트
│   └── benchmark.sh      # 단계별 벤치마크
├── data/               # 실험 데이터 (JSONL)
├── logs/               # 시뮬레이션 로그
├── reports/            # 인터뷰 리포트
└── main.py             # 진입점
```

## 출력 파일

| 파일 | 설명 |
|------|------|
| `logs/simulation_log.jsonl` | 모든 행동 로그 |
| `logs/epoch_summary.jsonl` | 에폭별 요약 |
| `reports/game_{timestamp}.json` | 인터뷰 결과 (JSON) |
| `reports/report_{timestamp}.md` | 인터뷰 리포트 (Markdown) |

## 테스트

```bash
pytest -v
```

## 문서

- [Phase 1 완료 리포트](docs/progress/phase1-complete.md)
- [Phase 2 완료 리포트](docs/progress/phase2-complete.md)
- [Phase 3 완료 리포트](docs/progress/phase3-complete.md)

## 기획

이 프로젝트는 Claude와 Gemini의 공동 기획으로 진행되었습니다.

## 라이선스

MIT
