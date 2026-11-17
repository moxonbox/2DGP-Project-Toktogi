---
object_id: plant_typha_orientalis
asset_class_candidate: B
asset_folder_code: "B06"
group: emergent_plants
taxon: "Typha orientalis"
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 부들 (*Typha orientalis*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B06`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_typha_orientalis` / `emergent_plants` |
| 명칭 | 부들 — *Typha orientalis* |
| 배치 카테고리 / 폴더 코드 | `B` / `B06` |
| 구역 | `Z3_wet_bank / Z4_riparian_vegetation` |
| 톡토기 연계 | **B/C** — 물가의 높은 정수식물·그늘 형성; 톡토기와의 직접 접촉은 미확인 [H10] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 줄기 약 1–1.5 m; 잎 길이 80–130 cm (성체 식물 사례) |
| 실루엣 | 물가 진흙에서 세워진 긴 정수성 식물 |
| 고유 식별점 | 기다란 띠모양 잎, 직립 줄기, 원통형 갈색 꽃이삭 |
| 색·표면 | 녹색 잎·황록~갈색 줄기·갈색 꽃이삭; 구체 색상 미정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `vertical_stem` | 핵심 형상 |
| `strap_leaves` | 분리 메시·재질 또는 선택 세부 요소 |
| `cylindrical_inflorescence` | 분리 메시·재질 또는 선택 세부 요소 |
| `basal_parts` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 잎 위주 |
| Variant 2 | 갈색 꽃이삭 있음 |
| Variant 3 | 군락 저밀도/고밀도 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 물가의 높은 정수식물·그늘 형성; 톡토기와의 직접 접촉은 미확인 [H10] [H17]
- **게임 설계:** `background_silhouette / shade_cast`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 지면에 고정되는 줄기 기반; 물선 위치는 배치 장면과 연동
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `rooted` |
| `motion_profile` | `wind_sway` |
| `anchor` | `root_base / leaf_tips` |
| `habitat_zone` | `Z3_wet_bank / Z4_riparian_vegetation` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_typha_orientalis
asset_class_candidate: B
folder_code: "B06"
evidence_level: "B/C"
zone: "Z3_wet_bank / Z4_riparian_vegetation"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_typha_orientalis_movement.md
model_spec: plant_typha_orientalis_model.md
```
## 7. 미확인 값·검수
- **미확인:** 꽃이삭 지름·잎 폭·바람 응답량·지역 밀도.
- **동정/구조:** 실물 미터 치수를 톡토기 1mm와 혼동 금지; 원통 꽃이삭 확인.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B06`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H10] [한국민족문화대백과, 부들](https://encykorea.aks.ac.kr/Article/E0024131)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
