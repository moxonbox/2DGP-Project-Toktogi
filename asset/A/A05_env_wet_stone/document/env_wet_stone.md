---
object_id: env_wet_stone
asset_class_candidate: A
asset_folder_code: "A05"
group: emergent_substrates
taxon: null
evidence_level: "A"
version: "1.0"
source: toktogi_habitat.md
---
# 젖은 돌·자갈 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `A05`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_wet_stone` / `emergent_substrates` |
| 명칭 | 젖은 돌·자갈 |
| 배치 카테고리 / 폴더 코드 | `A` / `A05` |
| 구역 | `Z2_emergent_objects / Z3_wet_bank` |
| 톡토기 연계 | **A** — 물 밖 돌에 물알둥근톡토기가 모이는 관찰 기록 있음 [H01] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 돌·자갈 실제 크기 수치는 원문 미확정 |
| 실루엣 | 수면 위로 솟은 불규칙 돌 표면과 물 아래 면 |
| 고유 식별점 | 돌출부와 균열, 젖은 면·마른 면 구별, 부착 피막 가능 |
| 색·표면 | 무기질 거친 표면과 젖음 마스크; 실제 조성·PBR 미정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `rock_core` | 핵심 형상 |
| `wet_mask` | 분리 메시·재질 또는 선택 세부 요소 |
| `dry_cap` | 분리 메시·재질 또는 선택 세부 요소 |
| `biofilm_decal_optional` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 수면 반잠김 |
| Variant 2 | 물가 고정 돌 |
| Variant 3 | 자갈 군집 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 물 밖 돌에 물알둥근톡토기가 모이는 관찰 기록 있음 [H01] [H17]
- **게임 설계:** `walk_on[A] / jump_from[A] / stop_on[A]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 고정 충돌면, 젖음·이끼 디칼은 물리 높이를 자동 변경하지 않음
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `fixed` |
| `motion_profile` | `static_wetmask` |
| `anchor` | `top_surface / waterline` |
| `habitat_zone` | `Z2_emergent_objects / Z3_wet_bank` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_wet_stone
asset_class_candidate: A
folder_code: "A05"
evidence_level: "A"
zone: "Z2_emergent_objects / Z3_wet_bank"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_wet_stone_movement.md
model_spec: env_wet_stone_model.md
```
## 7. 미확인 값·검수
- **미확인:** 돌 크기별 분포·마찰/착지 성공률·산란 선호도.
- **동정/구조:** 원석은 고정, 피막은 표면층; 근거 없는 자력 움직임 없음.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `A05`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H01] [Schneider et al. (2021), GigaScience](https://doi.org/10.1093/gigascience/giab035)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
