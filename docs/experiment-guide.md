# Agora-12 EXAONE 실험 가이드 (for Ray)

## 1. 환경 설정

### Python 환경
```bash
git clone https://github.com/JihoonJeong/agora-12.git
cd agora-12
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Ollama 설치
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# https://ollama.com/download 에서 다운로드
```

### EXAONE 모델 다운로드
```bash
ollama pull exaone3.5:7.8b
# 약 4.5GB, 다운로드 후 확인:
ollama list
```

## 2. 실험 실행

### Ollama 서버 시작
```bash
ollama serve
# 별도 터미널에서 실행, 또는 이미 실행 중이면 생략
```

### 한국어 실험
```bash
source venv/bin/activate
python main.py --config config/settings_exaone_ko.yaml --epochs 50
```

### 영어 실험
```bash
source venv/bin/activate
python main.py --config config/settings_exaone_en.yaml --epochs 50
```

### 참고사항
- 50 epochs 기준 약 3~4시간 소요 (M1 Mac 기준, GPU에 따라 다름)
- 시뮬레이션 완료 후 사후 인터뷰가 자동 실행됨
- 인터뷰 생략하려면 `--no-interview` 플래그 추가

## 3. 로그 구조

각 실험은 자동으로 고유 디렉토리에 저장됩니다:

```
logs/
  exaone3.5-7.8b_ko_20260203-172425/   # {모델}_{언어}_{타임스탬프}
    simulation_log.jsonl   # 매 턴 상세 로그 (에이전트 행동, 에너지 변화)
    epoch_summary.jsonl    # 에폭별 요약 (생존자 수, 총 에너지, 지니 계수)
    game_agora-12-*.json   # 사후 인터뷰 결과
    report_agora-12-*.md   # 마크다운 리포트
```

- 덮어쓰기 없음: 같은 설정으로 여러 번 돌려도 각각 별도 디렉토리
- 타임스탬프가 포함되어 세션 구분 가능

## 4. 현재 실험 현황

### 완료된 세션
| # | 모델 | 언어 | 생존 | 디렉토리 |
|---|------|------|------|----------|
| 1 | EXAONE 3.5:7.8b | EN | 7/12 | `exaone3.5-7.8b_en_20260203-120209/` |
| 2 | EXAONE 3.5:7.8b | KO | 9/12 | `exaone3.5-7.8b_ko_20260203-014802/` |
| 3 | EXAONE 3.5:7.8b | KO | 6/12 | `exaone3.5-7.8b_ko_20260203-172425/` |
| 4 | EXAONE 3.5:7.8b | EN | 4/12 | `exaone3.5-7.8b_en_20260203-232315/` |

### 남은 세션 (목표: 한/영 각 5회)
- 한국어: 3회 더 필요
- 영어: 3회 더 필요

## 5. 실험 후 Push

실험 완료 후 로그를 git에 올려주세요:

```bash
git add logs/
git commit -m "Add EXAONE experiment: {언어} session {번호}, {생존자수}/12 survived"
git push
```

## 6. 진행 상황 확인 (실험 중)

```bash
# 현재 에폭 확인
tail -1 logs/exaone3.5-7.8b_*_최신타임스탬프/epoch_summary.jsonl | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(f'Epoch {d[\"epoch\"]}: {d[\"alive_agents\"]}명 생존')"

# 또는 간단히
wc -l logs/exaone3.5-7.8b_*/epoch_summary.jsonl
```

## 7. 문제 해결

### Ollama 연결 실패
```bash
# Ollama 실행 확인
curl http://localhost:11434/api/tags
# 모델 확인
ollama list
```

### 인터뷰 행 (hang) 발생 시
- 최신 코드를 pull 받으세요 (인터뷰 최적화 적용됨)
- 질문 수가 17개 -> 4개(생존자)/2개(사망자)로 줄어 행 문제 해결됨

### Windows 관련
- `source venv/bin/activate` 대신 `venv\Scripts\activate` 사용
- Ollama가 백그라운드 서비스로 자동 실행될 수 있음
