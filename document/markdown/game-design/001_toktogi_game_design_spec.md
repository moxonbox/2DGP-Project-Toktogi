# 톡토기 통합 게임 기획 명세

현행 실행 기준은 Windows 프로토타입 framework-r4와 플레이 명세 v2.1이다. 차기 실행본은 [Pico2D 재구현 명세](../Rebuild.md)를 따르며, 아직 Pygame 기반인 현행 코드와 구분한다.
이 문서는 기획과 구현의 기준 문서, 에셋의 제작·배포 경로, 적용 범위와 공통 인수 기준을 연결한다.

<a id="spec-map"></a>
## 명세서 지도

### 기획 상세

- [시스템 기획](011_toktogi_system_design_spec.md) · 입력, 상태, 시간, 충돌, 이동과 도약
- [콘텐츠 기획](012_toktogi_content_design_spec.md) · 상승 코스, 대상 작업, 체크포인트와 목표
- [전투 기획](013_toktogi_combat_design_spec.md) · 공격 자격, 타격, 피격과 위험물

### 기획 구현

- [Pico2D 재구현](../Rebuild.md) · 채택 환경, 입력·출력 이식, 재질 유지, 구현 순서와 수락 관문
- [조작·입력](../Control.md#atlas-controls) · 플레이/F2 키·버튼·검색·시간·취소·포커스와 입력 검증
- [Pico2D 백엔드](../Pico2DBackend.md) · 단일 SDL renderer·좌표/DPI·RGBA·폰트·자원·실기 검증
- [Stage·Level 연속 전환](../StageLevel.md) · 개구리밥/연꽃잎 구간·월드 좌표·카메라·진행·로딩·체크포인트

- [게임 프레임워크](021_toktogi_game_framework_spec.md#atlas-framework) · 모듈 책임, 데이터 흐름, 재사용 진입점
- [플레이·액션·애니메이션 v2.1](022_toktogi_playable_action_animation_spec.md) · 요구 ID, 리그, 내보내기와 제작 계약
- [플레이 상태 머신](toktogi_state_machine.md#atlas-states) · 현행 키, 상태 전이, 연결 모션
- [2D 스프라이트 셰이더](../2Dshader.md#atlas-materials) · 조명·발광의 현행 구현과 F2 후처리 계획

### 에셋 제작과 실행

- [에셋 디렉토리·번호 규칙](../AssetLabelRule.txt) · 분류, 모션 폴더 계층, 버전 보관
- [C011 톡토기 에셋 색인](../../../asset/C/C011_toktogi/ASSET_INDEX.md) · 기반·현행 Blend, 모션 프레임, 텍스처, 복원 지도
- [기반 아틀라스 manifest](../../../asset/C/C011_toktogi/2D/integrated-r5/playable_manifest.json) · 셀 키, 재생 표본, 패스, 앵커
- [보조 모션 제작](../../../asset/C/C011_toktogi/3D/framework-r4/README.md) · Blender 선택기, Z 재디딤, 연속 자세 검증
- [실행·번들 갱신 README](../../../toktogi/prototype/README.md) · 설치, 번들·잠금 파일, 검증과 미리보기 갱신
- [Windows 실행](../../../toktogi/prototype/Start-Toktogi.cmd) · 플레이와 F2 검수 진입점
- [모션 미리보기](../../../asset/C/C011_toktogi/ToktogiMotionPreview.html) · 모션, 게임 시간표 및 입력 리플레이

### 검증과 참고

- [요구 사항별 검증](../../../toktogi/prototype/REQUIREMENT_VERIFICATION.md) · v2.1 요구 ID별 근거와 잔여 범위
- [실행 회귀 결과](../../../toktogi/prototype/verification.json) · 자동 코스, 판정, 재질과 프레임 검사
- [3D에서 2D로 변환 기술 검토](../3Dconv2D.md) · 후보 렌더링 방식과 출력 설계 배경
- [관찰 동작 자료](../reference/toktogi_movement.md) · 자세와 행동 제작 근거
- [모델 참고](../reference/toktogi_model.md) · 형태와 기관
- [선행 기획 검토](../report/toktogi_Design_Spec_v0_1_Review_v0_2.md) · 채택 결정과 보류의 배경

### 적용 범위

- 구현 · 1인 상승 코스의 이동, 지상 회전, 자동 공중제비, 경로 작업과 지상 공격. [현행 실행과 검수](../../../toktogi/prototype/README.md)
- 검수 전용 · 수직축 공중 선회, 관계 관찰 및 방울 손질은 에셋 확인에 사용한다. [콘텐츠 적용 범위](012_toktogi_content_design_spec.md)
- 구현 대기 · Pico2D 실행본, 개구리밥/연꽃잎의 seamless stage·level 전환, F2의 원본·평탄 Normal 비교·Bloom. [재구현 기준](../Rebuild.md) · [셰이더 구현 명세](../2Dshader.md)
- 보류 · 최종 좌표 계약 DEC-06, 정확 저장·복원 및 이동·경사 발판 IK. [제작·확장 범위](022_toktogi_playable_action_animation_spec.md)
- 제외 · 수영·부력·수면 행동·산란 및 관계 의존 플레이. 수면 식물 발판 환경과 연속 구간 이동은 [차기 범위](../StageLevel.md)에 포함한다. [플레이 범위 결정](022_toktogi_playable_action_animation_spec.md)

## 제작에서 실행까지

1. 에셋 색인에서 기반 리그와 [통합 작업본](../../../asset/C/C011_toktogi/3D/toktogi_unified.blend)을 확인한다. 기본·보조 모션은 통합본에서 선택하며, 기존 2D 셀의 제작 출처와 revision은 각각 보존한다.
2. 기본 또는 보조 모션을 갱신한 뒤 아틀라스·manifest나 보조 셀과 해당 재생 정보를 같은 제작 revision으로 맞춘다.
3. 기반 출력은 [패커](../../../toktogi/prototype/pack_assets.py)로 런타임 ZIP과 잠금 파일을 함께 생성한다. 보조 출력은 [제작 절차](../../../asset/C/C011_toktogi/3D/framework-r4/README.md)에 따라 별도 ZIP과 잠금 파일을 갱신한다.
4. [에셋 로더](../../../toktogi/prototype/materials.py)가 두 번들의 해시·기반 서명·프레임과 마커를 확인한다. 게임과 F2는 이 번들을 사용한다. 편집용 Blend와 개별 프레임은 제작·검수에 사용한다.
5. [모션 HTML 생성기](../../../toktogi/prototype/build_motion_preview.py)로 미리보기를 갱신한다. 재생 시간표나 리플레이를 바꿨다면 F2와 HTML에서 같은 시나리오를 대조한다.

## 변경과 인수

- 입력·물리 변경은 시스템 기획과 상태 머신에 반영한다. 코스 배치가 영향을 받으면 콘텐츠 기획에서 도달 기준과 검증 경로를 갱신한다.
- 대상 배치·마커 변경은 콘텐츠 기획에서 관리한다. 자세 지지, 도달, 바닥 여유와 실제 효과 시점은 관련 구현·검증과 함께 확인한다.
- 공격·위험 변경은 전투 기획에서 관리한다. 코스 위험 배치와 행동 우선순위, 취소 뒤 남는 효과를 함께 확인한다.
- 재질·모션 변경은 출력 revision과 적용 범위를 기록한다. 동일 프레임의 피벗·접지·작업 마커와 재질 패스 정합을 확인한다.
- 여러 분야에 적용되는 변경은 규칙의 기준 문서를 갱신한다. 다른 문서에서 해당 기준을 참조하고 중복 설명을 줄인다.

### 공통 인수 순서

1. 현행·원안의 요구 ID와 대상 프로필, 구현 상태, 영향을 받는 상세 문서를 기록한다.
2. 동일한 입력 기록으로 효과 횟수·발생 시점·종료 상태와 화면에 보이는 포즈를 확인한다.
3. 동작과 전환은 128px에서 확인한다. 표시율을 낮췄을 때 핵심 자세, 지지발, 작업 접점이 보이는지 검수한다.
4. 기존 코스는 고정 카메라, 차기 두 Level은 [StageLevel](../StageLevel.md)의 추적 Camera에서 주요 발판과 작업·전투 대상, 연결 양쪽 경로가 보이는지 확인한다. [플레이 화면 구현](../../../toktogi/prototype/play_view.py)
5. 요구 사항별 기록에 재현 근거와 적용 한계를 남긴다. 저장된 자동 회귀와 실제 장치 검수의 결과를 각각 기록한다.

<a id="atlas-sources"></a>
## 구조도 갱신 계약

구조도 생성기는 아래 ID로 섹션의 원본을 찾는다. 원본 이름과 제목은 바꿀 수 있으며 ID와 링크의 절 앵커로 연결한다.

| HTML ID | 기준 원본 | 표시 항목 |
| --- | --- | --- |
| architecture | [실행 진입점](../../../toktogi/prototype/Start-Toktogi.cmd) | 전체 배치, 처리 순서, 노드별 입출력과 구현 위치 |
| framework | [현행 호출 순서](021_toktogi_game_framework_spec.md#atlas-framework) | 초기화·틱·렌더링·검수 호출과 객체 관계 |
| files | [Python 진입점](../../../toktogi/prototype/main.py) | 파일·클래스·메서드·import의 위치와 관계 |
| controls | [조작·입력표](../Control.md#atlas-controls) | 플레이와 F2 입력, 키 표기, 동작과 조건 |
| states | [현행 행동·진행 상태](toktogi_state_machine.md#atlas-states) | 상태 카드·전이·상세, 독립 진행 상태 |
| motion | [전체 모션 프리뷰](../../../asset/C/C011_toktogi/ToktogiMotionPreview.html) | 카탈로그 집계, 대표 재생과 프레임 조작 |
| materials | [셰이더 구현 상태](../2Dshader.md#atlas-materials) | 5패스·조명 처리와 구현 상태 |
| specs | [명세서 지도](#spec-map) | 문서 카드의 제목·순서·링크와 적용 범위 |
| evidence | [현행 소스 실행 결과](../../../toktogi/prototype/verification.json) | 완주·회귀·요구 검증과 배포본 구분 |

- 이 표의 링크는 생성기 입력이다. 링크를 바꾸면 해당 화면을 다시 생성하고 보존 항목을 검증한다.
- 릴리스 ZIP은 해당 배포 시점의 자료다. 현재 프로젝트의 검증은 위 실행 결과와 요구 추적표에서 확인한다.
- 구조도 갱신과 검증 명령은 [생성기 README](../../tools/architecture/README.md)를 따른다.
- [현재 프로젝트 구조도](../../ToktogiProjectArchitecture.html)에서 명세서, 실행 파일, 상태 머신과 모션을 연다.
