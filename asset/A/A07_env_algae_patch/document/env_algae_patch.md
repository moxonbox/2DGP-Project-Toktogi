---
object_id: env_algae_patch
asset_class_candidate: A
asset_folder_code: "A07"
group: microfood
taxon: null
evidence_level: "A"
version: "1.0"
source: toktogi_habitat.md
---
# 조류 패치 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `A07`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_algae_patch` / `microfood` |
| 명칭 | 조류 패치 |
| 배치 카테고리 / 폴더 코드 | `A` / `A07` |
| 구역 | `Z0_water_surface / Z2_emergent_objects` |
| 톡토기 연계 | **A** — 물알둥근톡토기가 조류를 먹는 행동은 직접 자연사 관찰로 보고됨 [H14] [H01] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 패치 면적·두께·조류 종·생체량 미확정 |
| 실루엣 | 물체 상면·측면의 얇은 녹색~갈색 부착 조류층 |
| 고유 식별점 | 독립 거대식물 잎이 아니라 표면에 붙은 국소 군집 |
| 색·표면 | 녹색~갈색 얇은 피막; 생물학적 조성은 미결정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `patch_decal` | 핵심 형상 |
| `patch_mask` | 분리 메시·재질 또는 선택 세부 요소 |
| `optional_thin_geometry` | 분리 메시·재질 또는 선택 세부 요소 |
| `food_anchor` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 작은 패치 |
| Variant 2 | 번진 패치 |
| Variant 3 | 섭식 후 시각 변화[설계] |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 물알둥근톡토기가 조류를 먹는 행동은 직접 자연사 관찰로 보고됨 [H14] [H01] [H17]
- **게임 설계:** `feed_on[A·조류 섭식] / resource_deplete[설계, 양 미확인]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 기질 메시 위 정렬된 패치; 실제 부피·먹이량을 임의 설정하지 않음
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `attached` |
| `motion_profile` | `patch_state` |
| `anchor` | `food_point / substrate_uv` |
| `habitat_zone` | `Z0_water_surface / Z2_emergent_objects` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_algae_patch
asset_class_candidate: A
folder_code: "A07"
evidence_level: "A"
zone: "Z0_water_surface / Z2_emergent_objects"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_algae_patch_movement.md
model_spec: env_algae_patch_model.md
```
## 7. 미확인 값·검수
- **미확인:** 조류 종명·일일 소비량·재생률·식용성의 보편화.
- **동정/구조:** 이끼 잎사귀처럼 모델링하지 않음; 특정 조류 주식으로 확정 금지.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `A07`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H14] [Andy Murray (2020), S. aquaticus 섭식 사진](https://www.chaosofdelight.org/blog/springtail-of-the-month-sminthurides-aquaticus/31/8/2020)
- [H01] [Schneider et al. (2021), GigaScience](https://doi.org/10.1093/gigascience/giab035)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
