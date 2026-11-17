# Toktogi Pico2D 후보

Rebuild.md의 단계별 이식 후보입니다. 기존 `../prototype`을 비교 기준으로 보존합니다.
Windows x64 / Python 3.11 이상. 현재 작업 단계는 Git 커밋과 검증 보고서로 확인합니다.

## 실행

별도 환경에 `requirements.txt`를 설치합니다. 시작 스크립트는 자동 설치하지 않습니다.
`python main.py --verify`는 SDL 초기화 없이 검증합니다. `python main.py`는 Pico2D로 실행합니다.

## 인수 상태

구현·자동 검증 결과와 실제 키보드/IME/DPI/성능 인수는 구분합니다.
DEC-06, 정확 저장, 동적/경사 IK 및 기존 제작 QA는 이번 이식의 합격 항목이 아닙니다.
