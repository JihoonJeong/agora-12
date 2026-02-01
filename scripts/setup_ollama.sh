#!/bin/bash
# Agora-12 Ollama 환경 설정 스크립트
# MacBook Air M1 (16GB RAM) 최적화

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Agora-12 Ollama 환경 확인 스크립트                      ║"
echo "║     Target: MacBook Air M1 (16GB RAM)                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓ $1${NC}"
}

check_fail() {
    echo -e "${RED}✗ $1${NC}"
}

check_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 1. 시스템 정보 확인
echo "=== 1. 시스템 정보 ==="
echo "Chip: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo 'Unknown')"
echo "Memory: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))GB"
echo "macOS: $(sw_vers -productVersion)"
echo

# 2. Ollama 설치 확인
echo "=== 2. Ollama 설치 확인 ==="
if command -v ollama &> /dev/null; then
    check_pass "Ollama 설치됨: $(which ollama)"
    echo "   버전: $(ollama --version 2>/dev/null || echo 'Unknown')"
else
    check_fail "Ollama 미설치"
    echo
    echo "설치 방법:"
    echo "  brew install ollama"
    echo "  또는 https://ollama.ai 에서 다운로드"
    exit 1
fi
echo

# 3. Ollama 서버 상태 확인
echo "=== 3. Ollama 서버 상태 ==="
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    check_pass "Ollama 서버 실행 중 (localhost:11434)"
else
    check_fail "Ollama 서버 미실행"
    echo
    echo "서버 시작 방법:"
    echo "  ollama serve"
    echo "  (별도 터미널에서 실행하거나 백그라운드로 실행)"
    echo
    read -p "지금 서버를 시작할까요? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Ollama 서버 시작 중... (백그라운드)"
        ollama serve > /dev/null 2>&1 &
        sleep 3
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            check_pass "서버 시작 성공"
        else
            check_fail "서버 시작 실패"
            exit 1
        fi
    else
        exit 1
    fi
fi
echo

# 4. 설치된 모델 확인
echo "=== 4. 설치된 모델 확인 ==="
MODELS=$(ollama list 2>/dev/null)
if [ -n "$MODELS" ]; then
    echo "$MODELS"
else
    check_warn "설치된 모델 없음"
fi
echo

# 5. mistral 모델 확인
echo "=== 5. mistral:latest 모델 확인 ==="
if ollama list 2>/dev/null | grep -q "mistral"; then
    check_pass "mistral 모델 설치됨"

    # 모델 정보
    MODEL_SIZE=$(ollama list 2>/dev/null | grep mistral | awk '{print $2}')
    echo "   크기: $MODEL_SIZE"
else
    check_fail "mistral 모델 미설치"
    echo
    echo "설치 방법:"
    echo "  ollama pull mistral:latest"
    echo
    read -p "지금 mistral 모델을 다운로드할까요? (약 4GB, 5-10분 소요) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "mistral 모델 다운로드 중..."
        ollama pull mistral:latest
        check_pass "다운로드 완료"
    else
        exit 1
    fi
fi
echo

# 6. 간단한 연결 테스트
echo "=== 6. API 연결 테스트 ==="
echo "간단한 프롬프트로 테스트 중..."
TEST_RESPONSE=$(curl -s http://localhost:11434/api/generate \
    -d '{"model": "mistral:latest", "prompt": "Say hello in Korean", "stream": false}' \
    2>/dev/null | head -c 500)

if echo "$TEST_RESPONSE" | grep -q "response"; then
    check_pass "API 응답 정상"
    echo "   응답 샘플: $(echo "$TEST_RESPONSE" | grep -o '"response":"[^"]*"' | head -c 100)..."
else
    check_fail "API 응답 실패"
    echo "   응답: $TEST_RESPONSE"
fi
echo

# 7. 메모리 상태 확인
echo "=== 7. 메모리 상태 ==="
FREE_MEM=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
INACTIVE_MEM=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | tr -d '.')
PAGE_SIZE=$(vm_stat | head -1 | grep -o '[0-9]*')
AVAILABLE_MB=$(( (FREE_MEM + INACTIVE_MEM) * PAGE_SIZE / 1024 / 1024 ))

echo "사용 가능 메모리: 약 ${AVAILABLE_MB}MB"
if [ "$AVAILABLE_MB" -gt 4000 ]; then
    check_pass "충분한 메모리 (권장: 4GB 이상)"
else
    check_warn "메모리 여유 부족 (다른 앱 종료 권장)"
fi
echo

# 8. Python 환경 확인
echo "=== 8. Python 환경 확인 ==="
if command -v python3 &> /dev/null; then
    check_pass "Python3: $(python3 --version)"
else
    check_fail "Python3 미설치"
fi

# requirements 확인
cd "$(dirname "$0")/.."
if python3 -c "import yaml; import requests" 2>/dev/null; then
    check_pass "필수 패키지 설치됨 (pyyaml, requests)"
else
    check_warn "패키지 미설치"
    echo "   설치: pip install -r requirements.txt"
fi
echo

# 최종 요약
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                      환경 확인 완료                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "다음 단계:"
echo "  1. config/settings.yaml에서 default_adapter: ollama 설정"
echo "  2. scripts/benchmark.sh 실행"
echo
echo "권장 사항 (M1 16GB):"
echo "  - 전원 연결 상태에서 실행"
echo "  - Safari, Chrome 등 무거운 앱 종료"
echo "  - Activity Monitor로 메모리 모니터링"
echo
