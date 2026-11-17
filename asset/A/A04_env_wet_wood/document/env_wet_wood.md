---
object_id: env_wet_wood
asset_class_candidate: A
asset_folder_code: "A04"
group: emergent_substrates
taxon: null
evidence_level: "A"
version: "1.0"
source: toktogi_habitat.md
---
# 젖은 나무·떠 있는 가지 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `A04`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_wet_wood` / `emergent_substrates` |
| 명칭 | 젖은 나무·떠 있는 가지 |
| 배치 카테고리 / 폴더 코드 | `A` / `A04` |
| 구역 | `Z2_emergent_objects / Z0_water_surface` |
| 톡토기 연계 | **A** — 톡토기가 젖은 나무·떠 있는 가지를 이용한 기록 있음 [H01] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 나무 직경·길이 실측치 미확인; 부유/고정 상태 별도 |
| 실루엣 | 젖은 나무껍질이 있는 잔가지, 걸치거나 일부 잠긴 나무 |
| 고유 식별점 | 불규칙한 마디와 균열, 젖은 접촉부의 어두운 띠 |
| 색·표면 | 거칠어진 표면·젖음 마스크; 썩음/이끼 표현은 선택적 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `branch_main` | 핵심 형상 |
| `bark_sections` | 분리 메시·재질 또는 선택 세부 요소 |
| `submerged_segment` | 분리 메시·재질 또는 선택 세부 요소 |
| `wetline_mask` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 떠 있는 나뭇가지 |
| Variant 2 | 고정·걸친 나무 |
| Variant 3 | 젖은 껍질 상태 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 톡토기가 젖은 나무·떠 있는 가지를 이용한 기록 있음 [H01] [H17]
- **게임 설계:** `walk_on[A] / land_on[A] / shelter_near[설계]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 물선 위 상면 접촉·기준점, 수중 부분 별도 충돌 판단
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `wet` |
| `motion_profile` | `float_or_fixed` |
| `anchor` | `walk_top / waterline` |
| `habitat_zone` | `Z2_emergent_objects / Z0_water_surface` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_wet_wood
asset_class_candidate: A
folder_code: "A04"
evidence_level: "A"
zone: "Z2_emergent_objects / Z0_water_surface"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_wet_wood_movement.md
model_spec: env_wet_wood_model.md
```
## 7. 미확인 값·검수
- **미확인:** 기질 강성·정확한 가지 치수·부유 속도·포식자 은신효과.
- **동정/구조:** 부유형/고정형을 자동 혼합하지 않음; 접촉 동안 발판 기준 좌표 일치.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `A04`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H01] [Schneider et al. (2021), GigaScience](https://doi.org/10.1093/gigascience/giab035)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
