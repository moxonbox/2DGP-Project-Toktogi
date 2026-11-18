# Toktogi Pico2D 후보

Rebuild v1.2의 실행 후보. 기존 `../prototype`의 코드·번들·저장 결과를 보존한다.
Windows x64, 검증 Python 3.13.15. Pico2D 1.5.1 / Pillow 13.0.0 / PySDL2 0.9.17 / PySDL2-DLL 2.32.10.
Pygame 없는 별도 가상환경에서 실행하며 네트워크·Blender는 실행에 필요하지 않다.

## 설치와 실행

프로젝트 루트에서 최초 한 번 설치한다. 실행 스크립트는 설치·다운로드하지 않는다.

```powershell
py -3 -m venv toktogi/prototype_pico2d/.venv
toktogi/prototype_pico2d/.venv/Scripts/python.exe -m pip install -r toktogi/prototype_pico2d/requirements.txt
toktogi/prototype_pico2d/Start-Toktogi.cmd
toktogi/prototype_pico2d/Start-Toktogi.cmd --profile legacy
toktogi/prototype_pico2d/Start-Toktogi.cmd --verify
```

기본은 `habitat`: 젖은 숲바닥 → 수면 잎길 → 갈대숲 귀환으로 이어지는 3,120px 코스다.
A01–A07의 개구리밥·수면·나무·돌·낙엽·이끼, B04–B07 배경과 C261 r03을 연결한다.
등불 3개를 켜고 마지막 깃발에서 멈추면 완료한다. 씨앗 3개·섭식·회전·손질은 선택 활동이다.
쉼터 등불은 활성화 즉시 체크포인트를 저장한다. C261은 수면 구간에서만 공격한다.
`--profile pond_test`는 이전의 평면 수면 시험 구간을 실행한다.
[스테이지·재질 설계](../../document/markdown/HabitatStage.md)를 함께 참고한다.
경고 뒤 고정 위치를 공격하며 Space 도약으로 피하거나 가까운 입에 E/F로 반격한다.
`--profile seamless`는 `stage_01/pond_duckweed`와 `stage_02/lotus_leaf`의 기존 연속 코스다.
`--profile legacy`는 기존 단일 코스·Camera=(0,0)·261개 검수 항목을 비교한다.
seamless F2와 HTML은 원본 261개+새 경계 리플레이 2개=263개다.
Python·시작 스크립트는 임의 cwd에서 실행된다. 파일명 `_`와 C011 식별자는 그대로 사용한다.
한글 폰트는 Windows 맑은 고딕을 사용한다. 네이티브 출력은 `TOKTOGI_FONT`로 명시할 수 있다.

## 조작

- WASD: 입력 방향으로 회전, A/D 이동·W/S 도약 조준을 함께 수행한다. 화살표는 플레이 입력에서 제외하며 Ctrl로 제동하고 Shift 유지로 달린다.
- Space DOWN: 도약 준비 취소·짝 시작, UP: 도약 요청. 반복/고립 UP은 효과를 만들지 않는다.
- E: 가까운 적 공격 우선, 대상 활성화/수집, 유지 섭식, 대상 없으면 손질. F 공격(X 호환), Q 반전, Z 지상 360°.
- E DOWN 때 선택한 명령은 UP까지 유지한다. F/G는 플레이에서 사용하지 않는다.
- P/Esc: 일시정지, R: 체크포인트 재시작, F1/F2/Tab: 플레이·검수 장면.
- F2: 방향키로 항목/프레임, Space 재생, V 방향, M 패스, L 광원, F3 접점, Ctrl+F 검색.
- 평탄 Normal/Bloom 버튼은 F2 재질 검사다. Bloom은 초기 꺼짐이다. 강도 0.0으로 직접광을 끌 수 있다. 광원이 닿은 발광 부위가 임계 밝기를 넘으면 주변으로 번진다.

## 검증과 근거

```powershell
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/main.py --verify
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/verify_backend.py
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/verify_native_input.py
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/verify_app_native.py
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/verify_performance.py
```

`--verify`는 App/SDL 초기화 전 분기하고 pygame/sdl2/pico2d가 import되지 않았음을 검사한다.
기존 7개 회귀의 assertion을 유지했다. Pygame 객체·픽셀 API만 엔진 독립 입력/Pillow로 이식했다.
SDL 원시 입력 검사는 별도 관문으로 옮겼고, 직접 held를 주입하던 테스트에는 물리 키 fixture를 함께 설정했다.
`verification.json`: 기존 코스 13.75초, 도약 4회·탄성 1회 및 행동·재질 회귀.
`acceptance.json`: 2구간 34.183333초, 도약 8회·탄성 2회, 입력·월드·카메라·환경·재질 통합 근거.
기존 리플레이 4개 725틱은 원본 Game과 위치·속도·지지·상태·셀·효과가 정확히 같다.
기본/보조 2,374셀 전부 디코딩한다. 조명 기준 24건은 Alpha 차이 0, RGB 최대 1/255다.
`native_results.json`, `native_app_results.json`: 실제 SDL/Pico2D API를 사용하는 dummy/software 자동 검사다.
`performance_results.json`: 시작 비용과 120프레임 처리 비용, 메모리·DLL·장치 정보를 분리한다.
dummy 결과를 실제 창·물리 키·IME 후보창·모니터 DPI·장치 성능의 인수로 간주하지 않는다.

## 에셋과 잔여 인수

개구리밥은 후보에서 명시적으로 고정한 `asset/A/A01_plant_lemna_minor/2D/environment-r02`를 검증해 준비한다.
manifest·PNG·출처 Blend SHA, 앵커, 크기, 패스를 검사하며 경계 전환에서 파일을 읽지 않는다.
월드의 수평 충돌체는 유지한다. 배율·앵커·임시 상태는 `acceptance.json`의 environment.bindings에 기록한다.
연꽃 제작물은 아직 없다. Stage02는 `provisional_duckweed_for_lotus`이며 최종 연꽃 제작/바인딩 합격이 아니다.
제작물의 `production_export_allowed=false`, DEC-06 보류를 그대로 유지한다.
사용자가 Computer-Use 미사용을 지정했으므로 실제 창·키·IME·DPI 인수는 미검증이다.
기존 07 교차 후보 30쌍·왼쪽 Z 19자세, 정확 저장·동적/경사 IK도 계속 보류다.

## 생성 도구와 복원

```powershell
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/build_motion_preview.py
toktogi/prototype_pico2d/.venv/Scripts/python.exe document/tools/architecture/build_atlas.py --candidate
```

패커는 후보에서만 실행한다. 기본 원본은 C011/integrated-r5이며 두 번째 인자로 새 ZIP 경로를 지정할 수 있다.
새 ZIP과 잠금은 전체 디코딩 검사 후 함께 인계한다. 실행 중인 번들을 패킹하지 않는다.
기존 실행본 복원은 `toktogi/prototype/Start-Toktogi.cmd`로 전환한다. 기존 코드는 변경하지 않았다.
후보 복원은 Git의 해당 커밋에서 코드·ZIP·잠금·requirements·World·보고서를 한 묶음으로 복원한다.
최초 비교 기준은 `baseline.json`, 원래 저장소 커밋은 `d07501f`다. 혼합 버전의 ZIP/잠금은 시작 시 거부한다.

## 최신 추가 구현 검증

2026-11-17 23:45 종료 요청에 따라 추가분은 집중 검사만 수행했다. 전체 회귀는 추가 구현 전 결과다.
`controls_results.json`·`pond_results.json`: WASD/E, 두 공격의 도약 회피·반격·단일 피격·Pause/R 통과.
연잎은 asset에 최종 연꽃 제작물이 없어 테스트용 절개 잎 도형이며 양산 에셋으로 집계하지 않는다.
C261은 asset의 `gambusia-r03` male/right 원본 Sprite 6액션 72셀과 실제 mouth_tip을 재사용한다. NumPy를 추가하지 않았다.
F2 이동 광원/Bloom의 dummy p95는 22.01/24.70ms로 16.7ms 목표 미달이며 실기 인수는 미검증이다.

실행부와 배포 패커는 현재 C261 r03 명세와 해당 Sprite 72셀을 함께 사용한다. 실행 오류는 콘솔에 남고 키 입력을 기다린다.

2026-11-18 habitat 추가: 발판은 원본 앵커·일정 배율·Nearest로 정렬한다. 수평 물리 발판은 유지한다. 환경 Normal/RM 재조명은 시작 시 5단계 캐시하며 톡토기는 같은 월드 광원으로 실시간 계산한다.


## 조작·렌더링 최적화 · 2026-11-18

기본 habitat 보행은 24→72px/s, 회복 보행은 39.6px/s다. 반대 입력의 제동 가속을 1,700px/s²로 적용한다.
120Hz 시뮬레이션에서 최고 속도 도달 100ms, 정지 66.67ms, 역방향 이동 시작 50ms다. 기존 프로필은 24px/s를 유지한다.
재질 coverage 영역만 계산하고 Bloom의 동일 커널을 발광 영역에 적용한다. HUD는 상태 변경 때 갱신하며 프레임 전체 복사를 줄였다.
해상도·Normal/RM·BRDF·발광 세기·모션 프레임·120Hz 물리·캐시 상한은 유지한다. 신규 의존성은 없다.

| 동일 Windows/direct3d 숨김 출력, 각 180프레임 | 변경 전 중앙값 / p95 | 변경 후 중앙값 / p95 |
| --- | --- | --- |
| habitat 보행·월드 조명 | 18.82 / 24.83ms | 11.70 / 15.39ms |
| F2 이동 광원·Bloom | 15.23 / 21.33ms | 12.41 / 16.69ms |

`verify_optimization.py`는 렌더·업로드·출력 시간을 측정하며 시작·물리·입력 폴링·캡처 저장은 시간에서 제외한다.
056 당시 `optimization_before.json`의 원본 24개 RGBA 해시와 모두 일치했다. HUD 4상태, Bloom 배율 1/2/3과 입력 응답도 확인한다.
`optimization_results.json`에는 9개 도약, E 상호작용·공격, 물고기 피격/회피 4건의 집중 검사 결과를 함께 기록했다.
플레이 p95는 16.67ms 예산 이내다. F2 p95는 0.027ms 초과하며 최대 프레임 25.44/43.50ms가 남아 모든 프레임의 60fps를 보장하지 않는다.
전체 회귀·Computer-Use·실기 장시간 인수 및 배포 ZIP 재생성은 생략했다. 위 수치는 이번 로컬 환경의 결과다.


## 톡토기 팔레트 보정 · 2026-11-18

원본 Sprite는 팔레트·툰 명암까지 적용된 표시용 결과이며 Base는 거의 흰색인 재질 입력이다.
플레이·F2의 `lit`는 Normal/RM·발광으로 계산한 밝기를 Base의 기준 밝기와 비교해 원본 Sprite의 RGB에 같은 명암 변화를 적용한다. 변화 폭은 채널당 ±32/255이며 밝거나 어두운 픽셀은 RGB가 잘리지 않도록 변화 폭을 줄인다. Alpha와 재질 영역 밖 윤곽은 원본과 같다.
고정 80:20 혼합에서 광원을 좌우로 이동했을 때 대기 포즈의 평균 밝기 변화는 7.70/255였다. 현재는 19.36/255다. 첫 발판의 시작점과 첫 광원 바로 아래에서는 9.06에서 25.62로 커졌다.
`verify_materials.py`는 대기·보행 포즈의 조명 방향과 거리 반응, 24개 원시 BRDF 기준, 원본 색상 채널 간 차이, Alpha·윤곽·Bloom을 검사한다.
`palette_comparison.png`는 같은 대기 포즈의 원본과 광원 위치별 변경 전후를 보여준다.


## WASD 직접 회전 · 2026-11-18

A/D 단독은 A=왼쪽·D=오른쪽 기준으로 현재 방향에서 최대 180° 회전한 뒤 멈춘다. 기본/S는 종전과 반대 반원(A +180°·D −180°), W는 종전 반원(A −180°·D +180°)을 선택한다. 같은 키를 계속 유지하거나 다시 눌러도 한 바퀴 돌지 않는다.
Ctrl+A/D는 제동한 채 제자리에서 360° 이상 연속 회전한다. A는 화면 반대쪽, D는 화면 쪽으로 돌기 시작하며 180°마다 100ms 멈칫한다.
회전 중 키를 놓으면 현재 각도에 멈춘다. W는 아래 조준과 다음 A/D의 임시 반원 선택, S는 위 조준과 기본 반원 복귀를 맡는다. W를 놓아도 다음 방향 전환이 끝날 때까지 선택을 유지하며 완료하면 기본으로 돌아온다. 반대 키 동시 입력은 회전을 멈춘다. Ctrl 해제 시 A/D 기준 방향으로 180° 이내 복귀한다.
회전 중 각속도는 기존 Z와 같은 360°/1.55초이며, Ctrl+A/D에만 180°마다 100ms 멈칫을 적용한다. 반대 입력은 즉시 멈칫을 해제한다. 표시 자세는 Z의 62셀과 기존 카메라 방향을 사용하므로 실제 화면은 에셋 셀 간격으로 변한다.
A/D가 없는 W/S 단독 입력은 270°/90° 목표 회전을 유지한다. 반원 내부에서는 현재 각도에서 이어 가고, 좌우 경계에서 선택한 반원으로 방향을 바꾼다. 회전 중에는 Z 자세를 이어 가고 좌우 방향이 맞으면 조준 모션을 연결한다. W/S 교대는 중립 자세를 거치며, 조준 중 회전은 중립 복귀 2배속 재생 후(명목 80ms·요청부터 회전까지 약 92ms) 시작한다. 조준값과 이동 반응은 즉시 반영한다. 좌우 이동·도약·E/F 행동은 기존 2D 물리를 따른다.
공중·작업·피격·착지·Q/Z 재생 중에는 해당 행동 모션이 우선이며 이후 가장 가까운 좌우 행동 방향에서 회전을 재개한다. 지지 발이 발판을 벗어나는 회전 자세는 적용하지 않는다.
Q 반전과 Z 자동 360° 회전은 유지한다. 기존 리플레이·화살표 fixture는 새 WASD 회전과 분리한다.
`verify_directional_yaw.py`가 A/D 180° 제한·Ctrl+A/D 연속 회전·초기 화면 방향, 180°마다 멈칫과 360° 이후 재개, W 임시 반원·완료 후 기본 복귀·S 취소와 W/S 조준, 중간 정지, Pause, 반대 입력, 점프·공격, 발판 지지와 기존 Z를 확인한다.

수정된 `document/markdown/Control.md` 기준으로 Ctrl은 제동 및 A/D 조합 연속 회전, Shift는 달리기, F는 공격이다. X 공격은 호환키로 남긴다.
달리기는 보행 목표 속도의 2배이며 habitat 기준 보행 72·달리기 144px/s다. 회복 계수 .55와 제동 가속은 유지한다.
좌우 Ctrl/Shift를 각각 추적하며 한쪽만 놓아도 다른 쪽 유지가 유효하다. Ctrl 제동이 달리기보다 우선하며 Ctrl+A/D 회전은 허용한다. F2의 Ctrl+F 검색은 기존대로다.

`verify_wasd_transitions.py`는 빠른 WASD 교대의 표시 방향 변화, W/S 조준 셀의 연속 복귀와 회전 진입, 점프·공격·Pause 우선을 집중 검사한다. 각도 메타데이터가 없는 기존 번들은 시작 시 원본 마커 방향 표를 준비해 가까운 회전 셀을 선택한다. 새 이미지 보간이나 추가 에셋·의존성은 사용하지 않는다.


## 입력 파이프라인 조치 · 2026-11-18

키 유실과 모션 대기를 분리해 [상세 진단](../../document/markdown/InputPipelineDiagnosis.md)에 기록했다.
검색 중 KEYUP, 다른 keysym의 동일 물리 키 해제, F/X/E 새 단발 입력, 3ms 탭의 틱 내 상쇄와 수집 시간 누락을 수정했다.
조준→회전 표시는 175ms에서 약 92ms로 줄였다. 초기 4초의 거절 이유도 표시하며 실제 동작 적격성·120Hz 처리 순서는 유지한다.
`verify_input_pipeline.py`는 10~240fps 탭·96개 프레임 위상·동시 6키·기존 문맥 정리와 SDL scancode를 확인한다. `input_pipeline_before.json`과 `input_pipeline_results.json`이 근거다.
물리 키보드 rollover·IME/OS 필터·실제 input-to-photon은 미검증이다. 합성 시계 수치를 실제 장치 지연으로 보장하지 않는다.
