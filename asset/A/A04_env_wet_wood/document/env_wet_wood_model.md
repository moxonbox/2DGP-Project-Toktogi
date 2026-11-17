---
object_id: env_wet_wood
model_spec_id: env_wet_wood_model
parent_spec: env_wet_wood.md
group: emergent_substrates
asset_class_candidate: A
model_scope: external_visual_and_collision
version: "1.0"
---
# 젖은 나무·떠 있는 가지 (환경 요소) — 3D 모델 명세
> `toktogi_model.md`의 실루엣·크기·외부 구조·색채·미정 값 체계를 따르되, **기록된 치수와 제작용 변수는 분리**한다.
## 1. 전체 형태
| 요소 | 형상 규격 |
|---|---|
| 몸체·기질 | 젖은 나무껍질이 있는 잔가지, 걸치거나 일부 잠긴 나무 |
| 고유 형질 | 불규칙한 마디와 균열, 젖은 접촉부의 어두운 띠 |
| 물체 방향 | `local_forward=+X, up=+Z (제안)`; 프로젝트 최종 좌표계 결정 전 가정 |
| 배치 층 | `Z2_emergent_objects / Z0_water_surface` |
## 2. 크기·스케일
| 항목 | 규칙 |
|---|---|
| 원문 크기 | 나무 직경·길이 실측치 미확인; 부유/고정 상태 별도 |
| 생물 비교 | `toktogi` 암컷 최대 체장 **1mm = 1×**. 길이 외 폭·높이·뿌리 길이를 분리 |
| Blender 원본 | C011 몸길이 제작 대용값 `0.965396 BU`는 원형 측정값일 뿐 **mm→BU 확정 변환이 아님** [AssetSize(2)] |
| 출력 | 128×128px는 현행 C011 셀 참고값; 큰 식물·지형에 자동 적용하지 않음 |
| 미정 | `model_length_bu`, `render_scale`, `collision_size`, `lod_threshold` |
## 3. 메시·세부 구조
| 메시/계층 제안 | 모델링 가이드 |
|---|---|
| `branch_main` | 실제 형태를 좌우하는 기본 실루엣; 독립적인 pivot 유지 |
| `bark_sections` | 필요 LOD에서 분리; 실루엣과 동정 형질만 유지 |
| `submerged_segment` | 수면 위·아래 위치를 구분; 침수·움직임은 상위 수계 시스템 연동 |
| `wetline_mask` | 가능하면 별도 재질/디칼; 기하·충돌 높이와 혼동하지 않음 |
## 4. 재질·색채
- **육안 색·표면:** 거칠어진 표면·젖음 마스크; 썩음/이끼 표현은 선택적.
- **채널:** Base Color, Alpha, Normal, AO, Roughness/Metallic은 동일 방향·포즈에서 정합해야 함.
- **미정:** 실측 RGB·HEX·금속성·IOR·투명도·거칠기 및 미세구조 수치. 관찰 사진을 수치 증거로 과장하지 않음.
## 5. 모델 변형·참조 시점
- `variant_1` — 떠 있는 나뭇가지.
- `variant_2` — 고정·걸친 나무.
- `variant_3` — 젖은 껍질 상태.
- **필수 뷰:** 상면(실루엣), 측면(물선·높이), 정면(폭·대칭), 상세 확대(고유 형질).
- **기준 앵커:** `walk_top / waterline`. 별도 지지점·산란점·표면 UV는 충돌 데이터에서 정의.
## 6. 리깅·LOD·충돌 (제작 제안)
| 계층 | 구현 원칙 |
|---|---|
| `physics_root` | 월드 위치·접촉·부력 등은 시뮬레이션 소유 |
| `visual_root` | 보행/부유 흔들림 등 시각 오프셋; 실제 물리 위치 수정 금지 |
| `rig_optional` | 움직이는 부품만 뼈·쉐이프키; 정적 배경은 불필요한 본 생성 금지 |
| `surface_collider` | 게임 판정 표면을 분리; 재질 디칼과 충돌 메시 혼동 금지 |
| `LOD0/1/2` | 동정 특징 → 큰 형태 → 실루엣 순으로 축소; 거리 임계치는 미정 |
## 7. 모델 데이터
```yaml
object_id: env_wet_wood
asset_class_candidate: A
folder_code: "A04"
source_measure: "나무 직경·길이 실측치 미확인; 부유/고정 상태 별도"
length_mm: null # 단일 기준 수치만 확보하면 입력
model_length_bu: null
render_scale: null
origin_axis: null # DEC-06 최종 확정 전
collision_mesh: null
anchor_set: "walk_top / waterline"
```
## 8. 검수·미결정
- **형태:** 부유형/고정형을 자동 혼합하지 않음; 접촉 동안 발판 기준 좌표 일치.
- **미결정:** 기질 강성·정확한 가지 치수·부유 속도·포식자 은신효과.
- **검수:** 스프라이트 색·Normal·AO 정합, 물선/접지점, 크기축, 큰 에셋 타일 잘림, LOD 변형.
- **연계:** `env_wet_wood.md`, `env_wet_wood_movement.md`, `toktogi_habitat.md`, `AssetSize(2).md`.
