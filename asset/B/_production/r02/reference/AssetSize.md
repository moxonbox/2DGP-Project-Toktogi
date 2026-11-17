---
document: AssetSize.md
version: "1.1"
date: "2026-11-17"
project: 2DGP
reference_object: toktogi
reference_species: Sminthurides aquaticus
reference_length_mm: 1.0
reference_stage: adult_female_maximum
measurement_policy: biological_body_length_with_measure_kind
asset_profile: C011_integrated-r5_framework-r4
status: biological_reference_and_measured_prototype_dimensions
---

# AssetSize — 물알둥근톡토기 기준 천적 객체 상대 크기 명세서

> **용도** · 생물 체장 비교와 현행 C011의 Blender·2D 표시·충돌 크기를 기록한다. 생물 수치는 기존 원자료의 측정 기준대로 인용하고, 에셋 수치는 저장된 프로토타입 파일에서 따로 측정한다.
> **범위** · 거미류 3객체, 수면 노린재류 4객체, 반날개류·응애류·어류·양서류 각 1객체와 기준 톡토기 C011. 천적 후보의 외형 자료는 [11개 모델 명세 인덱스](../../asset/C/document/predator_model_objects_index.md)에 있다.

## 1. 기준 객체와 계산 규칙

| ID / 단계 | 실측 몸길이 | 기준 대비 | 해석 |
|---|---:|---:|---|
| `toktogi` — 암컷 성체 | **최대 약 1.0 mm** | **1.0×** | 본 문서의 고정 비교 기준. 개체군 평균이 아님 [B1] |
| `toktogi` — 수컷 성체 | 약 **0.3–0.4 mm** | **0.3–0.4×** | 생물 기준값. 제작 시 성별·크기 프리셋을 별도로 결정 [B1] |
| `toktogi` — 부화 직후 | 약 **0.1 mm** | 약 **0.1×** | 자연사 촬영자의 대략적 추정; 정밀 실측값 아님 [B2] |

- **몸길이 배율** `ratio_to_toktogi_female = measured_body_length_mm / 1.0` (분모는 암컷 상한 1 mm).
- **수컷 대비 배율**은 선택 사항: 포식자 길이 `L mm`라면 `L / 0.4` ~ `L / 0.3`배. 이 수치는 같은 개체 크기 조합의 관찰 결과가 아니다.
- 몸길이는 일반적으로 다리·더듬이·날개를 펼친 **외접 크기가 아니다**. 어류는 `SL`(표준체장, 꼬리지느러미 제외), 개구리는 `SVL`(주둥이–항문 길이), 응애는 `IL`(몸통 길이와 **동일하지 않은** 체격 지표)을 따로 표시한다.
- 범위는 **출처의 관찰·기재 범위**이지 표본 전체의 최소/최대나 자연적인 성장 범위를 보증하지 않는다. 특정 종이 정해지지 않은 속/과 객체에 일괄 적용하지 않는다.

## 2. 거미류 (3개 객체)

| 객체 ID / 적용 사례 | 몸길이 (mm) | 톡토기 대비 | 근거 조건 |
|---|---:|---:|---|
| `spider_pardosa` — *P. amentata* ♂ | 5.5–6.5 | 5.5–6.5× | **속 객체의 종 사례**. 다리 제외 [S1] |
| ↳ *P. amentata* ♀ | 6.0–8.0 | 6.0–8.0× | 상동 [S1] |
| ↳ *P. agrestis* ♂ | 4.5–5.0 | 4.5–5.0× | 별도 종 사례 [S2] |
| ↳ *P. agrestis* ♀ | 약 5.0 | 약 5.0× | 별도 종 사례 [S2] |
| `spider_linyphiidae` — *Erigone atra* ♂ / ♀ | 1.9–2.5 / 1.8–2.8 | 1.9–2.5× / 1.8–2.8× | **과 객체의 소형 종 사례** [S3] |
| ↳ *Bathyphantes gracilis* ♂ / ♀ | 1.5–2.0 / 1.9–2.5 | 1.5–2.0× / 1.9–2.5× | 소형·저층식생 거미 사례 [S4] |
| ↳ *Linyphia triangularis* ♂ / ♀ | 4.6–7.0 / 5.0–8.0 | 4.6–7.0× / 5.0–8.0× | 상대적으로 큰 그물형 사례 [S5] |
| `spider_triaeris_stenaspis` — 성체 ♀ | **1.47 / 1.7 / 1.8** | **1.47 / 1.7 / 1.8×** | 서로 다른 표본/종 카드의 **개별 기록**. 수컷 크기 미정 [S6][S7] |

- `spider_pardosa`는 속, `spider_linyphiidae`는 과 수준이므로 **하위 종을 선택해야** 최종 에셋 몸길이를 확정할 수 있다. 예시들을 합친 4.5–8.0mm 또는 1.5–8.0mm를 분류군의 보편 범위로 해석하지 않는다.
- 거미의 **다리 편길이, 체폭, 체고, 실젖·촉지 포함 외접치수는 미확정**이다. 몸길이 배율만으로 균일한 체형을 만들어서는 안 된다.

## 3. 수면 노린재류 (4개 객체)

| 객체 ID / 형태 | 몸길이 (mm) | 톡토기 대비 | 근거 조건 |
|---|---:|---:|---|
| `predator_hydrometra_stagnorum` — 성체 | **9.0–12.5**; 자료별 약 9–13 | **9.0–12.5×**; 대략 최대 13× | 유럽 종 카드의 체장 [N1][N2] |
| `predator_hydrometra_martini` — 성체 ♂ | **7.7–8.5** | **7.7–8.5×** | 1981년 미네소타 표본 `n=10` [N3] |
| ↳ 성체 ♀ | **8.8–10.15** | **8.8–10.15×** | 같은 논문 `n=10` [N3] |
| `predator_microvelia_reticulata` — **무시형** 성체 | **1.4–1.6** | **1.4–1.6×** | 날개가 없는 성충형 [N4] |
| ↳ **장시형** 성체 | **1.6–1.9** | **1.6–1.9×** | 날개가 긴 성충형 [N4] |
| `predator_mesovelia_vittigera` — 성체 | **2.0–3.5** | **2.0–3.5×** | 태국 표본 기반 종 기재; 한국 개체군 평균 아님 [N5] |

- `Hydrometra` **두 종은 같은 속**이지만 수치를 서로 대체하지 않는다. *H. martini*에서 별도 측정된 가슴 최대폭은 ♂ **0.475–0.55 mm**, ♀ **0.60–0.70 mm**(다리 기절 제외)다 [N3].
- *Microvelia*의 **무시형 성충은 약충이 아니다**. 두 날개형은 별도 메시/크기 프리셋으로 취급한다.

## 4. 딱정벌레·응애·어류·양서류 (4개 객체)

| 객체 ID / 적용 사례 | 몸길이 (mm) | 톡토기 대비 | 근거 조건 |
|---|---:|---:|---|
| `predator_stenus` — *Stenus koreanus* | **3.2–3.3** | **3.2–3.3×** | 속 객체의 **한국산 1종 사례**. 속 전체의 대표 체장 아님 [O1] |
| `predator_pergamasus_crassipes` — 성체 | **종별 몸길이 미확정** | **확정 불가** | 기존 모델의 0.8–1.5mm는 속 사진 추정값. 하단 IL 자료 참조 [O2] |
| `predator_gambusia_holbrooki` — 수컷 최대 **SL** | **35 mm** | **최대 35×** | 표준체장 상한값, 평균 아님 [O3] |
| ↳ 암컷 최대 **SL** | **60 mm** | **최대 60×** | 표준체장 상한값 [O3] |
| `predator_rana_temporaria` — 성체 길이 안내 | **약 60–80 mm** | **약 60–80×** | 아일랜드 자연사 안내 값. SVL 성격이나 원문 측정법 상세 미정 [O4] |
| ↳ 대형 성체 길이 사례 | **최대 약 110 mm** | **최대 약 110× (해당 출처)** | Naturalis 종 카드의 상한. 모든 개체군의 절대 최대값 아님 [O7] |

- **응애의 정량 보조자료:** Bowman(2021) 표 3은 *P. crassipes*의 **idiosomal index(IL) 1,144.8 μm = 1.1448 mm**를 제시한다 [O2]. IL은 앞다리와 뒷다리 기부 사이의 복측 지표이므로 머리·몸통의 실제 전체 길이와 **동일하지 않다**. `1.145×`는 *참고 지표값*일 뿐 에셋 몸길이의 검증된 배율로 채택하지 않는다.
- *Gambusia* 암컷의 **꼬리지느러미 포함 전장(TL)** 상한은 자료에 따라 약 **80mm(80×)**로 제시된다 [O5]. 이를 SL 60mm와 동일한 축의 수치로 취급하거나 무조건 60→80mm 보정하지 않는다.
- *Rana temporaria*의 실제 SVL은 개체군에 따라 달라진다. 스위스 고산 연못 연구는 수컷 **63–85mm**, 암컷 **65–94mm**를 보고했다 [O6]. 다른 영국 안내에는 **80–130mm**도 제시돼 출처별 크기 차이가 있다 [O8]. 이 값들을 합쳐 전 세계 공통 평균이나 확정 최대값으로 사용하지 않는다. 올챙이는 별도 프리셋으로 취급한다.

## 5. 현행 C011에서 확인한 크기

생물 비교의 1.0은 암컷 성체 상한 1 mm에서 정한 무차원 기준이다. 아래 Blender 치수는 제작 단위 BU, 스프라이트와 Capsule은 논리 픽셀로 기록한다.

### 5.1 Blender 원본과 중립 자세

| 항목 | 확인값 | 측정 조건 |
| --- | --- | --- |
| 단위 | Metric, Unit Scale 1.0. 메시·리그·루트 Scale 각 (1, 1, 1) | Blender 단위 설정. 종의 실세계 mm 환산 계수는 별도 미확정이다. |
| 원본 메시 전체 외접 크기 | **1.207 × 0.864 × 0.825 BU** | Toktogi_Skinned 로컬 XYZ의 rest 정점. 다리·더듬이 등 부속 기관을 포함한다. |
| 대기 평가 메시 전체 외접 크기 | **1.172 × 0.871 × 0.873 BU** | 통합 Blend에서 idle/left, Blender 프레임 1의 평가 메시 로컬 XYZ. 방향이 바뀌면 월드 외접 크기도 달라진다. |
| 몸길이 비교용 메시 대용값 | **0.965396 BU** | idle/left 프레임 1에서 M_Toktogi_Weathered 면에 속하며 최대 웨이트 그룹이 Body 또는 Head인 정점 778개의 로컬 X 범위(최대−최소). 눈 머티리얼·기관 그룹을 제외한 제작용 대용값이다. |
| 보조 개체 | 관찰 Action마다 크기가 달라진다. | 프레임 1의 모델 월드 외접 X 길이는 obs_female_contact에서 0.984 BU, obs_dance에서 0.471 BU다. 두 값은 연출 자세의 외접값이며 생물 프리셋에는 별도 근거를 둔다. |

측정은 Blender 5.3의 통합 작업본에서 수행했다. 몸길이 대용값을 공유 기준으로 쓰려면 다른 모델도 등가의 머리 앞끝·몸통 뒤끝과 전후축을 기록한다. 웨이트나 머티리얼을 재분할하면 대용값을 다시 확인한다. [통합 Blend](../../asset/C/C011_toktogi/3D/toktogi_unified.blend)

### 5.2 2D 출력의 크기와 여백

- integrated-r5 기반의 고정 직교 카메라 스케일은 1.78 BU다. 128×128px 타일의 환산은 약 0.01390625 BU/px다. 이는 카메라 평면의 환산이며 정점의 3D 축 길이는 카메라 각도와 포즈에 따라 다른 스팬으로 투영된다.
- 피벗은 좌상단 기준 (64, 88)px다. 아틀라스 패딩 2px와 타일 내부의 투명 여백은 각각 기록한다. 로더용 PNG는 128×640px로, 128×128px 패스 5장이 세로로 쌓인다.
- 표는 Alpha > 0인 픽셀의 외접 사각형을 스캔했다. Sprite는 표시용 외곽선을 포함하고, Base는 재조명에 쓰는 표면 범위를 나타낸다. 폭·높이 및 여백의 범위는 각각 독립적으로 집계했다.

| 대상 | Sprite 외접 폭 × 높이 | Base 외접 폭 × 높이 | Sprite 최소 타일 여백 |
| --- | --- | --- | --- |
| idle/left 표본 0 | **93 × 71px** | **89 × 67px** | 16px |
| idle/right 표본 0 | **92 × 59px** | **88 × 55px** | 17px |
| 원본 1,444셀 전체 | 폭 66–122px, 높이 49–97px | 폭 62–118px, 높이 45–93px | 3px |
| 원본 중 단일 개체·소품 없음 1,256셀 | 폭 66–104px, 높이 51–97px | 폭 62–100px, 높이 47–93px | 3px |
| 보조 930셀 | 폭 58–108px, 높이 50–109px | 폭 54–104px, 높이 46–105px | 2px |

원본의 최대 폭 122px는 2개체 관찰 장면 obs_rebuff/left/0이다. 보조의 2px 여백은 ground_spin_left/left/12에서 확인했다. 따라서 원본 기록의 3px 여백을 전체 배포 파일의 하한으로 적용하려면 보조 출력도 검사해야 한다. 측정한 번들 2,374셀은 C011의 개별 PNG와 바이트 단위로 일치했다. [출력 manifest](../../asset/C/C011_toktogi/2D/integrated-r5/playable_manifest.json) · [원본 ZIP](../../prototype/toktogi_assets.zip) · [보조 ZIP](../../prototype/toktogi_runtime_poses.zip)

### 5.3 게임 표시와 충돌

- 플레이 창 1280×744px, 논리 필드 960×560px에서 128px 셀을 **1×**로 표시한다. 셀 좌상단은 필드 오프셋에 게임 위치를 더하고 피벗 (64,88)을 뺀 좌표다. F2의 **1×/2×/3×**는 검수 확대다. [플레이 렌더러](../../prototype/play_view.py) · [F2 검수](../../prototype/motion_viewer.py)
- 이동 Capsule은 반경 **14px**, 너비 **28px**, 전체 높이 **52px**다. 게임 위치의 y를 발 기준으로 삼는다. 발끝·입·공격 등의 마커 및 효과 범위는 각각의 규칙으로 다룬다. 시각 실루엣 확대는 충돌이나 판정 범위의 변경 근거가 아니다. [충돌 코드](../../prototype/physics.py) · [게임 판정](../../prototype/game.py)
- 이 값은 현행 프로토타입이다. 최종 시점·좌표·피벗·Normal 변환 계약 DEC-06은 보류다. [플레이 명세](game-design/022_toktogi_playable_action_animation_spec.md)

## 6. 다른 에셋의 크기 결정과 검증

| 단계 | 기록과 계산 |
| --- | --- |
| 1. 생물 기준 선택 | measure_kind, 출처, 분류·표본·성별·단계·날개형을 보존한다. 생물 비교값은 길이 mm ÷ 1.0 mm다. 체장·SL·TL·SVL·IL 계열은 구분하고 대용 지표는 표시한다. |
| 2. 제작 기준 설정 | 실측 재현 모드라면 length_m = length_mm × 0.001이다. C011 상대 연출 모드라면 호환 가능한 체장 기준을 정하고 모델 앞·뒤 기준점의 길이를 먼저 잰다. 현행 자산의 mm↔BU는 자동으로 채우지 않는다. |
| 3. 메시 크기 결정 | 현행 C011 대용값을 선택한 경우, 예시 목표 체장(BU) = 0.965396 × 생물 길이비 × 별도 연출 계수. 가져온 모델의 변환 축·단위를 정리한 후 목표 체장 ÷ 현재 기준점 길이로 전체를 균일 스케일한다. 부속 기관 비율은 별도 근거를 사용한다. |
| 4. 카메라와 타일 결정 | 지원 방향·극단 자세의 투영 외접 범위와 피벗·마커를 실제 표시 크기에서 검사한다. 큰 에셋의 셀 예산·카메라·연출 축소값을 정하고 게임 로더가 해당 규격을 지원하는지 확인한다. |
| 5. 판정과 출력 검증 | 시점별 Sprite/Base 외접값, 투명 여백, 지지발 접지, 작업 접점, 논리 충돌 크기와 측정 표본을 기록한다. 카메라·피벗·리그를 바꾸면 관련 패스·마커·연결 표본도 검증한다. |

예를 들어 생물 길이비 6.0을 C011 몸길이 대용값에 적용하면 약 5.79 BU다. 이는 균일 스케일 계산 예시이며, 실제 에셋의 표시 크기는 시점과 타일 적합성 검수에서 결정한다.

```yaml
asset_id: predator_microvelia_reticulata
folder_id: C231_microvelia_reticulata
reference_species: Microvelia reticulata
life_stage: adult
wing_morph: apterous
measure_kind: body_length
body_length_mm: {min: 1.4, max: 1.6}
ratio_to_toktogi_female: {min: 1.4, max: 1.6}
reference_source: N4
model_body_length_bu: null
display_scale: null
projected_bounds_px: null
collision_profile: null
```

생물 길이 외에 근거가 필요한 체폭·체고·다리 편길이와 미측정 에셋 값은 null로 남긴다. 길이비는 질량·부피·포식 성공률·생태 관계의 근거로 삼지 않는다. [에셋 제작·재검수 절차](AssetPipeLine.md)

## 7. 출처 및 기존 모델 명세서 연결

| 코드 | 출처 | 대상 |
|---|---|---|
| [B1] | [톡토기 외형 명세](reference/toktogi_model.md) §2 및 [종합 생물 명세](reference/toktogi.md) §3 | 톡토기 암수 몸길이 |
| [B2] | [A Chaos of Delight 자연사 관찰](https://www.chaosofdelight.org/blog/springtail-of-the-month-sminthurides-aquaticus/31/8/2020) | 부화 직후 관찰값 |
| [S1] | [Spiders of Europe — *Pardosa amentata*](https://araneae.nmbe.ch/data/153/Pardosa_amentata) | 늑대거미 사례 |
| [S2] | [Spiders of Europe — *Pardosa agrestis*](https://araneae.nmbe.ch/data/82/Pardosa_agrestis) | 늑대거미 사례 |
| [S3] | [Spiders of Europe — *Erigone atra*](https://araneae.nmbe.ch/data/234/Erigone_atra) | 접시거미과 소형 |
| [S4] | [Spiders of Europe — *Bathyphantes gracilis*](https://araneae.nmbe.ch/data/525/Bathyphantes_gracilis) | 접시거미과 소형 |
| [S5] | [Spiders of Europe — *Linyphia triangularis*](https://araneae.nmbe.ch/data/1256/Linyphia_triangularis) | 접시거미과 대형 |
| [S6] | [Spiders of Europe — *Triaeris stenaspis*](https://araneae.nmbe.ch/data/1327/Triaeris_stenaspis) | *Triaeris* 암컷 1.8mm |
| [S7] | [AMNH Oonopidae PBI 표본](https://research.amnh.org/oonopidae/taxonomy/speciesdescription.php?fromall=fromall&genusid=68&speciesid=2118) 및 [C213 모델 명세](../../asset/C/C213_spider_stenaspis/document/spider_triaeris_stenaspis_model.md) | *Triaeris* 다른 표본 크기 |
| [N1] | [Wanzen-im-Ruhrgebiet — *Hydrometra stagnorum*](https://www.wanzen-im-ruhrgebiet.de/artenprofile/hydrometridae/hydrometra-stagnorum/) | 9–12.5mm |
| [N2] | [Warwickshire Wildlife Trust](https://www.warwickshirewildlifetrust.org.uk/wildlife-explorer/common-water-measurer) | 약 9–13mm |
| [N3] | [Bennett & Cook (1981) *Semiaquatic Hemiptera of Minnesota*](https://conservancy.umn.edu/bitstreams/6692aaac-8c04-4da7-af65-9b444f8523cc/download), p.23 | *H. martini* 암수 표본 |
| [N4] | [Aquatic Bugs — *Microvelia reticulata*](https://aquaticbugs.com/microvelia-reticulata/) | 날개형별 몸길이 |
| [N5] | [Diversity (2022), 태국 *Mesovelia* 종 연구](https://www.mdpi.com/1424-2818/14/6/466) | 2–3.5mm |
| [O1] | [Korean Journal of Applied Entomology — *Stenus koreanus*](https://www.entomology2.or.kr/journal/article.php?code=32948) | 한국산 종 사례 |
| [O2] | [Bowman (2021), *Experimental and Applied Acarology*, 표 3 및 IL 정의](https://pmc.ncbi.nlm.nih.gov/articles/PMC8085810/) | 응애 IL 지표, 체장 아님 |
| [O3] | [Fishes of Australia — *Gambusia holbrooki*](https://fishesofaustralia.net.au/home/species/3636) | 암수 SL 상한 |
| [O4] | [Herpetological Society of Ireland — Common Frog](https://thehsi.org/native-reptiles-and-amphibians/common-frog/) | 성체 6–8cm 소개 |
| [O5] | [US FWS — Eastern Mosquitofish 평가](https://www.fws.gov/sites/default/files/documents/Ecological-Risk-Screening-Summary-Eastern-Mosquitofish.pdf) | 대체 TL 값 및 측정 차이 |
| [O6] | [고산지대 *Rana temporaria* 개체군 생활사 연구](https://sonar.ch/global/documents/263753) | 암수 SVL 관찰 범위 |
| [O7] | [Naturalis — *Rana temporaria* 종 카드](https://reptiles-and-amphibians.linnaeus.naturalis.nl/linnaeus_ng/app/views/species/nsr_taxon.php?id=98989) | 상한 11cm 종 소개 |
| [O8] | [Woodland Trust — Common frog](https://www.woodlandtrust.org.uk/trees-woods-and-wildlife/animals/reptiles-and-amphibians/common-frog/) | 별도 기관의 8–13cm 소개; 측정법 주의 |

> **유지 원칙** · 각 객체의 구조·외형은 [모델 명세 인덱스](../../asset/C/document/predator_model_objects_index.md)에서 관리한다. 이 문서에서는 길이 차이를 성별·표본·측정법과 함께 병기하고, 에셋의 제작 단위와 표시·충돌 값을 프로필별로 기록한다.
