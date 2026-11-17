---
object_id: env_shore_slope
asset_class_candidate: A
asset_folder_code: "A03"
group: shore
taxon: null
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 연속 물가 경사 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `A03`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_shore_slope` / `shore` |
| 명칭 | 연속 물가 경사 |
| 배치 카테고리 / 폴더 코드 | `A` / `A03` |
| 구역 | `Z3_wet_bank / Z0_water_surface / Z4_riparian_vegetation` |
| 톡토기 연계 | **B/C** — 물가 경사 자체는 일반 수변 환경; 톡토기의 장기 습윤 육상 정착은 미확인 [H12] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 경사 각도·폭·구배는 선택값; 종별 확인 수치 없음 |
| 실루엣 | 수면에서 육상으로 이어지는 낮은 경사 지형 |
| 고유 식별점 | 실트·진흙·모래·자갈·젖음띠·미세 웅덩이 혼합 |
| 색·표면 | 젖음에 따라 명도·거칠기 변화(연출); 물리 마찰 수치 미정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `slope_base` | 핵심 형상 |
| `soil_layer` | 분리 메시·재질 또는 선택 세부 요소 |
| `gravel_scatter` | 분리 메시·재질 또는 선택 세부 요소 |
| `wetline_mask` | 분리 메시·재질 또는 선택 세부 요소 |
| `shallow_puddles` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 완만한 경사 |
| Variant 2 | 자갈 섞인 둑 |
| Variant 3 | 진흙형 경계 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 물가 경사 자체는 일반 수변 환경; 톡토기의 장기 습윤 육상 정착은 미확인 [H12] [H17]
- **게임 설계:** `walk_surface[설계] / waterline_transition[설계]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** Z0→Z3→Z4 이동면 연속; 끊긴 충돌 경계는 피함
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `grounded` |
| `motion_profile` | `wetness_shift` |
| `anchor` | `slope_path / waterline` |
| `habitat_zone` | `Z3_wet_bank / Z0_water_surface / Z4_riparian_vegetation` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_shore_slope
asset_class_candidate: A
folder_code: "A03"
evidence_level: "B/C"
zone: "Z3_wet_bank / Z0_water_surface / Z4_riparian_vegetation"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_shore_slope_movement.md
model_spec: env_shore_slope_model.md
```
## 7. 미확인 값·검수
- **미확인:** 대상 종 육상 이동거리·건조 생존시간·마찰계수.
- **동정/구조:** 경사 고형 지면과 물 충돌면 접합 시 틈 없음.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `A03`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H12] [Intermittent rivers 생태학 리뷰 (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9542210/)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
