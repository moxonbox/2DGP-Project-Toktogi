---
object_id: env_still_water
asset_class_candidate: A
asset_folder_code: "A02"
group: water
taxon: null
evidence_level: "A+B"
version: "1.0"
source: toktogi_habitat.md
---
# 잔잔한 담수 수면 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `A02`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_still_water` / `water` |
| 명칭 | 잔잔한 담수 수면 |
| 배치 카테고리 / 폴더 코드 | `A` / `A02` |
| 구역 | `Z0_water_surface / Z1_floating_mat` |
| 톡토기 연계 | **A+B** — 수면 보행·도약의 직접 확인 기질; 정량 수면장력·도약속도는 미확인 [H01] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 수면 넓이·깊이는 장면 설계치; 생물 mm 기준으로 고정 불가 |
| 실루엣 | 연속 공기–물 경계면과 물선, 얕은 수면 잔물결 |
| 고유 식별점 | 표면 접촉/수면 아래 렌더링을 분리; 물색·탁도 변이 가능 |
| 색·표면 | 반사·굴절·투명도·탁도는 렌더 설정이며 실측 PBR 불명 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `surface_plane` | 핵심 형상 |
| `underwater_volume_optional` | 분리 메시·재질 또는 선택 세부 요소 |
| `shoreline_mask` | 분리 메시·재질 또는 선택 세부 요소 |
| `ripple_decals` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 정체 수면 |
| Variant 2 | 약한 흐름 |
| Variant 3 | 소규모 국소 잔물결 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 수면 보행·도약의 직접 확인 기질; 정량 수면장력·도약속도는 미확인 [H01] [H17]
- **게임 설계:** `walk_on[A] / jump_from[A] / ripple_at_contact[설계]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 물 표면 충돌면을 시각 수면과 분리; 수중 체류를 기본 동작으로 만들지 않음
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `water_surface` |
| `motion_profile` | `surface_ripple` |
| `anchor` | `waterline / contact_point` |
| `habitat_zone` | `Z0_water_surface / Z1_floating_mat` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_still_water
asset_class_candidate: A
folder_code: "A02"
evidence_level: "A+B"
zone: "Z0_water_surface / Z1_floating_mat"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_still_water_movement.md
model_spec: env_still_water_model.md
```
## 7. 미확인 값·검수
- **미확인:** 수면장력·점성·물 흐름 속도·파형 진폭/주기·수심의 종별 조건.
- **동정/구조:** 접촉면 연속성 유지; 수면 보행을 상시 잠수로 변환 금지.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `A02`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H01] [Schneider et al. (2021), GigaScience](https://doi.org/10.1093/gigascience/giab035)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
