# A02_env_still_water — environment-r02

2026-11-17. 모델·디테일·C011 방향별 정적 Sprite 보완. 게임 연결 상태는 보류다.

## 변경과 크기

수면에 낮은 주기 곡면과 고정 잔물결 무늬를 넣었다. 상면과 경계·밑면을 분리해 판 가장자리의 잘못된 스무딩을 줄였다. 물 흐름이나 부력 애니메이션은 아니다.

- [원본 외형](env_still_water_model.md)·[동작](env_still_water_movement.md)·[r01 채택 범위](production_r01.md)는 보존한다. 기존 미채택 동작을 이번 정적 출력의 구현으로 간주하지 않는다.
- [r02 계약](production_contract_r02.json): 길이 기준 7.4×C011, 목표 X 길이 7.143930BU. 부속부 포함 최종 외접은 7.1439 × 4.4408 × 0.0352BU다. 목표 길이와 전체 외접은 서로 다른 측정값이다.
- 생물 실측 mm는 null이다. 모듈 길이·폭·높이·무늬는 게임 연출 선택값이다. C011 몸 대용값 0.965396BU를 사용하며 SI 실측 스케일로 주장하지 않는다.
- 640px 정사각 셀, 0.01390625BU/px, 1× Nearest. left Sprite 외접 604×202px. 모든 방향의 Sprite/Base 투명 여백 ≥8px.
- 삼각형 2,302/4,000, 본 0. [실측](../3D/model_validation_r02.json). 편집 가능한 닫힌 메시를 유지하고 검증되지 않은 숨은 면 삭제는 하지 않았다.

## 방향·피벗·표시

- C011 integrated-r5와 같은 9키: left, yaw_045/090/135/180/225/270/315, right. right는 2.00151174696589rad(약 114.68°)이며 yaw_180과 별개다.
- 모든 게임 방향은 같은 카메라·같은 피벗 [320.0, 319.2249]에서 메시의 실제 Z 회전으로 출력했다. 이미지 미러·임의 trim·2D 회전은 없다. 6개 ortho_*는 모델 검수 전용으로 분리했다.
- [manifest](../2D/environment-r02/manifest.json)에 방향·yaw·카메라 행렬·피벗·앵커·외접·시간·파일 해시·아틀라스 rect가 있다. Blend 내장 SELECT_ENVIRONMENT_VIEW.py의 select_view(name)으로 같은 15시점을 재현한다.
- 5패스는 Sprite/Base/Normal/RM/Emissive 순서다. 데이터 패스 A=255, coverage는 Base A. Base에 조명·AO를 굽지 않으며 AO 소비자 기본값은 1이다. RM G/B=0, 발광=0.
- 기본색 #77A0AA, 거칠기 0.22, 젖음 전이 폭 0.08BU는 연출값이다. 고정 UV 무늬·선형 bilinear 보간·C011 4단 명암 뒤 재질별 팔레트 양자화를 쓴다. 실제 팔레트는 각 cell의 palette_rgb다.
- 외곽색 #22313B, 반경 0px. 수면·부착막은 검은 테두리가 판처럼 보이지 않도록 외곽선 0px 예외다. 디더·화면 AA·mipmap은 없다.
- Blender 미리보기는 기존 C011 AgX·3광원·World, CPU Sprite는 고정 toon4, 연속 재조명 비교판은 기존 게임 BRDF power .82/ambient .34다. 이 세 경로를 구분한다.

## 검수와 자료

- [전후 비교](../2D/environment-r02/before_after.png)·[9방향/C011](../2D/environment-r02/game_views_C011.png)·[회색조](../2D/environment-r02/game_views_grayscale.png)·[공유 광원](../2D/environment-r02/shared_light_compare.png).
- [8방향 APNG](../2D/environment-r02/turntable.png)는 350ms마다 방향을 보여주는 검수 회전이다. 동작 애니메이션이 아니다. 호환 right는 9방향 판에서 별도 확인한다.
- [UV 체크](../2D/environment-r02/uv_checker_compare.png)의 left·ortho_top을 시각 확인했다. 작은 뿌리·자갈·능선·맥·색 조각은 별도 UV 섬으로 체크 밀도가 더 높다. 부위별 밀도 차이와 반복 밑면은 의도적이다. 밑면은 반복을 허용하며 완전한 고유 UV 베이크 아틀라스로 쓰지 않는다.
- [기존 GPT 시트](../sheet/env_still_water_sheet_r01.png)·[원본 프롬프트](../sheet/prompt.txt)를 재사용했다. 새 ImageGen 호출은 없다. [새 6면 시트](../sheet/env_still_water_blender_views_r02.png)는 최종 메시에서 출력했다.
- 재개방·packed/external 일치·15방향 정순/역순·unknown 거부·임의 프레임 seek·원상 복귀 PASS. 셀 15개·아틀라스 영역 45개·APNG 8프레임의 원본 픽셀 일치 PASS.
- [파일 검사](../../_pipeline_r02/validation.json)·[저장본 검사](../../_pipeline_r02/saved_validation.json)·[아틀라스 검사](../../_pipeline_r02/atlas_preview_validation.json)·[출처](../../_pipeline_r02/source_evidence.json).

## 미검증·보류

128px 전용 게임 로더 연결·충돌/접지 바인딩·실제 코스·실기 성능은 미실행이다. 물리·부력·먹이·산란 이벤트는 구현하지 않았다. DEC-06과 번호 확정은 보류이며 production_export_allowed=false를 유지한다. 게임 애니메이션이나 양산 승인으로 해석하지 않는다.
