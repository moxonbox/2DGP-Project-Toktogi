---
object_id: plant_ceratophyllum_demersum
asset_class_candidate: B
asset_folder_code: "B05"
group: submerged_plants
taxon: "Ceratophyllum demersum"
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 붕어마름류 (*Ceratophyllum demersum*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B05`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_ceratophyllum_demersum` / `submerged_plants` |
| 명칭 | 붕어마름류 — *Ceratophyllum demersum* |
| 배치 카테고리 / 폴더 코드 | `B` / `B05` |
| 구역 | `Z5_shallow_underwater` |
| 톡토기 연계 | **B/C** — 얕은 수중의 배경 입체식생; 톡토기의 상시 잠수 행동 근거는 아님 [H09] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 줄기 길이·포기 전체 크기는 원자료에 공통 확정치 없음 |
| 실루엣 | 뿌리 없는 수중 줄기와 줄기 둘레의 돌려난 잎 |
| 고유 식별점 | 잎은 여러 갈래로 갈라지며 형태가 지역·변종별로 달라짐 |
| 색·표면 | 수중 녹색·암록색 계열; 투과광에 따른 색 변화는 렌더링 변수 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `submerged_stem` | 핵심 형상 |
| `whorled_leaf_sets` | 분리 메시·재질 또는 선택 세부 요소 |
| `fine_leaf_segments` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 짧은 절편 |
| Variant 2 | 길게 펼친 줄기 |
| Variant 3 | 잎 마디 밀도 변형 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 얕은 수중의 배경 입체식생; 톡토기의 상시 잠수 행동 근거는 아님 [H09] [H17]
- **게임 설계:** `background_submerged / visual_occluder`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 수중 배경; 톡토기의 주요 접촉·산란 지점으로 지정하지 않음
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `submerged` |
| `motion_profile` | `water_sway` |
| `anchor` | `stem_mid / whorl_nodes` |
| `habitat_zone` | `Z5_shallow_underwater` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_ceratophyllum_demersum
asset_class_candidate: B
folder_code: "B05"
evidence_level: "B/C"
zone: "Z5_shallow_underwater"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_ceratophyllum_demersum_movement.md
model_spec: plant_ceratophyllum_demersum_model.md
```
## 7. 미확인 값·검수
- **미확인:** 종·변종별 정확한 분절 길이, 잎 갈래 수와 강성, 지역 출현.
- **동정/구조:** 뿌리를 잘못 추가하지 않기; 잎 돌려남·갈래 표현.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B05`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H09] [Korean Journal of Plant Resources, Ceratophyllum](https://www.kjpr.kr/articles/xml/V4MO/)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
