---
object_id: fx_moisture_particles
asset_class_candidate: E
asset_folder_code: "E01"
group: effects
taxon: null
evidence_level: "C"
version: "1.0"
source: toktogi_habitat.md
---
# 물방울·물안개·미세 입자 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `E01`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `fx_moisture_particles` / `effects` |
| 명칭 | 물방울·물안개·미세 입자 |
| 배치 카테고리 / 폴더 코드 | `E` / `E01` |
| 구역 | `Z0_water_surface / Z2_emergent_objects / Z3_wet_bank` |
| 톡토기 연계 | **C** — 주변 환경 효과; 톡토기 행동·생존의 종별 임계 조건을 나타내지 않음 [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 물방울·입자 크기/속도는 실제 측정치 없이 게임 연출값 |
| 실루엣 | 국소 물방울, 낙수 잔물결, 낮은 물안개와 떠다니는 유기입자 |
| 고유 식별점 | 입자·안개·물방울을 분리한 시스템 효과; 생물 몸통처럼 구현하지 않음 |
| 색·표면 | 투명도·블러·반사/굴절·상태별 페이드; 값은 [설계] |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `droplet_mesh_or_billboard` | 핵심 형상 |
| `mist_particles` | 분리 메시·재질 또는 선택 세부 요소 |
| `ripple_spawn` | 분리 메시·재질 또는 선택 세부 요소 |
| `organic_specks` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 물방울 |
| Variant 2 | 안개 |
| Variant 3 | 낙수 잔물결 |
| Variant 4 | 유기입자 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 주변 환경 효과; 톡토기 행동·생존의 종별 임계 조건을 나타내지 않음 [H17]
- **게임 설계:** `spawn_effect / fade_out / ripple_on_impact`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 입자의 물리 충돌은 선택; 캐릭터 자동 대미지/이동 제한을 만들지 않음
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `effect` |
| `motion_profile` | `particle_fx` |
| `anchor` | `emitter / impact` |
| `habitat_zone` | `Z0_water_surface / Z2_emergent_objects / Z3_wet_bank` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: fx_moisture_particles
asset_class_candidate: E
folder_code: "E01"
evidence_level: "C"
zone: "Z0_water_surface / Z2_emergent_objects / Z3_wet_bank"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: fx_moisture_particles_movement.md
model_spec: fx_moisture_particles_model.md
```
## 7. 미확인 값·검수
- **미확인:** 물방울 직경·풍향·안개 밀도·수질·생물별 습도 한계.
- **동정/구조:** E 효과 에셋; C 캐릭터가 아니며 생물학적 위협값 부여 금지.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `E01`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
