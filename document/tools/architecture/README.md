# 톡토기 구조도 생성

프로젝트 루트에서 Python 3.11 이상으로 실행한다. 생성기 자체는 Pillow만 사용하며 게임 창·SDL·Blender를 시작하지 않는다. 기존 출력과 Pico2D 후보를 별도 파일로 만든다.

```powershell
python -m pip install Pillow==13.0.0
python document/tools/architecture/build_atlas.py
python document/tools/architecture/build_atlas.py document/ToktogiProjectArchitecture.html
```

기본 입력은 `toktogi/prototype/`의 코드·두 ZIP·`verification.json`과 기존 모션 HTML이다. 기본 출력은 `document/ToktogiProjectArchitecture.html`이다. 생성 중 9개 원본 ID, Control의 두 표, 상태 머신 앵커·Mermaid 전이, 심볼·소스 위치, 출력 링크·중복 ID·삽입 미디어를 검사한다. 오류가 있으면 결과 파일을 쓰기 전에 실패한다.

## Pico2D 후보

후보 코드·두 ZIP·잠금·환경 에셋을 먼저 프로젝트에 게시한다. 아래 명령은 후보의 검증 결과와 모션 HTML을 만든 뒤 구조도를 생성한다. 의존성 설치는 명시적으로 실행하며 생성기가 자동 설치하지 않는다.

```powershell
python -m venv toktogi/prototype_pico2d/.venv
toktogi/prototype_pico2d/.venv/Scripts/python.exe -m pip install -r toktogi/prototype_pico2d/requirements.txt
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/main.py --verify
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/build_motion_preview.py asset/C/C011_toktogi/2D/integrated-r5 toktogi/prototype_pico2d/ToktogiMotionPreview.html
toktogi/prototype_pico2d/.venv/Scripts/python.exe document/tools/architecture/build_atlas.py --candidate
```

`--candidate`는 실행·Python 파일·모션·검증 원본을 `toktogi/prototype_pico2d/`로 바꾸며 `document/ToktogiPico2DArchitecture.html`을 출력한다. 선택 출력 경로는 첫 위치 인수로 지정한다. `verification.json`, `ToktogiMotionPreview.html`, `build_motion_preview.py`가 없으면 누락 경로를 출력하고 중단한다. 과거 결과를 후보 결과로 대체하지 않는다.

후보 화면은 World·Camera·Environment·Pico2D Backend·추가 검증 모듈과 경계 리플레이 두 항목을 표시한다. 기본 코스 회귀 수치는 후보의 legacy 비교 프로필이다. 두 Level 완주·경계·대상 상태 근거는 후보 `acceptance.json`의 `world_game`·`replays`에 있으며 파일이 게시된 경우 링크한다. 저장된 Blender 자세 측정은 기존 제작 근거로 유지한다. CPU 검사와 구조도 생성은 실제 키·IME·DPI·물리 모니터 인수 합격을 뜻하지 않는다.

## 원본 계약과 보존 범위

[통합 게임 기획 명세](../../markdown/game-design/001_toktogi_game_design_spec.md#atlas-sources)의 9개 ID(`architecture`, `framework`, `files`, `controls`, `states`, `motion`, `materials`, `specs`, `evidence`)를 유지한다. Markdown 절은 2단계 제목 앞의 `<a id="절-ID"></a>`로 참조한다.

호출·객체 관계는 framework-r4 표를 읽고 후보 변경 책임을 별도로 반영한다. 조작은 [Control](../../markdown/Control.md#atlas-controls)의 플레이/F2 두 표, 상태 상세는 [상태 머신](../../markdown/game-design/toktogi_state_machine.md#atlas-states)의 표와 Mermaid 전이를 사용한다. 모션 수·셀·사건 시간은 선택한 모션 HTML, 재질 상태는 셰이더 명세, 모듈·import·정의 줄 번호는 선택한 런타임 소스에서 읽는다.

레이아웃은 같은 폴더의 `atlas.template.html`과 `atlas.css`를 사용한다. 출력 HTML의 미디어는 자체 포함이며 소스 링크는 `document/`에 배치했을 때 연결된다. 다른 폴더 출력은 검토용 사본이다. 생성 HTML을 직접 수정하지 않는다.

기존 `verify_atlas.py`는 옛 SPEC 경로와 legacy 원본을 고정한 검사기다. 별도 갱신 전에는 후보 검증 명령으로 사용하지 않는다. 현재 생성기의 내장 검사는 정적 계약·링크 검사이며 브라우저 상호작용 검사를 대신하지 않는다. `verify_interactions.cjs` 실행에는 해당 Node/브라우저 시험 환경과 검사 대상 경로 확인이 필요하다.
