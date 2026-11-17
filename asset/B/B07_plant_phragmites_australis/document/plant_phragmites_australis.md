---
object_id: plant_phragmites_australis
asset_class_candidate: B
asset_folder_code: "B07"
group: emergent_plants
taxon: "Phragmites australis"
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 갈대 (*Phragmites australis*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B07`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_phragmites_australis` / `emergent_plants` |
| 명칭 | 갈대 — *Phragmites australis* |
| 배치 카테고리 / 폴더 코드 | `B` / `B07` |
| 구역 | `Z3_wet_bank / Z4_riparian_vegetation` |
| 톡토기 연계 | **B/C** — 수면 가장자리의 높은 식생 경관·그늘 제공; 톡토기 직접 이용 미확인 [H11] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 줄기 약 1–3 m (출처의 대략적인 높이) |
| 실루엣 | 수변에 솟은 긴 직립 줄기와 좁고 긴 잎 |
| 고유 식별점 | 지하줄기에서 무리 지어 자람; 끝부분에 원뿔꽃차례 |
| 색·표면 | 녹색 잎·담갈색 마른 줄기·갈색 계열 꽃차례 등 계절 변이 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `tall_cane` | 핵심 형상 |
| `narrow_leaves` | 분리 메시·재질 또는 선택 세부 요소 |
| `top_panicle` | 분리 메시·재질 또는 선택 세부 요소 |
| `rhizome_hint_optional` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 새순 |
| Variant 2 | 꽃차례 있음 |
| Variant 3 | 마른 줄기/살아 있는 줄기 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 수면 가장자리의 높은 식생 경관·그늘 제공; 톡토기 직접 이용 미확인 [H11] [H17]
- **게임 설계:** `background_silhouette / vegetation_occlusion`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 지면 고정; 촬영 영역을 덮지 않도록 원거리 LOD 활용
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `rooted` |
| `motion_profile` | `wind_sway` |
| `anchor` | `base / panicle_tip` |
| `habitat_zone` | `Z3_wet_bank / Z4_riparian_vegetation` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_phragmites_australis
asset_class_candidate: B
folder_code: "B07"
evidence_level: "B/C"
zone: "Z3_wet_bank / Z4_riparian_vegetation"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_phragmites_australis_movement.md
model_spec: plant_phragmites_australis_model.md
```
## 7. 미확인 값·검수
- **미확인:** 개별 줄기 두께·잎맥/꽃차례 치수, 계절별 무늬, 거친 정도.
- **동정/구조:** 원뿔꽃차례와 부들 원통 꽃이삭 구별.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B07`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H11] [국립수목원 생물도감, 갈대](https://www.bris.go.kr/portal/book/childIlustbkDetailPopup.do?ilustbkNo=96&menuId=114)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
