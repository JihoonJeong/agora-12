# Agora-12 Progress Report: Phase 2 완료

**작성일**: 2026-02-01
**작성자**: Claude Code (구현 담당)
**상태**: Phase 2 (상호작용 시스템) ✅ 완료

---

## 1. 구현 완료 항목

### 1.1 Support 시스템 (`src/support.py`)
```python
# 비용/보상
giver_cost: 1 energy
receiver_reward: 2 energy + 1 influence

# 추적 기능
- get_supporters(agent_id): 나를 지지한 에이전트
- get_supported(agent_id): 내가 지지한 에이전트
- get_mutual_supporters(): 상호 지지 관계
- get_support_context(): 프롬프트용 컨텍스트
```

### 1.2 Whisper 누출 시스템 (`src/whisper.py`)
```python
base_leak_probability: 0.15  # 15%
observer_bonus: 0.35         # Observer 있으면 +35% → 50%

# 누출 시
- 같은 공간의 다른 에이전트에게 "심증" 전달
- Agent.suspicions 리스트에 기록
```

### 1.3 시장 에너지 풀 (`src/market.py`)
```python
spawn_per_epoch: 25
distribution: activity_weighted

# 분배 로직
1. 거래 안 한 에이전트: min_presence_reward (2)
2. 남은 풀: 거래 횟수 비례 분배
```

### 1.4 Treasury 시스템
```python
overflow_threshold: 100
# 100 초과 시 → 시장 풀로 이동
```

### 1.5 영향력 계급 (`src/influence.py`)
| 계급 | 영향력 | 칭호 | 특권 |
|------|--------|------|------|
| commoner | 0-4 | 평민 | - |
| notable | 5-9 | 유력자 | speak_weight_bonus |
| elder | 10+ | 원로 | contest_architect |

### 1.6 Crisis 이벤트 (`src/crisis.py`)
```python
start_after_epoch: 30
probability: 0.1  # 10%
extra_decay: 5
duration: 1 epoch

# 이벤트 타입
- drought (가뭄)
- plague (역병)
- famine (기근)
```

### 1.7 건축가 스킬 (`src/architect.py`)
| 스킬 | 비용 | 효과 |
|------|------|------|
| build_billboard | 10 energy | 공지 게시 (1 에폭) |
| adjust_tax | 5 energy | 세율 조절 (0~30%) |
| grant_subsidy | Treasury | 에이전트에게 에너지 지급 |

### 1.8 Decay 가속
```python
decay = base(5) + floor(epoch/10) * acceleration(0.5)
# epoch 1-9: 5
# epoch 10-19: 5.5
# epoch 20-29: 6
# ...
```

### 1.9 Reasoning 로깅
```json
{
  "thought": "에너지가 부족하여 support를 요청하기로 결정",
  "action_type": "speak",
  ...
}
```

---

## 2. 테스트 결과

```
tests/test_simulation.py - 20 passed (Phase 1)
tests/test_phase2.py     - 24 passed (Phase 2)
----------------------------------------
Total: 44 passed ✅
```

Phase 2 테스트 커버리지:
- SupportTracker (추가/조회/상호지지)
- WhisperSystem (누출 확률/Observer 보너스)
- MarketPool (거래 기록/분배)
- Treasury (입출금/overflow)
- InfluenceSystem (계급/칭호/권한)
- CrisisSystem (발생 조건/extra decay)
- ArchitectSkills (subsidy/tax/billboard)
- Agent Phase 2 (max cap/suspicion/status)

---

## 3. 시뮬레이션 결과 (100 에폭)

```
Epoch   1 | 생존: 12 | 에너지: 1166 | Treasury:   0
Epoch  20 | 생존:  3 | 에너지:  450 | Treasury:   0
Epoch  37 | 생존:  2 | 에너지:  400 | Treasury:   0 [CRISIS: 역병]
Epoch  54 | 생존:  2 | 에너지:  400 | Treasury:   0 [CRISIS: 기근]
Epoch  95 | 생존:  2 | 에너지:  400 | Treasury:   0 [CRISIS: 가뭄]
Epoch 100 | 생존:  2 | 에너지:  400 | Treasury:   0

--- 최종 결과 ---
생존자: 2/12
  merchant_01: E=200, I=1 (평민), @market
  merchant_02: E=200, I=2 (평민), @market
```

### 관찰
1. **시장 풀 효과**: merchant 2명이 100 에폭까지 생존 (max cap 200 도달)
2. **Crisis 발생**: epoch 37, 54, 95에 위기 이벤트 발생
3. **페르소나 전략**: merchant만 생존 (시장 중심 전략의 우위)
4. **Phase 1 대비 개선**: 20 에폭 전멸 → 100 에폭에 2명 생존

### 밸런스 분석
```
시나리오 B (시장 중심) 달성: merchant 100+ 에폭 생존 ✅
시나리오 A (협력 없음): ~20 에폭에 대부분 사망 ✅
시나리오 C/D: LLM 연동 후 검증 필요
```

---

## 4. 파일 구조 (Phase 2 완료)

```
src/
├── __init__.py      # 패키지 (확장)
├── agent.py         # Agent (max_energy, suspicions 추가)
├── environment.py   # Environment
├── personas.py      # 페르소나 프롬프트
├── logger.py        # 로깅 (thought 필드 지원)
├── simulation.py    # 메인 루프 (전면 수정)
├── actions.py       # NEW: 행동 정의
├── support.py       # NEW: Support 추적
├── whisper.py       # NEW: Whisper 누출
├── market.py        # NEW: 시장 풀 + Treasury
├── influence.py     # NEW: 영향력 계급
├── crisis.py        # NEW: Crisis 이벤트
└── architect.py     # NEW: 건축가 스킬
```

---

## 5. 다음 단계 (Phase 3: LLM 연동)

### 구현 예정
- [ ] 상황 인식 프롬프트 생성 (CONTEXT_TEMPLATE)
- [ ] LLM API 호출 (Anthropic / Google)
- [ ] 응답 파싱 및 행동 변환
- [ ] Mock 모드 ↔ 실제 모드 전환

### Phase 3 질문 사항

**Q1. LLM 선택**
- 모든 에이전트 동일 LLM?
- 페르소나별 다른 LLM? (예: architect만 Claude)

**Q2. 프롬프트 길이**
- 최근 N턴 히스토리 포함 범위?
- 전체 컨텍스트 요약 방식?

**Q3. 비용 관리**
- 에폭당 API 호출 수 제한?
- 캐싱 전략?

---

## 6. GitHub

**커밋**: `0310147` - Phase 2 구현 (12 files, +1592/-100 lines)
**URL**: https://github.com/JihoonJeong/agora-12

---

*다음 progress report: Phase 3 완료 시점*
