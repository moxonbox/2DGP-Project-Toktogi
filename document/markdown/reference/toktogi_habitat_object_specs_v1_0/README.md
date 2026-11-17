# 2DGP 톡토기 서식지 객체 명세서 색인 (v1.0)
> **대상:** `toktogi_habitat.md`의 독립 에셋 ID **19개 × 상세·model·movement = 57문서**. 주요 출처는 원본 §8 [H01]–[H17].
> **규칙:** [AssetLabelRule.txt](../../AssetLabelRule.txt)에 따라 A(상호작용), B(배경), E(효과) 폴더에 배치했다. 종류 `0(None)`과 분류별 에셋 자리 `1`부터 16진수 순으로 배정했다. 아래 코드는 폴더 접두사이며 variation·모션·프레임 ID는 제작 시 확정한다.
> **축척:** [AssetSize.md](../../AssetSize.md)에 따라 톡토기 성체 암컷 **최대 1.0mm=1×**, 원본 C011 메시 `0.965396 BU`는 제작 대용값일 뿐 실제 mm의 BU 환산값이 아님.

[원본 ZIP](../../../../asset/toktogi_habitat_object_specs_v1_0.zip) · [배치 manifest](manifest.json) · [QA 기록](QA_report.md)

서식지 문서의 수면 보행·도약, 부력, 산란은 관찰 자료 또는 설계 제안이다. 현재 실행 범위는 [StageLevel](../../StageLevel.md)을 따른다.

## 1. 독립 에셋 19개
| 그룹 | 객체 ID / 이름 | 근거 등급 / 폴더 코드 | 역할 / 상대 크기 단서 | 3종 문서 |
|---|---|---|---|---|
| `floating_plants` | `plant_lemna_minor` 나도좀개구리밥 | A+B / `A01` | 엽상체 2.5–6 × 1.5–4 mm; 톡토기(암컷 최대 1 mm) 대비 길이 2.5–6× | [상세](../../../../asset/A/A01_plant_lemna_minor/document/plant_lemna_minor.md) · [모델](../../../../asset/A/A01_plant_lemna_minor/document/plant_lemna_minor_model.md) · [동작](../../../../asset/A/A01_plant_lemna_minor/document/plant_lemna_minor_movement.md) |
| `floating_plants` | `plant_lemna_perpusilla` 좀개구리밥 | B/C / `B01` | 엽상체 약 1.5–4 × 0.7–2.5 mm; 길이 1.5–4× | [상세](../../../../asset/B/B01_plant_lemna_perpusilla/document/plant_lemna_perpusilla.md) · [모델](../../../../asset/B/B01_plant_lemna_perpusilla/document/plant_lemna_perpusilla_model.md) · [동작](../../../../asset/B/B01_plant_lemna_perpusilla/document/plant_lemna_perpusilla_movement.md) |
| `floating_plants` | `plant_spirodela_polyrhiza` 개구리밥 | B/C / `B02` | 엽상체 약 5–8 × 4–6 mm; 길이 5–8×; 뿌리 약 3–5 cm(별도 측정축) | [상세](../../../../asset/B/B02_plant_spirodela_polyrhiza/document/plant_spirodela_polyrhiza.md) · [모델](../../../../asset/B/B02_plant_spirodela_polyrhiza/document/plant_spirodela_polyrhiza_model.md) · [동작](../../../../asset/B/B02_plant_spirodela_polyrhiza/document/plant_spirodela_polyrhiza_movement.md) |
| `floating_plants` | `plant_wolffia_arrhiza` 분개구리밥 | B/C / `B03` | 엽상체 약 0.5–1.5 × 0.4–1.2 mm; 길이 0.5–1.5× | [상세](../../../../asset/B/B03_plant_wolffia_arrhiza/document/plant_wolffia_arrhiza.md) · [모델](../../../../asset/B/B03_plant_wolffia_arrhiza/document/plant_wolffia_arrhiza_model.md) · [동작](../../../../asset/B/B03_plant_wolffia_arrhiza/document/plant_wolffia_arrhiza_movement.md) |
| `floating_plants` | `plant_salvinia_natans` 생이가래 | B/C / `B04` | 수면 잎 약 8–14 × 5–8 mm; 길이 8–14× (식물상 기재 차이) | [상세](../../../../asset/B/B04_plant_salvinia_natans/document/plant_salvinia_natans.md) · [모델](../../../../asset/B/B04_plant_salvinia_natans/document/plant_salvinia_natans_model.md) · [동작](../../../../asset/B/B04_plant_salvinia_natans/document/plant_salvinia_natans_movement.md) |
| `submerged_plants` | `plant_ceratophyllum_demersum` 붕어마름류 | B/C / `B05` | 줄기 길이·포기 전체 크기는 원자료에 공통 확정치 없음 | [상세](../../../../asset/B/B05_plant_ceratophyllum_demersum/document/plant_ceratophyllum_demersum.md) · [모델](../../../../asset/B/B05_plant_ceratophyllum_demersum/document/plant_ceratophyllum_demersum_model.md) · [동작](../../../../asset/B/B05_plant_ceratophyllum_demersum/document/plant_ceratophyllum_demersum_movement.md) |
| `emergent_plants` | `plant_typha_orientalis` 부들 | B/C / `B06` | 줄기 약 1–1.5 m; 잎 길이 80–130 cm (성체 식물 사례) | [상세](../../../../asset/B/B06_plant_typha_orientalis/document/plant_typha_orientalis.md) · [모델](../../../../asset/B/B06_plant_typha_orientalis/document/plant_typha_orientalis_model.md) · [동작](../../../../asset/B/B06_plant_typha_orientalis/document/plant_typha_orientalis_movement.md) |
| `emergent_plants` | `plant_phragmites_australis` 갈대 | B/C / `B07` | 줄기 약 1–3 m (출처의 대략적인 높이) | [상세](../../../../asset/B/B07_plant_phragmites_australis/document/plant_phragmites_australis.md) · [모델](../../../../asset/B/B07_plant_phragmites_australis/document/plant_phragmites_australis_model.md) · [동작](../../../../asset/B/B07_plant_phragmites_australis/document/plant_phragmites_australis_movement.md) |
| `riparian_herbs` | `plant_persicaria_thunbergii` 고마리 | B/C / `B08` | 뻗는 줄기 길이 약 1 m; 잎 개별 길이 미확인 | [상세](../../../../asset/B/B08_plant_persicaria_thunbergii/document/plant_persicaria_thunbergii.md) · [모델](../../../../asset/B/B08_plant_persicaria_thunbergii/document/plant_persicaria_thunbergii_model.md) · [동작](../../../../asset/B/B08_plant_persicaria_thunbergii/document/plant_persicaria_thunbergii_movement.md) |
| `water` | `env_still_water` 잔잔한 담수 수면 | A+B / `A02` | 수면 넓이·깊이는 장면 설계치; 생물 mm 기준으로 고정 불가 | [상세](../../../../asset/A/A02_env_still_water/document/env_still_water.md) · [모델](../../../../asset/A/A02_env_still_water/document/env_still_water_model.md) · [동작](../../../../asset/A/A02_env_still_water/document/env_still_water_movement.md) |
| `shore` | `env_shore_slope` 연속 물가 경사 | B/C / `A03` | 경사 각도·폭·구배는 선택값; 종별 확인 수치 없음 | [상세](../../../../asset/A/A03_env_shore_slope/document/env_shore_slope.md) · [모델](../../../../asset/A/A03_env_shore_slope/document/env_shore_slope_model.md) · [동작](../../../../asset/A/A03_env_shore_slope/document/env_shore_slope_movement.md) |
| `emergent_substrates` | `env_wet_wood` 젖은 나무·떠 있는 가지 | A / `A04` | 나무 직경·길이 실측치 미확인; 부유/고정 상태 별도 | [상세](../../../../asset/A/A04_env_wet_wood/document/env_wet_wood.md) · [모델](../../../../asset/A/A04_env_wet_wood/document/env_wet_wood_model.md) · [동작](../../../../asset/A/A04_env_wet_wood/document/env_wet_wood_movement.md) |
| `emergent_substrates` | `env_wet_stone` 젖은 돌·자갈 | A / `A05` | 돌·자갈 실제 크기 수치는 원문 미확정 | [상세](../../../../asset/A/A05_env_wet_stone/document/env_wet_stone.md) · [모델](../../../../asset/A/A05_env_wet_stone/document/env_wet_stone_model.md) · [동작](../../../../asset/A/A05_env_wet_stone/document/env_wet_stone_movement.md) |
| `debris` | `env_wet_leaf_litter` 젖은 낙엽·식물 부스러기 | B/C / `A06` | 잎 종·크기·두께 수치는 미선정 | [상세](../../../../asset/A/A06_env_wet_leaf_litter/document/env_wet_leaf_litter.md) · [모델](../../../../asset/A/A06_env_wet_leaf_litter/document/env_wet_leaf_litter_model.md) · [동작](../../../../asset/A/A06_env_wet_leaf_litter/document/env_wet_leaf_litter_movement.md) |
| `underwater` | `env_sediment` 바닥 퇴적물 | B/C / `B09` | 입경·퇴적층 두께·분포는 장소별 미선정 | [상세](../../../../asset/B/B09_env_sediment/document/env_sediment.md) · [모델](../../../../asset/B/B09_env_sediment/document/env_sediment_model.md) · [동작](../../../../asset/B/B09_env_sediment/document/env_sediment_movement.md) |
| `microfood` | `env_algae_patch` 조류 패치 | A / `A07` | 패치 면적·두께·조류 종·생체량 미확정 | [상세](../../../../asset/A/A07_env_algae_patch/document/env_algae_patch.md) · [모델](../../../../asset/A/A07_env_algae_patch/document/env_algae_patch_model.md) · [동작](../../../../asset/A/A07_env_algae_patch/document/env_algae_patch_movement.md) |
| `microfood` | `env_periphyton_biofilm` 부착생물막 | B / `B0A` | 막 두께·면적·조성은 상황별 미확정 | [상세](../../../../asset/B/B0A_env_periphyton_biofilm/document/env_periphyton_biofilm.md) · [모델](../../../../asset/B/B0A_env_periphyton_biofilm/document/env_periphyton_biofilm_model.md) · [동작](../../../../asset/B/B0A_env_periphyton_biofilm/document/env_periphyton_biofilm_movement.md) |
| `microfood` | `env_diatoms_micro` 규조류 미세 표현 | B / `B0B` | 세포·규조 껍질 종별 치수 원문 미제시; 1mm 기준 임의 배율 금지 | [상세](../../../../asset/B/B0B_env_diatoms_micro/document/env_diatoms_micro.md) · [모델](../../../../asset/B/B0B_env_diatoms_micro/document/env_diatoms_micro_model.md) · [동작](../../../../asset/B/B0B_env_diatoms_micro/document/env_diatoms_micro_movement.md) |
| `effects` | `fx_moisture_particles` 물방울·물안개·미세 입자 | C / `E01` | 물방울·입자 크기/속도는 실제 측정치 없이 게임 연출값 | [상세](../../../../asset/E/E01_fx_moisture_particles/document/fx_moisture_particles.md) · [모델](../../../../asset/E/E01_fx_moisture_particles/document/fx_moisture_particles_model.md) · [동작](../../../../asset/E/E01_fx_moisture_particles/document/fx_moisture_particles_movement.md) |

## 2. 구역 6개·장면 프리셋 3개 — 조합 규칙(독립 메시 아님)
| ID | 구성·역할 | 우선 연결 객체 |
|---|---|---|
| `Z0_water_surface` | 수면 생활 핵심 | `env_still_water`, `env_algae_patch` |
| `Z1_floating_mat` | 부유식물·산란 | `plant_lemna_minor` 외 4종 부유식물 |
| `Z2_emergent_objects` | 젖은 고형 발판 | `env_wet_wood`, `env_wet_stone`, `env_wet_leaf_litter` |
| `Z3_wet_bank` | 경사 진흙·자갈 | `env_shore_slope`, `env_wet_leaf_litter`, 정수식물 |
| `Z4_riparian_vegetation` | 젖은 육상 식생 | `plant_typha_orientalis`, `plant_phragmites_australis`, `plant_persicaria_thunbergii` |
| `Z5_shallow_underwater` | 수중 배경 | `env_sediment`, `plant_ceratophyllum_demersum`, `env_diatoms_micro` |
| `POND_CORE` | 수면+나도좀개구리밥+조류+잔가지 | `env_still_water`, `plant_lemna_minor`, `env_algae_patch`, `env_wet_wood` |
| `WATER_EDGE` | 수면→젖은 물가 연속 경사 | `env_shore_slope`, `env_wet_stone`, `env_still_water` |
| `KOREAN_SHORE_OPTION` | 한국 담수의 **가상 식생 선택안** | `plant_lemna_perpusilla`, `plant_spirodela_polyrhiza`, 정수식물 등 |

> 이 9개 ID는 **컴포지션·프리셋**이므로 `3D/2D/document/sheet` 하위의 독립 생물/환경 메시로 계산하지 않는다. 각 구역·장면의 배치·물리·변형은 [조합 규칙](zone_scene_layout.md)에서 관리한다.

## 3. 공통 제작·검증
- 상세 문서: 국명/학명, 원문 치수, 등급(A/B/C/U), 기질 이용, 상호작용 범위.
- 모델 문서: 부위별 메시, 표면/변형/LOD, 기준점, 실측과 모델링 임의값 구분.
- 동작 문서: 정적/부유/바람/수위/섭식/이펙트의 상태·클립, `pre–mid–end`, 물리 소유권.
- `B`는 플레이어 비상호작용 배경이고, `E`는 효과. `A`의 보행·섭식·산란은 근거·설계 수준을 이벤트별로 구분한다.
- 테스트 `NOT_RUN`: 본 ZIP은 모델·애니메이션 파일을 생성하지 않으며 문서/계약만 생성한다.
- 입력 참조: `toktogi_habitat.md`, `AssetLabelRule(1).txt`, `AssetSize(2).md`, `spider_pardosa(2).md`, `spider_pardosa_model(1).md`, `spider_pardosa_movement(1).md`.
