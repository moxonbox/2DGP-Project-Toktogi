---
object_id: env_wet_wood
movement_spec_id: env_wet_wood_movement
parent_spec: env_wet_wood.md
asset_folder_code: "A04"
asset_class_candidate: A
role_2dgp: habitat_asset
version: "1.0"
status: design_not_tested
---
# 젖은 나무·떠 있는 가지 (환경 요소) — 움직임·상태·애니메이션 명세
> 거미 이동 예시의 `state / pre–mid–end / physics_root` 계약을 **환경 객체에 맞게 축소**. 정적 기질에 가짜 자발 이동을 부여하지 않는다.
## 1. 생태·동작 범위
- **형태·생태:** 톡토기가 젖은 나무·떠 있는 가지를 이용한 기록 있음 (원본 근거: [H01] [H17]).
- **기본 움직임:** 고정형 static; 부유형은 수면 물리 시스템을 따라 이동·회전.
- **접촉·상호작용:** walk_on[A] / land_on[A] / shelter_near[설계].
- **근거 구분:** 수치·생물행동은 출처 범위만 인정. 흔들림·성장 연출·물리 반응은 `[설계]`이며 종별 실측값 아님.
## 2. `state` / `clip` 카탈로그
| 상태/클립 | 진입 조건 | `pre` 준비 | `mid` 유지·작동 | `end` 정리 |
|---|---|---|---|---|
| `fixed_rest` | 고정형 | 수면·접지 확인 | 루트 불변 | 유지 |
| `floating_bob` | 부유형 | 시스템 부력 읽기 | 루트 위치 물리 추종 + 시각 흔들림 | 앵커 정합 |
| `contact_reaction` | 착지/접촉[설계] | 지지점 확인 | 경미한 시각 반응, 필요하면 물결 | 안정 |
## 3. 상호작용·물리 소유권
- `physics_root`: 실제 월드 이동·수위·부력·접촉·콜라이더 권한은 환경/물리 시스템에 있음.
- `visual_root`: 잎·줄기·물방울의 시각 흔들림 등 표현만 관리. 충돌·산란·먹이 소모를 단독 확정하지 않음.
- `support_anchor`: `walk_top / waterline`; 모델의 이동/변형에도 접촉점이 필요하면 월드 기준으로 갱신.
- **충돌 규칙:** 물선 위 상면 접촉·기준점, 수중 부분 별도 충돌 판단
- **카테고리:** `B` 후보 객체는 플레이어 상호작용 없음; `A` 후보의 접촉은 별도 승인된 이벤트로만 처리; `E`는 시각 효과.
- 물리 갱신과 시각 프레임은 별도 타이밍; 이미 처리한 접촉 이벤트를 렌더러 재생으로 반복 확정하지 않음.
## 4. `pre–mid–end` 및 프레임 규약
- `phase`, `phase_instance_id`, `phase_u(0..1)`, `loop_id`, `event_marker_ids`를 저장; 재진입마다 인스턴스 갱신.
- `pre`: 소유 시스템의 입력값 수신; `mid`: 루프/보간·변형; `end`: 이전 접촉·재질 이벤트 정리.
- 반복 프레임/시킹/일시정지로 자원 소모·발판 변경·이펙트를 중복 발생시키지 않음.
- 상태 전환은 기존 `visual_root`와 새 앵커를 보간하되, `physics_root`의 권위를 침해하지 않음.
## 5. 리그·접점·3D→2D
| 채널 | 구현 원칙 |
|---|---|
| `physics_root` | 위치·회전·충돌 기준, 배경 객체는 일반적으로 고정 |
| `visual_root` | 시각 애니메이션 전용, 판정 변형 금지 |
| `anchors` | `walk_top / waterline` |
| `mesh_parts` | 필요한 움직이는 부위만 본/쉐이프키; LOD에서는 정적 메시 대체 가능 |
| `manifest` | `asset_id, revision, clip, phase, sample_time, view, pivot, bbox, anchors` |
- Base/Alpha/Normal/AO/ORM 채널의 실루엣과 프레임 정합 검수; DEC-06의 최종 카메라·방향·Normal 공간은 보류.
## 6. 실행 데이터(설계안)
```yaml
object_id: env_wet_wood
asset_class_candidate: A
motion_profile: float_or_fixed
state: idle
phase: mid
phase_instance_id: null
support_id: null
event_instance_id: null
system_motion_speed: null
amplitude: null
period: null
collision_policy: null
asset_contract: DEC-06-deferred
```
## 7. 수락 시험(실행 전 `NOT_RUN`)
- `MOV-01` pre→mid→end와 루프·취소·재생에서 상태·마커 중복 이벤트 없음.
- `MOV-02` 월드 충돌·물선·부유점은 시각 프레임 변경과 무관하게 결정적 유지.
- `MOV-03` 부유형/고정형을 자동 혼합하지 않음; 접촉 동안 발판 기준 좌표 일치.
- `MOV-04` 3D→2D 각 뷰·LOD에서 마커·피벗·재질 패스·전이 프레임 정합.
- `MOV-05` 기질 강성·정확한 가지 치수·부유 속도·포식자 은신효과를 실측값처럼 고정하지 않음.
## 8. 출처·범위
- 생물·지형 사실: `env_wet_wood.md`, `toktogi_habitat.md` (H01, H17).
- 제작 계약 참고: `spider_pardosa_movement(1).md`, `AssetLabelRule(1).txt`, `AssetSize(2).md`.
