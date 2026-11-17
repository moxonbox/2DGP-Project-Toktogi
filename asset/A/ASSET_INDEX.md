# A 환경 에셋 제작본

2026-11-17 · environment-r01 · AssetPipeLine v2.3 적용. **A01–A07 정적 제작 후보 7개를 생성하고 저장·픽셀 검증했다. 게임 연결 완료본은 아니다.**

| 에셋 | C011 길이 기준 배율 | 셀 px | game_left Sprite px | 삼각형 |
| --- | ---: | ---: | ---: | ---: |
| [A01 나도좀개구리밥](A01_plant_lemna_minor/ASSET_INDEX.md) | 3.5 | 384² | 226×138 | 428 |
| [A02 잔잔한 수면](A02_env_still_water/ASSET_INDEX.md) | 7.4 | 640² | 604×202 | 12 |
| [A03 물가 경사](A03_env_shore_slope/ASSET_INDEX.md) | 6.0 | 512² | 468×220 | 1194 |
| [A04 젖은 가지](A04_env_wet_wood/ASSET_INDEX.md) | 5.0 | 512² | 328×126 | 436 |
| [A05 젖은 돌](A05_env_wet_stone/ASSET_INDEX.md) | 3.0 | 320² | 242×150 | 188 |
| [A06 젖은 낙엽](A06_env_wet_leaf_litter/ASSET_INDEX.md) | 4.5 | 448² | 284×86 | 192 |
| [A07 조류 패치](A07_env_algae_patch/ASSET_INDEX.md) | 1.75 | 192² | 114×34 | 192 |

[전체 1× 비교판](_pipeline_r01/overview_1x.png) · [회색조](_pipeline_r01/overview_grayscale.png) · [검증](_pipeline_r01/validation.json) · [저장본 재개방](_pipeline_r01/saved_validation.json) · [ZIP](_pipeline_r01/asset_A_environment_r01.zip)

## 완료와 한계

- GPT Image 원본 시트·프롬프트 7세트, 편집 가능한 Blend 7개, 고정 UV 텍스처, 49개 5패스 적층 PNG와 Sprite 미리보기, 뷰별 피벗·앵커·해시 manifest를 저장했다.
- 폴더·논리 ID·클립·뷰·샘플을 별도로 기록했다. 8자리 번호 미정과 DEC-06은 계속 보류다. 3D와 셀 크기를 C011의 128px로 강제하지 않았다.
- 정적 지형에 본·자발 이동을 추가하지 않았다. 물리·먹이·산란 이벤트는 실행하지 않는다. 원본 생태·동작 명세는 보존하며 채택/제외/보류는 각 production_r01.md에 명시했다.
- 셀 원시 RGBA 합계 198,983,680byte (약 189.8MiB). 모든 뷰 전량 적재 비용이며 디코딩·재조명 캐시·업로드 여유는 별도다.
- SDL dummy에서 7개 정적 Sprite 합성 p95 1.55ms. 기존 게임 BRDF로 320px 돌 1개를 이동 광원 재조명한 p95는 28.52ms로 16.7ms 목표를 초과했다. 실기 화면/GPU·실제 게임 코스 검증은 하지 않았다.
- 기존 `toktogi/prototype/`는 128px C011 전용이다. 원본 코드·ZIP을 바꾸지 않았다. 이번 독립 검수기는 새로운 셀 크기의 읽기·해시·패스를 검증하는 인계 도구다.

## 실행 및 출처

[재현 절차](_pipeline_r01/README.md) · [파일 잠금](_pipeline_r01/files.sha256.json) · [원본 근거](_pipeline_r01/source_evidence.json)

ImageGen 내장 도구를 사용했다. 모델 식별자·seed는 반환되지 않아 추정하지 않았다. Blender MCP의 원본 읽기는 성공했으나 제작 호출은 120초 제한으로 실패하여 **Blender 5.3 CLI**로 동일 스크립트를 실행했다. Computer-Use는 사용하지 않았다.
