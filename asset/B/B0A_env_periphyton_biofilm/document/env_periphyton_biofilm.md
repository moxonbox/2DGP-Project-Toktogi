---
object_id: env_periphyton_biofilm
asset_class_candidate: B
asset_folder_code: "B0A"
group: microfood
taxon: null
evidence_level: "B"
version: "1.0"
source: toktogi_habitat.md
---
# 부착생물막 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B0A`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_periphyton_biofilm` / `microfood` |
| 명칭 | 부착생물막 |
| 배치 카테고리 / 폴더 코드 | `B` / `B0A` |
| 구역 | `Z1_floating_mat / Z2_emergent_objects / Z5_shallow_underwater` |
| 톡토기 연계 | **B** — 담수 생물막 일반 근거; 물알둥근톡토기가 모든 생물막을 먹는다는 근거 없음 [H15] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 막 두께·면적·조성은 상황별 미확정 |
| 실루엣 | 돌·나무·수생식물에 얇게 달라붙은 미생물·조류 점질막 |
| 고유 식별점 | 불균일한 경계와 점상 군집; 표면 부착형이지 독립 동물 아님 |
| 색·표면 | 옅은 녹갈색~갈색 반투명 층; 굴절·재질 수치 미정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `film_decal` | 핵심 형상 |
| `local_mask` | 분리 메시·재질 또는 선택 세부 요소 |
| `opacity_layer` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 돌 표면막 |
| Variant 2 | 나무 표면막 |
| Variant 3 | 부유식물 표면막 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 담수 생물막 일반 근거; 물알둥근톡토기가 모든 생물막을 먹는다는 근거 없음 [H15] [H17]
- **게임 설계:** `background_surface_layer / optional_growth_visual[설계]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 부착 기질을 따라 변형; 플레이어 먹이 상호작용은 기본 비활성
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `attached` |
| `motion_profile` | `material_state` |
| `anchor` | `substrate_uv` |
| `habitat_zone` | `Z1_floating_mat / Z2_emergent_objects / Z5_shallow_underwater` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_periphyton_biofilm
asset_class_candidate: B
folder_code: "B0A"
evidence_level: "B"
zone: "Z1_floating_mat / Z2_emergent_objects / Z5_shallow_underwater"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_periphyton_biofilm_movement.md
model_spec: env_periphyton_biofilm_model.md
```
## 7. 미확인 값·검수
- **미확인:** 세균·조류 종조성·섭식 여부·막 강성·미세 구조.
- **동정/구조:** 식용 조류 패치와 동의어로 합치지 않음; 먹이 evidence B 유지.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B0A`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H15] [담수 부착 생물막 연구 (2021)](https://www.sciencedirect.com/science/article/pii/S0304377021001169)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
