---
object_id: plant_salvinia_natans
asset_class_candidate: B
asset_folder_code: "B04"
group: floating_plants
taxon: "Salvinia natans"
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 생이가래 (*Salvinia natans*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B04`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_salvinia_natans` / `floating_plants` |
| 명칭 | 생이가래 — *Salvinia natans* |
| 배치 카테고리 / 폴더 코드 | `B` / `B04` |
| 구역 | `Z1_floating_mat / Z5_shallow_underwater` |
| 톡토기 연계 | **B/C** — 부유식물층의 이질성·수중 그림자 추가; 대상 톡토기 직접 이용 미확인 [H08] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 수면 잎 약 8–14 × 5–8 mm; 길이 8–14× (식물상 기재 차이) |
| 실루엣 | 두 부유 잎과 잘게 갈라진 수중 잎을 가진 부유 양치식물 |
| 고유 식별점 | 표면 발수성 털; 아래로 분지된 수중 잎은 진짜 뿌리와 구분 |
| 색·표면 | 녹색 부유 잎, 발수성 표면; 수중 갈래 구조는 더 어두울 수 있으나 수치 미정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `floating_leaf_L/R` | 핵심 형상 |
| `divided_submerged_frond` | 분리 메시·재질 또는 선택 세부 요소 |
| `stem` | 분리 메시·재질 또는 선택 세부 요소 |
| `surface_hairs` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 잎 쌍 |
| Variant 2 | 확장 군락 |
| Variant 3 | 발수성 털 강조 LOD |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 부유식물층의 이질성·수중 그림자 추가; 대상 톡토기 직접 이용 미확인 [H08] [H17]
- **게임 설계:** `background_floating / vegetation_shade`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 물 표면에 뜬 잎과 물속 갈라진 잎의 접촉층을 구별
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `floating` |
| `motion_profile` | `ambient_float` |
| `anchor` | `floating_pair / submerged_frond` |
| `habitat_zone` | `Z1_floating_mat / Z5_shallow_underwater` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_salvinia_natans
asset_class_candidate: B
folder_code: "B04"
evidence_level: "B/C"
zone: "Z1_floating_mat / Z5_shallow_underwater"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_salvinia_natans_movement.md
model_spec: plant_salvinia_natans_model.md
```
## 7. 미확인 값·검수
- **미확인:** 뿌리와 수중 잎 혼동, 종별 부력·파동 계수, 대상 종 산란.
- **동정/구조:** 떠 있는 잎 2개와 수중 잎 구조를 유지; 단일 뿌리처럼 모델링 금지.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B04`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H08] [World Flora Online, Salvinia natans](https://www.worldfloraonline.org/taxon/wfo-0001117304)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
