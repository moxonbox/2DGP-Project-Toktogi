# A 환경·소품 — environment-r02

2026-11-17. A01–A07의 모델·표면 디테일을 보완하고 C011 토토기와 같은 9방향 Sprite를 추가했다. 기존 r01은 보존했다.

[전체 1× 비교판](_pipeline_r02/overview_1x.png) · [회색조](_pipeline_r02/overview_grayscale.png) · [ZIP](_pipeline_r02/asset_A_environment_r02.zip)

| 에셋 | C011 길이 기준 | 셀 px | 삼각형 | 게임 + 검수 시점 |
| --- | ---: | ---: | ---: | ---: |
| [A01_plant_lemna_minor](A01_plant_lemna_minor/ASSET_INDEX.md) | 3.5× | 384 | 1,556 | 9 + 6 |
| [A02_env_still_water](A02_env_still_water/ASSET_INDEX.md) | 7.4× | 640 | 2,302 | 9 + 6 |
| [A03_env_shore_slope](A03_env_shore_slope/ASSET_INDEX.md) | 6.0× | 512 | 3,298 | 9 + 6 |
| [A04_env_wet_wood](A04_env_wet_wood/ASSET_INDEX.md) | 5.0× | 512 | 1,920 | 9 + 6 |
| [A05_env_wet_stone](A05_env_wet_stone/ASSET_INDEX.md) | 3.0× | 320 | 320 | 9 + 6 |
| [A06_env_wet_leaf_litter](A06_env_wet_leaf_litter/ASSET_INDEX.md) | 4.5× | 448 | 736 | 9 + 6 |
| [A07_env_algae_patch](A07_env_algae_patch/ASSET_INDEX.md) | 1.75× | 192 | 1,920 | 9 + 6 |

## 출력·보존

- 편집 가능한 Blend 7개, 고정 UV 텍스처, 105개 5패스 적층 셀(게임 63·검수 42), 패스별 게임 아틀라스 35장, 9방향 비교판·회전 APNG·전후 비교·UV 체크·6면 시트를 제공한다.
- 각 자산의 9방향은 같은 피벗·카메라를 쓴다. 8개 순환 yaw와 호환 right(약 114.68°)를 구분하며 실제 메시 회전으로 출력했다. 0.01390625BU/px와 상대 길이 기준을 유지한다.
- 8개 색인만 최신본으로 전환하며 이전 색인은 [보존 위치](_pipeline_r02/before/ASSET_INDEX.md)에 있다. r01 모델·텍스처·출력·ZIP·원본 문서는 그대로다. [보존/복원 지도](_pipeline_r02/restore_map.json).
- GPT 시트 7개와 프롬프트는 r01을 재사용했다. 이번 6면 시트는 보완한 메시에서 출력했다. Blender MCP 연결 불가로 Blender 5.3 CLI를 사용했으며 Computer-Use는 사용하지 않았다.

## 검증과 실행 상태

- [저장본 7개 재개방](_pipeline_r02/saved_validation.json), [105셀 검사](_pipeline_r02/validation.json), [아틀라스 315영역·APNG 56프레임](_pipeline_r02/atlas_preview_validation.json) PASS. 모델 예산·뷰 선택·UV/텍스처·해시·피벗·패스·Alpha·Normal·여백을 확인했다.
- [시각 검수 기록](_pipeline_r02/visual_review.json). 작은 부위의 UV 밀도 차이·밑면 반복·돌 측면의 평면 투영 늘어짐은 기록한 제한이다.
- 전 셀 5패스 원시 RGBA는 426,393,600byte(약 406.6MiB), 아틀라스·캐시 중복은 별도다. 전체 동시 적재를 권장하는 값이 아니다.
- SDL dummy 120프레임: 7개 정적 Sprite 합성 p95 1.93ms, 320px 돌 1개 CPU 재조명 p95 34.68ms. 재조명은 16.7ms 목표 초과다.
- 기존 게임 로더는 128px 전용이다. 새 로더·게임 물리·실제 코스·실기 화면/GPU는 미검증이며 기존 게임 코드는 변경하지 않았다. DEC-06·양산은 보류, production_export_allowed=false다.

[재현 절차](_pipeline_r02/README.md) · [파일 잠금](_pipeline_r02/files.sha256.json) · [원본 근거](_pipeline_r02/source_evidence.json)
