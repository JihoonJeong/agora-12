#!/bin/bash
# Agora-12 단계별 벤치마크 스크립트
# MacBook Air M1 (16GB RAM) 최적화

set -e

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 로그 디렉토리 생성
mkdir -p logs reports

# 타임스탬프
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BENCHMARK_LOG="logs/benchmark_${TIMESTAMP}.log"

log() {
    echo -e "$1" | tee -a "$BENCHMARK_LOG"
}

header() {
    echo
    log "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    log "${CYAN}║  $1${NC}"
    log "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# 시작
header "Agora-12 Ollama 벤치마크 시작"
log "시작 시간: $(date)"
log "로그 파일: $BENCHMARK_LOG"
log ""

# 환경 확인
header "Phase 0: 환경 확인"

# Ollama 서버 확인
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log "${RED}✗ Ollama 서버가 실행 중이 아닙니다${NC}"
    log "  먼저 'ollama serve'를 실행하세요"
    exit 1
fi
log "${GREEN}✓ Ollama 서버 실행 중${NC}"

# 모델 확인
if ! ollama list 2>/dev/null | grep -q "mistral"; then
    log "${RED}✗ mistral 모델이 설치되어 있지 않습니다${NC}"
    log "  먼저 'ollama pull mistral:latest'를 실행하세요"
    exit 1
fi
log "${GREEN}✓ mistral 모델 준비됨${NC}"

# 설정 확인
if ! grep -q "default_adapter: ollama" config/settings.yaml 2>/dev/null; then
    log "${YELLOW}⚠ config/settings.yaml에서 default_adapter가 ollama가 아닙니다${NC}"
    log "  benchmark 전용 설정(config/settings_benchmark.yaml)을 사용합니다"
    CONFIG_FILE="config/settings_benchmark.yaml"
else
    CONFIG_FILE="config/settings.yaml"
fi
log "설정 파일: $CONFIG_FILE"
log ""

# 메모리 상태 기록
log "시스템 메모리:"
vm_stat | head -5 | tee -a "$BENCHMARK_LOG"
log ""

# Phase 1: 3 에폭 테스트
header "Phase 1: 연결 테스트 (3 에폭)"
log "예상 시간: 3-5분"
log "예상 LLM 호출: ~36회 (12 에이전트 × 3 에폭)"
log ""

START_TIME=$(date +%s)

if python3 main.py --config "$CONFIG_FILE" --epochs 3 2>&1 | tee -a "$BENCHMARK_LOG"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log ""
    log "${GREEN}✓ Phase 1 완료${NC}"
    log "  소요 시간: ${DURATION}초 ($(($DURATION / 60))분 $(($DURATION % 60))초)"
    log "  에폭당 평균: $(($DURATION / 3))초"
else
    log "${RED}✗ Phase 1 실패${NC}"
    log "로그를 확인하세요: $BENCHMARK_LOG"
    exit 1
fi

log ""
log "${YELLOW}Phase 1 결과를 확인하세요.${NC}"
log "계속하려면 Enter, 중단하려면 Ctrl+C"
read -r

# Phase 2: 10 에폭 테스트
header "Phase 2: 소규모 테스트 (10 에폭)"
log "예상 시간: 10-20분"
log "예상 LLM 호출: ~120회"
log ""

START_TIME=$(date +%s)

if python3 main.py --config "$CONFIG_FILE" --epochs 10 2>&1 | tee -a "$BENCHMARK_LOG"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log ""
    log "${GREEN}✓ Phase 2 완료${NC}"
    log "  소요 시간: ${DURATION}초 ($(($DURATION / 60))분 $(($DURATION % 60))초)"
    log "  에폭당 평균: $(($DURATION / 10))초"
else
    log "${RED}✗ Phase 2 실패${NC}"
    exit 1
fi

log ""
log "${YELLOW}Phase 2 결과를 확인하세요.${NC}"
log "Crisis 이벤트 발생 확인 (epoch 10부터 30% 확률)"
log "계속하려면 Enter, 중단하려면 Ctrl+C"
read -r

# Phase 3: 50 에폭 풀 벤치마크
header "Phase 3: 풀 벤치마크 (50 에폭 + 인터뷰)"
log "예상 시간: 1-2시간"
log "예상 LLM 호출: ~600회 + 인터뷰"
log ""
log "${YELLOW}⚠ 주의사항:${NC}"
log "  - 맥북이 뜨거워질 수 있습니다"
log "  - 전원 연결 권장"
log "  - 중간에 중단하려면 Ctrl+C"
log ""

START_TIME=$(date +%s)

if python3 main.py --config "$CONFIG_FILE" --epochs 50 --interview --verbose 2>&1 | tee -a "$BENCHMARK_LOG"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log ""
    log "${GREEN}✓ Phase 3 완료${NC}"
    log "  총 소요 시간: ${DURATION}초 ($(($DURATION / 60))분 $(($DURATION % 60))초)"
    log "  에폭당 평균: $(($DURATION / 50))초"
else
    log "${RED}✗ Phase 3 실패${NC}"
    exit 1
fi

# 최종 결과 요약
header "벤치마크 완료"

log "=== 생성된 파일 ==="
log ""
log "로그 파일:"
ls -lh logs/*.jsonl 2>/dev/null | tail -5 | tee -a "$BENCHMARK_LOG" || log "  (없음)"
log ""
log "리포트 파일:"
ls -lh reports/*.json reports/*.md 2>/dev/null | tail -5 | tee -a "$BENCHMARK_LOG" || log "  (없음)"
log ""
log "벤치마크 로그: $BENCHMARK_LOG"
log ""

log "=== 제출용 파일 ==="
LATEST_REPORT=$(ls -t reports/game_*.json 2>/dev/null | head -1)
LATEST_MD=$(ls -t reports/report_*.md 2>/dev/null | head -1)

if [ -n "$LATEST_REPORT" ]; then
    log "1. 인터뷰 JSON: $LATEST_REPORT"
fi
if [ -n "$LATEST_MD" ]; then
    log "2. 리포트 MD: $LATEST_MD"
fi
log "3. 시뮬레이션 로그: logs/simulation_log.jsonl"
log "4. 벤치마크 로그: $BENCHMARK_LOG"
log ""

log "${GREEN}모든 테스트 완료!${NC}"
log "종료 시간: $(date)"
