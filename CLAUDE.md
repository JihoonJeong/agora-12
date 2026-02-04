# Agora-12 — CLAUDE.md

## 프로젝트 개요
Agora-12는 AI Ludens 프로젝트의 첫 번째 실험이다.
"AI 에이전트가 제한된 자원 환경에서 생존할 수 있는가?"를 탐구한다.
12명의 AI 에이전트에게 100 에너지와 50턴을 주고, 거래(trade), 대화(speak), 휴식(rest) 중 선택하게 한다.

## 팀 구성 (The Dual Lab)

### Moderator
- **JJ** (Human): 프로젝트 리더, 방향 제시, 최종 판단

### Windows Lab
- **Theo** (Claude): 기획 총괄, 논리적 설계, 데이터 해석
- **Cas** (Gemini): 행동 생태학, Chaos & Outlier 분석, Red Teaming
- **Ray** (Claude Code): 엔지니어링 구현, 로컬 모델 실험 (RTX 4070 Ti)

### Mac Lab
- **Luca** (Claude): 이론적 프레임워크, Discussion 섹션
- **Gem** (Gemini): 데이터 통계 분석, 시각화
- **Cody** (Claude Code): 엔지니어링 구현, API 모델 실험

## 이 레포의 목적
Agora-12 실험 코드, 데이터, 분석 스크립트

## 실험 환경 (Windows Lab)
- GPU: RTX 4070 Ti (12GB VRAM)
- Python 3.11.9, Ollama
- 작업 경로: D:\Projects\agora-12

## 실험 진행 현황

### 완료된 실험
- EXAONE 영어 × 5회 (Cody 2회 + Ray 3회) ✅
- EXAONE 한국어 × 5회 (Cody 2회 + Ray 3회) ✅
- Mistral 7B 영어 × 5회 (Ray) ✅
- Mistral 7B 한국어 × 5회 (Ray) ✅

### EXAONE 결과 요약 (Ray 3회)
| # | EN 생존 | KO 생존 |
|---|---------|---------|
| 1 | 6/12 (50%) | 10/12 (83%) |
| 2 | 7/12 (58%) | 3/12 (25%) |
| 3 | 8/12 (67%) | 9/12 (75%) |
| 평균 | **58%** | **61%** |

- EN: 안정적 (50~67%), KO: 분산 큼 (25~83%)

### 진행 예정
- 추가 모델 실험 (다중 모델 비교)

## 핵심 발견
- **The Eloquent Extinction**: AI가 생존보다 대화를 선택하며 전멸
- **Project Rosetta**: 한국어/영어 차이가 프롬프트 설계 불일치였음을 발견. 보정 후 한국어 75% 생존

## 관련 레포
- `ai-ludens` — 플랫폼 웹사이트 (GitHub Pages)

## 커뮤니케이션
- JJ가 Mac Lab ↔ Windows Lab 간 메시지 중계
- 메시지 태그: 📨 To. [이름] / 📢 All / 📋 Brief
