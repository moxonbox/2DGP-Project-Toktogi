---
object_id: env_wet_leaf_litter
asset_class_candidate: A
asset_folder_code: "A06"
group: debris
taxon: null
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 젖은 낙엽·식물 부스러기 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `A06`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_wet_leaf_litter` / `debris` |
| 명칭 | 젖은 낙엽·식물 부스러기 |
| 배치 카테고리 / 폴더 코드 | `A` / `A06` |
| 구역 | `Z2_emergent_objects / Z3_wet_bank` |
| 톡토기 연계 | **B/C** — 일반 수변의 자연적 부스러기; 물알둥근톡토기의 특정 필수 먹이로 확인되지 않음 [H12] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 잎 종·크기·두께 수치는 미선정 |
| 실루엣 | 물에 걸친 구부러진 잎, 물먹은 엽편과 작은 식물 부스러기 |
| 고유 식별점 | 가시적인 잎맥·자연스러운 말림·찢김·부분 침수 |
| 색·표면 | 녹갈~갈색 잎·젖음띠; 계절색은 식물종 미결정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `leaf_plane_thickened` | 핵심 형상 |
| `curled_edge` | 분리 메시·재질 또는 선택 세부 요소 |
| `vein_normal` | 분리 메시·재질 또는 선택 세부 요소 |
| `wetline_mask` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 떠 있는 낙엽 |
| Variant 2 | 걸쳐 있는 낙엽 |
| Variant 3 | 젖은 바닥 낙엽 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 일반 수변의 자연적 부스러기; 물알둥근톡토기의 특정 필수 먹이로 확인되지 않음 [H12] [H17]
- **게임 설계:** `optional_walk_on[설계] / drift_if_float[설계]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 부유 잎과 바닥 고정 잎은 물리 상태 분리; 보행 허용 여부도 별도
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `wet` |
| `motion_profile` | `float_or_fixed` |
| `anchor` | `leaf_center / edge` |
| `habitat_zone` | `Z2_emergent_objects / Z3_wet_bank` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_wet_leaf_litter
asset_class_candidate: A
folder_code: "A06"
evidence_level: "B/C"
zone: "Z2_emergent_objects / Z3_wet_bank"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_wet_leaf_litter_movement.md
model_spec: env_wet_leaf_litter_model.md
```
## 7. 미확인 값·검수
- **미확인:** 잎 종·두께·부력·분해율·톡토기 먹이 이용.
- **동정/구조:** 기본 먹이로 등록하지 않음; 출현 근거 B/C 유지.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `A06`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H12] [Intermittent rivers 생태학 리뷰 (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9542210/)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
