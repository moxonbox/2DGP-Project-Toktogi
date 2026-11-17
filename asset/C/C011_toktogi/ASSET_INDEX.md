# C011 톡토기 에셋

물알둥근톡토기(*Sminthurides aquaticus*)의 생물 자료와 integrated-r5·framework-r4 제작본에 반영한 내용을 기록한다.
원천 자료 D1–D8의 출처와 반영 범위는 [플레이 명세 v2.1 부록 C](../../../document/markdown/022_toktogi_playable_action_animation_spec.md#c1-제공된-8개-파일)에서 확인할 수 있다.

## 3D 모델·리깅

### 참고 명세와 실제 반영

| 참고 명세 | 반영한 내용 |
| --- | --- |
| [종합 생물 명세 · D1](../../../document/markdown/reference/toktogi.md) | 종의 몸 형태와 기관을 캐릭터의 근거로 삼았다. 더듬이, 다리, 복관, 도약기관을 제작·행동 단위로 구분했다. |
| [3D 모델링용 외형 명세 · D2](../../../document/markdown/reference/toktogi_model.md) | 둥근 몸 실루엣, 여섯 다리, 더듬이, 복관과 접힌 도약기관을 외형에 반영했다. 문서에서 미정인 치수는 게임용 비율로 조정했다. |
| [행동·움직임 명세 · D3](../../../document/markdown/reference/toktogi_movement.md) | 걷기·섭식·손질·도약 자세의 근거다. 06–07은 더듬이 손질에서 도약기관 손질로 이어지며 중간에 지지발을 바꾼다. |
| [상태 머신·리깅 단계 · D4](../../../document/markdown/architecture/toktogi_state_machine.md) | 준비·본동작·종료 포즈, 발끝 지지와 작업 접촉 마커, 중단 후 복귀 자세를 만들 때 참조했다. |
| [생태계 관계 명세 · D5](../../../document/markdown/reference/toktogi_ecosystem.md) | 서식 환경·먹이·공존 관계를 표현할 때 참고했다. 현행 플레이의 활성 상호작용 범위는 콘텐츠 기획을 따른다. |
| [플레이 명세 v2.1 §11–12](../../../document/markdown/022_toktogi_playable_action_animation_spec.md#11-3d-모델리그) | 리그 계층, IK, 소켓과 접지, 연속 포즈와 출력 표본의 제작 계약이다. |

### 제작 기준과 산출물

- **형태·표면** · 흰 몸과 어두운 눈의 대비를 유지한다. [BaseColor 원본](3D/textures/toktogi_rigged_basecolor.png)은 Blend 내장본과 일치한다.
- **리그** · 현행 주 캐릭터는 37본·2,732삼각형이다. 손질·회전에서 작업 기관과 지지발을 구분한다. [실행 프로젝트 제작 기록](../../../prototype/README.md)
- **Z 회전** · 좌우 Action에서 지지발 목표를 월드 좌표에 고정하고, 교대하는 발을 다음 접지 위치로 옮긴다. 저장본 지오메트리와 프레임 사이 자세를 검수했다. [보조 모션 제작 기록](3D/framework-r4/README.md) · [연속 자세 검증](3D/framework-r4/spin_interkey_validation.json)
- **기반 리그** · 기본 모션과 2D 원본 셀의 제작 출처다. [integrated-r5 Blend](3D/integrated-r5/toktogi_integrated.blend)
- **보조 모션 리그** · Z·공중제비·모서리·복귀 등 런타임 보조 Action의 제작본이다. [framework-r4 Blend](3D/framework-r4/toktogi_framework_r4.blend)
- **통합 작업본** · 기본 클립 82개와 보조 프로필 146개를 한 파일에서 선택한다. Scripting에서 `SET_TOKTOGI_MOTION.py`의 `MOTION`을 바꾸고 Run Script를 실행한다. ID와 방향은 내장 `TOKTOGI_MOTION_LIST.txt`에 있다. [통합 Blend](3D/toktogi_unified.blend)
- [3D 모델 생성용 시트 폴더](sheet/README.md)는 별도 시트를 보관할 위치다.

### 행동 적용 범위

- 관찰 자료는 기관 사용과 행동 순서의 근거다. 공중제비의 회전량·시간과 360° 제자리 회전은 게임용 연출이다.
- 06–07 손질은 플레이에서 사용한다. 08 방울 손질과 개체 간 관찰 장면은 검수용이다. 수면 동작·산란 및 관계 의존 플레이는 제외 범위다. [콘텐츠 기획](../../../document/markdown/012_toktogi_content_design_spec.md) · [행동 장면 적용 범위](../../../document/markdown/022_toktogi_playable_action_animation_spec.md#부록-a-원본-31개-생물-장면의-적용-범위)

## 2D 스프라이트 제작

### 참고 명세와 실제 반영

| 참고 명세 | 반영한 내용 |
| --- | --- |
| [3D에서 2D로 변환 기술 검토 · D6](../../../document/markdown/architecture/3Dconv2D.md) | 3D의 실루엣과 재질 데이터를 화면 공간에 따로 출력한다. 패스마다 색·수치 해석을 구분하고 정수 확대에 Nearest를 사용한다. |
| [기획 검토 v0.2 · D7](../../../document/markdown/report/toktogi_Design_Spec_v0_1_Review_v0_2.md) | 고정 카메라의 픽셀풍, 실시간 재질 반응, 발끝 접지와 스프라이트 실루엣의 정합을 적용했다. 최종 생산 좌표 계약 DEC-06은 보류다. |
| [1차 기획서 · D8](../../../01_2DGP_1차_기획서.pdf) | 도약 중심 모션과 픽셀·재질·조명 방향의 초기 기준이다. 현행 출력 범위와 규격은 v2.1 및 제작 manifest를 따른다. |
| [플레이 명세 v2.1 §13–14](../../../document/markdown/022_toktogi_playable_action_animation_spec.md#13-3d2d-출력재생-계약) | 출력 방향, 크롭과 아틀라스, 재질 패스, 피벗·접지·작업 마커, 표본 시간과 전환을 정의한다. |
| [2D 셰이더 명세](../../../document/markdown/architecture/2Dshader.md#atlas-materials) | Base와 Normal·RM·Emissive를 사용해 런타임 조명에 반응한다. F2의 원본·평탄 Normal 비교와 Bloom은 구현 대기다. |

### 출력·검수 기준

- **프레임** · 각 셀은 128×128px이다. 개별 PNG에는 Sprite·Base·Normal·RM·Emissive 다섯 패스를 위아래로 저장한다.
- **정렬** · 한 프레임의 패스는 같은 타일·피벗을 쓴다. 발 접지와 작업 접점은 manifest 마커를 기준으로 확인한다.
- **시간** · 자세 표본, 방향, 프레임 시간은 manifest에 연결한다. 공중제비처럼 제작 검수와 게임의 재생 시간이 다른 모션은 실제 게임 시간표에서 대조한다.
- **표시** · 실제 128px와 정수 배율에서 윤곽, 가는 더듬이, 발끝, 눈 하이라이트를 확인한다. 낮은 표시율에서도 핵심 접촉·전환 자세가 보이는지 검수한다.
- **제작 검증** · [출력 검증](2D/integrated-r5/asset_validation.json) · [포즈 검증](2D/integrated-r5/pose_validation.json) · [런타임 검증](2D/integrated-r5/runtime_validation.json)

| 패스 | 보관 데이터와 용도 |
| --- | --- |
| Sprite | 베이크된 외관, 윤곽과 최종 실루엣 Alpha |
| Base | sRGB 기본색과 조명이 적용되는 표면 범위 |
| Normal | 카메라 기준 표면 방향. 런타임에서 정규화해 조명에 사용한다. |
| RM | R 채널의 거칠기, G 채널의 금속성 |
| Emissive | 선형 발광값. 눈 하이라이트의 표현에 사용한다. |

### 파일과 실행 경로

- **원본 1,444셀** · [제작용 2D 아틀라스 manifest](2D/integrated-r5/playable_manifest.json)
- **보조 930셀** · [보조 모션 manifest](3D/framework-r4/runtime_poses.json)
- **개별 프레임** · `2D/<모션 계열>/<모션 ID>/<방향>/<프레임>.png`. 경로 예시로 조준 `2D/aim/aim_down/`, 보행 `2D/walk/walk_start/`, 회전 `2D/turn/ground_spin_left/`을 참조한다.
- **재생·검수** · [전체 모션 미리보기](ToktogiMotionPreview.html)와 게임 F2를 사용한다. [런타임 번들·갱신 방법](../../../prototype/README.md)

기반 아틀라스를 바꾸면 해당 manifest와 [원본 번들](../../../prototype/toktogi_assets.zip)을 함께 갱신한다.
보조 모션을 바꾸면 대응하는 보조 manifest와 [보조 번들](../../../prototype/toktogi_runtime_poses.zip)을 함께 갱신한다.
두 번들은 기반 manifest 서명으로 정합을 검사한다. [패커](../../../prototype/pack_assets.py) · [에셋 로더](../../../prototype/materials.py)

| 모션 계열 | 폴더 수 |
| --- | --- |
| 조준·공중·공격·제동 | `aim` 4, `air` 7, `attack` 1, `brake` 12 |
| 취소·모서리·탄성·낙하 | `cancel` 94, `edge` 12, `elastic` 1, `fall` 2 |
| 섭식·피격·대기·상호작용 | `feed` 3, `hit` 2, `idle` 1, `interact` 4 |
| 도약·착지·관찰·진행 | `jump` 39, `land` 2, `obs` 19, `progress` 3 |
| 회복·회전·보행 | `recovery` 14, `turn` 6, `walk` 2 |

## 명명과 이전 버전

- 에셋 폴더의 분류·번호와 모션 디렉토리 구조는 [에셋 번호 규칙](../../../document/markdown/architecture/AssetLabelRule.txt)을 참조한다. 개별 프레임은 원본 모션 ID와 인덱스를 유지한다.
- 이전 버전 101파일 중 비중복 93파일은 [7z 보관본](3D/versions/toktogi_previous.7z)에 있다. [복원 지도](3D/versions/restore_map.json)의 `archive:`는 7z 내부, `current:`는 이 폴더 기준 경로다.
