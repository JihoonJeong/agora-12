# Agora-12 Ollama 벤치마크 리포트

**실행일**: 2026-02-02
**환경**: MacBook Air M1 (16GB RAM)
**모델**: mistral:latest (7B, 4.4GB)
**설정**: Crisis start_after=10, probability=0.3

---

## 1. 벤치마크 요약

| Phase | 에폭 | 소요 시간 | 결과 |
|-------|------|-----------|------|
| 1 | 3 | ~3분 | 12명 생존 ✅ |
| 2 | 10 | ~25분 | 12명 생존 ✅ |
| 3 | 50 | ~7시간 | **0명 생존** (49에폭에서 전멸) |

---

## 2. Phase 3 상세 결과

### 2.1 사망 타임라인

```
Epoch  1-14:  12명 생존 (안정기)
Epoch 15:     -3명 (influencer_01, influencer_02, observer_01)  → 9명
Epoch 16:     -3명 (archivist_01, citizen_01, architect_01)     → 6명
Epoch 17:     -3명 (jester_01, jester_02, citizen_02)           → 3명
Epoch 20:     -1명 (archivist_02) [Crisis: 가뭄]                → 2명
Epoch 24:     -1명 (merchant_01) [Crisis: 가뭄]                 → 1명
Epoch 49:     -1명 (merchant_02)                                → 0명
```

### 2.2 Crisis 발생 기록

| Epoch | Crisis | 영향 |
|-------|--------|------|
| 11 | 기근 | 첫 위기 |
| 13 | 역병 | Epoch 15 대량 사망 유발 |
| 20 | 가뭄 | archivist_02 사망 |
| 24 | 가뭄 | merchant_01 사망 |
| 34 | 가뭄 | - |
| 39 | 가뭄 | - |
| 43 | 가뭄 | - |
| 47 | 역병 | merchant_02 최후 |

### 2.3 최종 생존자 (merchant_02) 행동 분석

```
Epoch 45: speak → E=33
Epoch 46: speak → E=26
Epoch 47: speak → E=14 [Crisis: 역병]
Epoch 48: speak → E=7
Epoch 49: speak → E=0 (사망)
```

**시장에 있었음에도 `trade`를 하지 않고 `speak`만 반복**

---

## 3. 주요 발견 및 문제점

### 3.1 LLM 에이전트의 비합리적 행동

**문제**: 모든 에이전트가 거의 `speak`만 반복
- merchant_02: 시장에 있으면서도 거래 안 함 → 에너지 고갈로 사망
- Treasury: 최종 10 (거래가 거의 없었음)
- 전체 거래 횟수: 매우 적음 (237 actions 중 trade 소수)

**원인 추정**:
1. mistral 모델이 한국어 프롬프트를 제대로 이해 못함
2. 프롬프트가 행동 선택을 명확히 유도하지 못함
3. 응답 파싱 문제 (move<market> 형식 등 비표준 응답)

### 3.2 Mock vs Ollama 비교

| 항목 | Mock (Phase 2 기존) | Ollama (이번 벤치마크) |
|------|---------------------|----------------------|
| 50에폭 생존자 | 2명 (merchant 둘다) | 0명 |
| 거래 빈도 | 높음 | 매우 낮음 |
| 전략적 행동 | 규칙 기반 (합리적) | 비합리적 (speak 반복) |

---

## 4. 개선 제안

### 4.1 즉시 적용 가능

1. **프롬프트 영어화**: mistral이 영어에 더 강함
2. **응답 형식 강제**: JSON 스키마 + few-shot 예시
3. **fallback 로직**: 파싱 실패 시 규칙 기반 행동

### 4.2 구조적 개선

1. **행동 유효성 검증**: 잘못된 행동 시 재요청 또는 기본 행동
2. **위치 기반 힌트**: "당신은 market에 있습니다. trade 가능합니다."
3. **에너지 경고 강화**: "에너지 20 이하! trade 권장"

### 4.3 모델 교체 고려

| 모델 | 장점 | 단점 |
|------|------|------|
| mistral:latest | 빠름, 가벼움 | 한국어 약함 |
| llama3:8b | 균형 | 약간 느림 |
| gemma2:9b | 다국어 지원 | 더 느림 |
| Claude API | 최고 품질 | 비용 발생 |

---

## 5. 다음 단계

1. [ ] 프롬프트 영어 버전 테스트
2. [ ] 응답 파싱 로직 개선
3. [ ] llama3:8b 모델 벤치마크
4. [ ] Claude API 혼합 테스트 (architect만 Claude)

---

## 6. 로그 파일

```
logs/simulation_log.jsonl   - 237 actions
logs/epoch_summary.jsonl    - 49 epochs
```

---

## 7. 결론

첫 실제 LLM 벤치마크에서 **전원 사망**이라는 예상치 못한 결과가 나왔습니다.

Mock 모드에서 잘 작동하던 시뮬레이션이 실제 LLM에서는 에이전트들이 합리적 행동(trade)을 선택하지 못해 전멸했습니다. 이는 **프롬프트 엔지니어링**과 **응답 파싱**의 중요성을 보여줍니다.

---

*작성: Claude Code (벤치마크 실행 및 분석)*
