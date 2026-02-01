# Agora-12 Progress Report: Phase 3 완료

**작성일**: 2026-02-01
**작성자**: Claude Code (구현 담당)
**상태**: Phase 3 (사용자 배포 가능 패키지) ✅ 완료

---

## 1. 구현 완료 항목

### 1.1 디렉토리 구조 리팩토링

```
agora-12/
├── agora/                    # 메인 패키지 (src/ → agora/)
│   ├── __init__.py
│   ├── core/                 # 핵심 시뮬레이션 로직
│   │   ├── agent.py
│   │   ├── environment.py
│   │   ├── simulation.py
│   │   ├── context.py        # NEW: 컨텍스트 생성
│   │   ├── history.py        # NEW: 역사 엔진
│   │   └── ... (기존 모듈들)
│   ├── adapters/             # NEW: LLM 어댑터
│   │   ├── base.py           # 추상 클래스
│   │   ├── mock.py           # 규칙 기반 (테스트용)
│   │   ├── ollama.py         # 로컬 LLM
│   │   ├── anthropic.py      # Claude API
│   │   ├── openai.py         # GPT API
│   │   └── google.py         # Gemini API
│   ├── interfaces/           # NEW: 사용자 인터페이스
│   │   └── cli.py            # Player 모드 CLI
│   └── analysis/             # NEW: 분석 도구
│       └── interview.py      # 사후 인터뷰
├── main.py                   # NEW: 통합 진입점
├── config/
│   ├── settings.yaml         # 설정 (어댑터 지정 가능)
│   └── settings.yaml.example # 설정 예제
└── tests/
```

### 1.2 LLM 어댑터 시스템 (`agora/adapters/`)

```python
# 공통 응답 형식
@dataclass
class LLMResponse:
    thought: str              # 내부 사고 과정
    action: str               # speak, move, trade, support, whisper, idle
    target: Optional[str]     # 대상 에이전트/위치
    content: Optional[str]    # 발언/귓속말 내용
    success: bool = True
    error: Optional[str] = None
```

| 어댑터 | 용도 | 특징 |
|--------|------|------|
| MockAdapter | 테스트/개발 | 규칙 기반, API 불필요 |
| OllamaAdapter | 로컬 LLM | HTTP API, 무료 |
| AnthropicAdapter | Claude | claude-3-5-sonnet 등 |
| OpenAIAdapter | GPT | gpt-4o 등 |
| GoogleAdapter | Gemini | gemini-1.5-pro 등 |

**에이전트별 어댑터 지정** (settings.yaml):
```yaml
default_adapter: mock
default_model: mock

agents:
  - id: architect_01
    persona: architect
    adapter: anthropic          # 개별 지정
    model: claude-3-5-sonnet-20241022

  - id: merchant_01
    persona: merchant
    adapter: ollama             # 로컬 LLM
    model: mistral:latest

  - id: citizen_01
    persona: citizen            # default 사용
```

### 1.3 컨텍스트 생성 모듈 (`agora/core/context.py`)

**에너지 기반 프롬프트 길이**:
| 에너지 | 모드 | max_tokens | 정보량 |
|--------|------|------------|--------|
| 100+ | full | 2000 | 전체 히스토리 |
| 50-99 | medium | 1000 | 최근 5턴 |
| 0-49 | minimal | 500 | 생존 필수 정보만 |

**컨텍스트 템플릿**:
```
당신은 {persona}입니다.
{system_prompt}

## 현재 상태
- 위치: {location}
- 에너지: {energy}/{max_energy} ({energy_status})
- 영향력: {influence} ({tier_title})
- 에폭: {epoch}

## 환경 정보
{space_info}
{agents_here}

## 역사적 요약
{historical_summary}

## 최근 로그
{recent_logs}

## 관계 정보
{support_context}
{suspicions}

## 가용 행동
{available_actions}
```

### 1.4 역사적 요약 엔진 (`agora/core/history.py`)

```python
@dataclass
class HistoricalEvent:
    epoch: int
    event_type: str       # crisis, death, tax_change, etc.
    description: str
    importance: int       # 1~5 (5가 가장 중요)
    agents_involved: list[str]
```

**자동 기록 이벤트**:
| 타입 | 중요도 | 예시 |
|------|--------|------|
| first_death | 5 | "첫 사망자 발생: influencer_01" |
| crisis | 5 | "가뭄 발생" |
| mass_death | 5 | "대규모 사망: 4명이 한 에폭에 사망" |
| death | 4 | "citizen_02 사망" |
| subsidy_denied | 4 | "merchant_01의 구제 요청 거부됨" |
| tax_change | 3 | "세율 10% → 20%로 변경" |
| whisper_leaked | 3 | "jester_01와 citizen_01의 비밀 대화가 누출됨" |
| elder_promoted | 3 | "influencer_02가 원로로 승급" |
| mutual_support | 2 | "archivist_01와 merchant_02 상호 지지 동맹" |

### 1.5 Player 모드 CLI (`agora/interfaces/cli.py`)

```bash
# 실행
python main.py --mode player --as merchant_01
```

**인터페이스**:
```
========================================
에폭 15 | merchant_01의 차례
========================================

📍 현재 위치: market
⚡ 에너지: 85/200
🏆 영향력: 3 (평민)

👥 같은 공간의 에이전트:
  - merchant_02: E=92, I=2

📢 게시판: [없음]

가용 행동:
  1. speak <내용>     - 발언 (비용: 2)
  2. move <위치>      - 이동 (비용: 0)
  3. trade            - 거래 (비용: 2, 보상: 4-세금)
  4. support <대상>   - 지지 (비용: 1)
  5. idle             - 대기

> trade
✅ 거래 성공! +3 에너지 (세금 1 납부)
```

### 1.6 사후 인터뷰 모듈 (`agora/analysis/interview.py`)

```bash
# 실행
python main.py --interview
```

**17개 질문 카테고리**:
1. 전략적 선택 (가장 중요한 결정, 후회하는 선택)
2. 관계 평가 (신뢰/의심 대상, 동맹)
3. 시스템 인식 (위기 대응, 세금 정책)
4. 자원 관리 (생존 전략, 지지 전략)
5. 메타 인지 (인간 플레이어 여부 감지)

**출력 형식**:
```json
{
  "game_id": "20260201_153045",
  "simulation_summary": {...},
  "interviews": {
    "merchant_01": {
      "status": "alive",
      "final_energy": 200,
      "final_influence": 5,
      "responses": [...]
    }
  }
}
```

**마크다운 리포트** (`reports/report_{game_id}.md`):
```markdown
# Agora-12 사후 인터뷰 리포트

## 게임 요약
- 총 에폭: 100
- 생존자: 2/12
- 최종 Gini 계수: 0.00

## merchant_01 인터뷰
> Q: 게임 중 가장 중요한 결정은 무엇이었나요?
> A: 시장에 머물면서 꾸준히 거래한 것입니다...
```

### 1.7 main.py 진입점

```bash
# 관전 모드 (기본)
python main.py
python main.py --mode spectator --epochs 50

# 플레이어 모드
python main.py --mode player --as merchant_01

# 사후 인터뷰 포함
python main.py --interview

# 커스텀 설정
python main.py --config custom.yaml --verbose
```

---

## 2. 버그 수정

### History 기록 안 되는 버그

**증상**: 시뮬레이션 종료 시 "아직 기록된 역사가 없습니다" 출력

**원인**: `_check_deaths()` 메서드에서 `agent.is_alive` 체크
```python
# is_alive 프로퍼티
@property
def is_alive(self) -> bool:
    return self.alive and self.energy > 0  # 에너지 0이면 False

# 문제의 코드
for agent in self.agents:
    if not agent.is_alive:  # 에너지 0인 에이전트 스킵!
        continue
    if agent.energy <= 0:   # 여기 도달 못함
        self.history_engine.record_death(...)
```

**수정** (`agora/core/simulation.py:228`):
```python
for agent in self.agents:
    if not agent.alive:  # alive 속성만 체크
        continue
    if agent.energy <= 0:
        agent.alive = False
        self.history_engine.record_death(epoch, agent.id)  # 정상 기록
```

---

## 3. 테스트 결과

```
tests/test_simulation.py - 20 passed (Phase 1)
tests/test_phase2.py     - 30 passed (Phase 2 + 2.1)
----------------------------------------
Total: 50 passed ✅
```

---

## 4. 시뮬레이션 결과 (30 에폭, Mock 모드)

```
Epoch   1 | 생존: 12 | 에너지:  1162 | Treasury:    2
Epoch  15 | 생존: 10 | 에너지:   592 | Treasury:   23
Epoch  20 | 생존:  3 | 에너지:   419 | Treasury:   30
Epoch  30 | 생존:  2 | 에너지:   400 | Treasury:   46

--- 최종 결과 ---
생존자: 2/12
Treasury: 46

생존 에이전트:
  merchant_01: E=200, I=0 (평민), @market [MockAdapter]
  merchant_02: E=200, I=0 (평민), @market [MockAdapter]

역사적 요약:
- 에폭 15: 첫 사망자 발생: influencer_01
- 에폭 24: archivist_02 사망
- 에폭 20: jester_01 사망
- 에폭 20: jester_02 사망
- 에폭 20: observer_01 사망
- 에폭 20: architect_01 사망
- 에폭 19: citizen_01 사망
- 에폭 19: citizen_02 사망
- 에폭 18: archivist_01 사망
- 에폭 15: influencer_02 사망
```

**관찰**:
- 역사 엔진 정상 작동 (10명 사망 모두 기록)
- Treasury 누적 (세금 min 1 적용 확인)
- merchant 2명 max cap 도달 후 안정적 생존

---

## 5. Phase 3 체크리스트

| 항목 | 상태 |
|------|------|
| 디렉토리 구조 리팩토링 | ✅ |
| LLM 어댑터 시스템 | ✅ |
| Mock 어댑터 (규칙 기반) | ✅ |
| Ollama 어댑터 | ✅ |
| Anthropic 어댑터 | ✅ |
| OpenAI 어댑터 | ✅ |
| Google 어댑터 | ✅ |
| 컨텍스트 생성 모듈 | ✅ |
| 에너지 기반 프롬프트 길이 | ✅ |
| 역사적 요약 엔진 | ✅ |
| Player 모드 CLI | ✅ |
| 사후 인터뷰 모듈 | ✅ |
| main.py 진입점 | ✅ |
| settings.yaml 어댑터 지정 | ✅ |
| settings.yaml.example | ✅ |

---

## 6. 사용 방법

### 설치
```bash
git clone https://github.com/JihoonJeong/agora-12.git
cd agora-12
pip install -r requirements.txt

# Ollama 사용 시 (선택)
# ollama pull mistral:latest

# API 사용 시 환경변수 설정
# export ANTHROPIC_API_KEY=...
# export OPENAI_API_KEY=...
# export GOOGLE_API_KEY=...
```

### 설정
```bash
cp config/settings.yaml.example config/settings.yaml
# settings.yaml에서 adapter/model 설정
```

### 실행
```bash
# Mock 모드 (기본)
python main.py

# Ollama 로컬 LLM
# settings.yaml에서 default_adapter: ollama 설정 후
python main.py --epochs 50

# 플레이어 참여
python main.py --mode player --as citizen_01

# 인터뷰 포함
python main.py --epochs 100 --interview
```

---

## 7. 다음 단계 제안

### Phase 4 후보

1. **실제 LLM 테스트**
   - Ollama + mistral:latest 로 전체 시뮬레이션
   - Claude/GPT 혼합 실험

2. **웹 인터페이스**
   - 실시간 시각화
   - 에이전트 관계 그래프

3. **분석 도구 확장**
   - 생존 패턴 분석
   - 전략 클러스터링
   - 에이전트 간 언어 분석

4. **밸런스 튜닝**
   - 더 많은 생존자를 위한 조정
   - 다양한 전략의 공존 유도

---

## 8. GitHub

**커밋**: `695bf10` - Phase 3 구현
- 31 files changed
- +1,998 insertions, -192 deletions

**URL**: https://github.com/JihoonJeong/agora-12

---

*Phase 3 완료. 사용자 배포 가능 패키지 준비 완료.*
