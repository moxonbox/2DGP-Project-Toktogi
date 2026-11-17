# 톡토기 플레이 프레임워크 — framework-r4

`Start-Toktogi.cmd` 실행. Python 3.11 이상, Pygame 2.6.1, Pillow 13.0.0 필요. 의존성은 `python -m pip install -r requirements.txt`로 설치합니다. 런타임에는 Blender·인터넷이 필요 없습니다.

## 플레이

- ← / → 이동, Shift 제동, ↑ / ↓ 도약 방향. Space를 눌렀다 떼면 도약합니다. 착지 전후의 짧은 탄성 입력 창을 이용해 높은 잎으로 이동합니다.
- E: 접촉 거리의 등불 활성화·씨앗 수집. F 유지: 먹이 섭식. G 유지: 넓은 발판에서 왼쪽을 향해 손질. X: 가시 껍질 공격. Q: 반대 방향 회전. Z: 접지 상태에서 현재 방향을 기준으로 360° 회전. 회전 중 새 공격·점프는 회전 종료 뒤 목적 방향으로 실행됩니다.
- P / Esc: 일시정지·재개. R: 현재 체크포인트에서 새 도전. 마지막 등불 근처에서 멈추면 클리어.
- 플레이에는 HUD·장식 배경이 없습니다. 접촉 가능한 먹이·버튼·씨앗이 연두색으로 바뀌며 거절된 작업에는 180ms의 따뜻한 캐릭터 틴트가 표시됩니다. 이 반응은 판정에 영향을 주지 않습니다.

## 프레임워크 재사용

- 배치 또는 체크포인트 변경은 course.py의 Course를 복사해 주입합니다. 좌표는 960×560 논리 필드의 픽셀이며 플랫폼은 x0, x1, 상단 y, 하단 y, 종류를 가집니다. 첫 플랫폼은 시작 지지면입니다. 체크포인트 플랫폼 인덱스와 목표 플랫폼 하나를 포함합니다.
- 배치 변경과 별도로 Capsule 충돌 계산은 physics.py, 시간 정렬은 timeline.py, 자세 선택과 트랙 연결은 motion.py에 있습니다. Game에 Course와 에셋을 넣으면 SDL 창 없이 step과 edge를 호출할 수 있습니다. 앱 전체에서 바꿀 때는 App(course=...)를 사용합니다.
- 다른 128px 소재는 sprite_renderer.SpriteRenderer에 이름별 5패스 Surface를 돌려주는 maps 함수와 발광 스케일을 주입합니다. 재질 표시와 검수에 같은 render 메서드를 사용합니다. 기존 Assets는 번들 잠금과 integrated-r5 데이터 형식을 확인합니다.
- 실행 구조·데이터 흐름과 인수 조건은 [게임 프레임워크 명세서](../document/markdown/021_toktogi_game_framework_spec.md), 키와 상태는 [상태 머신](../document/markdown/architecture/toktogi_state_machine.md)에 있습니다. python main.py --verify는 기존 회귀와 모듈 재사용, 360° 진입·종료·후속 행동을 함께 검증합니다.

```python
from dataclasses import replace

from app import App
from course import COURSE

practice = replace(COURSE, spawn_x=150.0)
App(course=practice).run()
```

## r4 개선

Q와 방향키가 같은 지지 검사로 반전을 시작합니다. 발판 끝에서 발이 지지되지 않으면 발판 안쪽으로 이동한 뒤 반전합니다. 중립 Q는 약 0.48초이며 두 지지 자세를 100ms씩 표시합니다. 섭식에서 보행·반전·새 섭식·손질로 들어갈 때 직전 자세를 이어받습니다. 코스 시작 및 체크포인트는 발 지지와 Capsule 겹침을 함께 검사합니다.

[요구별 검증](REQUIREMENT_VERIFICATION.md) · [구조도 갱신 방법](../document/tools/architecture/README.md)

## 모션·재질 검수

F2 검수 화면, F1 플레이 복귀. 82개 원본 클립, 17개 원본 전환, 146개 런타임 보조 프로필을 재생합니다. 보조 프로필은 손질 취소 표본·목표 방향별 복귀, 착지 표본별 재도약, 모서리 자세입니다. 일반 검수 245항목과 실제 게임 시간표 12항목과 입력 리플레이 4항목을 제공합니다. F2에서 `game_` 또는 `replay_`를 검색하거나 HTML의 게임 재생 시간 섹션을 여세요. 좌우 Z, 공중제비, 일반·탄성 전개 구간을 같은 시간표로 검수합니다.

↑ / ↓ 선택, ← / → 프레임, Space 재생, V 지원 방향, Ctrl+F 검색. `runtime_`로 보조 프로필을 찾습니다. M: 7개 재질 패스, L: 고정·마우스·이동 광원, F3: 접지 마커. 배율은 Nearest 1×/2×/3×입니다. 검수 동안 코스 물리 시간은 멈춥니다.


## r4 입력과 도약

첫 발판 끝은 x=201, 먹이는 x=130으로 옮겨 머리 공간과 양방향 섭식 자세를 확보했습니다. 일반 발사 속도 426px/s와 탄성 541px/s는 기존 값입니다. Space 유지가 보행을 제동하지 않으며 Shift는 접지 제동입니다.

탄성 선행·후행 입력은 접지 승인 때 방향·조준을 적용합니다. Q는 방향키와 같은 회전 제어기를 사용합니다. F UP은 논리 작업을 즉시 닫고 보행은 종료 포즈를 중단합니다. 좌우 동시 유지 시 Walk 의도 0, 무입력 Jump.end는 종료 자세를 유지합니다.

좌우 공중제비는 같은 37본·2,732삼각형 모델의 30셀·5패스입니다. 게임에서 330ms, 원본 Action·F2·HTML에서는 680ms로 자세를 검수합니다. 카메라를 향한 축의 몸 중심 회전과 작은 화면 내 위치 보정으로 128px 타일 안에 보존합니다. 회전 수와 재생 시간은 종별 실측값을 승계하지 않은 게임 연출입니다. 회복 도약은 기존 압축 표현을 사용하며 지지 이탈·피격·천장 접촉은 회전을 해제합니다. 전개 핵심 포즈는 100ms이고 정점 핵심 자세도 속도 범위에서 유지합니다.

현행 입력표·전이도는 ../document/markdown/architecture/toktogi_state_machine.md와 ../document/image/toktogi_state_machine.png입니다. 원 도표는 보존됩니다. python main.py --verify는 r4 입력·도달·10/15/30/60fps 검증도 함께 실행합니다.

## r3 보완

- 회전 중 작업 입력은 현재 회전의 종료 경계에서 시작합니다. Space 취소·피격·지지 상실은 대기 작업을 정리합니다. 재반전은 현재 회전 표본에서 되돌아갑니다.
- 반대 방향을 유지해 착지해도 착지 압축을 표시합니다. 반대 방향 회복 재도약은 160ms 준비에서 방향을 바꾸고, 동일 방향은 80ms 준비를 사용합니다.
- 모서리 조준에는 접은 다리를 유지하는 8개 자세를 추가했습니다. 발판이 작업 자세의 모든 지지발을 받치지 못하면 작업을 거절합니다. 작업 가능색도 현재 공격·회전 상태를 반영합니다.
- 마지막 발판에서는 1px/s 미만으로 0.20초 머물러야 클리어합니다. Pause·검수 복귀는 손질을 다시 실행하지 않고 현재 표본에서 복귀합니다. 진행 키의 중복 DOWN·포커스 가드를 적용했습니다.
- 손질 취소의 복관·도약기관 충돌을 줄이고, 지지발의 높이를 보정해 780개 접지 보조 셀에 지지 목록을 기록했습니다. r4의 30개 공중 셀은 지지발이 없습니다.
- 최초 검수 프레임의 폰트·셰이더 초기화는 화면을 표시하기 전에 준비합니다. 당시 243항목은 F2와 asset/C/C01_toktogi/ToktogiMotionPreview.html에서 재생할 수 있습니다. HTML은 단독 파일로 열 수 있습니다.

## r2 변경

- 무관한 마우스·윈도·미할당 키 이벤트가 행동 취소 순서를 바꾸지 않습니다. SDL queue 시각을 120Hz 경계에 배치하며, 접촉 → 행동 입력 → 효과 → Pause·진행 전환 순서입니다.
- 작업 효과와 표시가 수락 시각부터 같은 경과 시간을 씁니다. 공격 active [0.078, 0.162)초의 root 이동도 구간 안에서 보간합니다.
- 자동 균형 복귀가 보행으로 표시됩니다. 작업 종료 후 과거 보행 위상을 다시 제동하지 않습니다. 착지 중 즉시 재도약은 실제 착지 표본에서 출발합니다.
- 손질 취소는 현재 자세에서 320ms의 효과 없는 직접 복귀를 사용합니다. 해제 당시 이동 방향이 있으면 그 방향의 중립 자세로 회전하며 복귀합니다. 방향키 반전에도 제동·회전 표시가 들어갑니다. 물리 입력을 잠그지 않습니다.
- Shift 등으로 가장자리에 머물 때 바깥쪽 다리를 접은 4개 정적 모서리 프로필을 사용합니다. 몸의 지지는 Capsule이 결정하고, 접은 다리는 지지 마커에서 제외합니다. 임의 지형 IK는 아닙니다.
- Pause는 현재 표시 셀을 그대로 고정합니다. 재개 시 유지 입력과 작업은 해제된 상태입니다.
- 셰이더 수식은 Pillow의 C 이미지 연산으로 계산하고 검수 텍스트를 재사용합니다. 원본 Python 수식의 24개 기준 출력과 채널 오차 최대 1/255를 확인했습니다.

## 에셋·검증

`toktogi_assets.zip`의 integrated-r5 원본 1,444셀·5패스와 `.source.json`은 유지합니다. `toktogi_runtime_poses.zip`은 같은 리그에서 만든 930개 추가 셀과 원본 셀을 참조하는 공유 경계입니다. 두 ZIP의 SHA256과 기반 manifest 서명을 확인하며 불일치하면 실행을 거절합니다.

원본 모델은 `../asset/C/C01_toktogi/3D/integrated-r5/toktogi_integrated.blend`, 보조 Action이 추가된 모델은 `../asset/C/C01_toktogi/3D/framework-r4/toktogi_framework_r4.blend`입니다. 메쉬·UV·웨이트·rest bone·머티리얼 구조는 유지했습니다. 파생본의 `SET_RUNTIME_POSE.py`로 프로필을 선택합니다. 제작·검증 기록은 해당 폴더 README와 `PATCH_NOTES.md`에 있습니다.

`2D/integrated-r5`의 아틀라스와 manifest가 바뀌면 프로젝트 루트에서 아래 패커를 실행합니다. 보조 모션은 [Blender 제작 절차](../asset/C/C01_toktogi/3D/framework-r4/README.md)에 따라 갱신하고, 새 보조 ZIP과 동명의 `.source.json`을 함께 `prototype`에 배치합니다. 두 번들의 기반 서명이 일치해야 합니다. 재생 자료를 바꿨다면 모션 HTML을 갱신한 뒤 회귀를 실행합니다.

```powershell
python prototype/pack_assets.py asset/C/C01_toktogi/2D/integrated-r5
python prototype/build_motion_preview.py
python prototype/main.py --verify
```

`python main.py --verify`: 코스 완주, 기존 회귀 검증, 실제 App의 0이 아닌 시각 입력, 취소 경계, 보행 12위상×3작업 종료, 18개 착지 재도약, 10/15/30/60fps 복귀, 4개 모서리, 원본·추가 셀 전체, 셰이더 기준 비교를 실행합니다. `verification.json`, `regression_results.json`, `gameplay_r2_results.json`에 기록합니다.

[요구 사항별 검증](REQUIREMENT_VERIFICATION.md)의 추가 실행은 `verification.json`의 `requirement_trace`에 기록됩니다.

측정은 같은 호스트의 SDL dummy update+draw 기준입니다. 실물 키보드·GPU/모니터 지연이나 다른 PC의 60fps를 보증하지 않습니다. 첫 로드와 캐시 실패 프레임은 계속 측정 대상입니다. 테스트 결과의 최대 비용도 함께 확인하세요.

수면·산란은 제외합니다. 일반·탄성 도약의 공중제비는 게임 연출로 자동 재생합니다. 지상 360도는 Z로 실행합니다. 수직축 공중 선회와 관계 장면은 검수 에셋입니다. 정확 저장·복원, 경사·이동 발판 IK, 복수 광원·깊이 그림자, 설치 없는 EXE 배포, DEC-06 최종 생산 좌표 계약은 이번 보완 범위 밖입니다. 원본 손질 메시 교차의 전면 재제작도 포함하지 않습니다.
