---
object_id: env_sediment
asset_class_candidate: B
asset_folder_code: "B09"
group: underwater
taxon: null
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 바닥 퇴적물 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B09`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_sediment` / `underwater` |
| 명칭 | 바닥 퇴적물 |
| 배치 카테고리 / 폴더 코드 | `B` / `B09` |
| 구역 | `Z5_shallow_underwater / Z3_wet_bank` |
| 톡토기 연계 | **B/C** — 수생 생물의 일반 배경 기질; 물알둥근톡토기는 상시 잠수 저서 생물이 아님 [H12] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 입경·퇴적층 두께·분포는 장소별 미선정 |
| 실루엣 | 수중 바닥의 실트·점토·모래·자갈층 |
| 고유 식별점 | 층리·조립질 조각·유기입자 산재; 부유 수면이 아님 |
| 색·표면 | 흙색·회갈색·탁도 효과; 수중 조명에 따른 색변화 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `sediment_floor` | 핵심 형상 |
| `layer_masks` | 분리 메시·재질 또는 선택 세부 요소 |
| `gravel_instances` | 분리 메시·재질 또는 선택 세부 요소 |
| `organic_particles_optional` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 고운 실트 |
| Variant 2 | 사질 바닥 |
| Variant 3 | 자갈 혼합층 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 수생 생물의 일반 배경 기질; 물알둥근톡토기는 상시 잠수 저서 생물이 아님 [H12] [H17]
- **게임 설계:** `background_floor / suspension_on_disturbance_optional[설계]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 바닥 충돌은 수중 배경 생물용; 톡토기 주 서식면으로 지정하지 않음
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `underwater` |
| `motion_profile` | `static_sediment` |
| `anchor` | `floor_surface / turbidity_origin` |
| `habitat_zone` | `Z5_shallow_underwater / Z3_wet_bank` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_sediment
asset_class_candidate: B
folder_code: "B09"
evidence_level: "B/C"
zone: "Z5_shallow_underwater / Z3_wet_bank"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_sediment_movement.md
model_spec: env_sediment_model.md
```
## 7. 미확인 값·검수
- **미확인:** 정확한 입도·퇴적속도·수심·모래 물리계수.
- **동정/구조:** 톡토기를 수중 바닥을 걷는 기본 캐릭터로 오인하지 않음.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B09`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H12] [Intermittent rivers 생태학 리뷰 (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9542210/)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
