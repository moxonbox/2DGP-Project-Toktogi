---
object_id: spider_pardosa
scientific_name: Pardosa
taxonomic_rank: genus
korean_name: 긴마디늑대거미속
version: '1.0'
review_date: '2026-11-17'
role_2dgp: ai_predator_or_hazard
prey_toktogi_status: unverified_species_level_predation
---
# *Pardosa* — 2DGP 이동·행동·애니메이션 명세
> 기준: `spider_pardosa(1).md` v1.2, `toktogi_movement.md`, 플레이어 행동·상태 머신, `3Dconv2D.md`, 2DGP 기획서. **플레이어는 toktogi**, 본 객체는 비플레이어 AI 후보.
> 표기: **[근거]** 원본 자료의 관찰·연구 / **[종 사례]** 특정 *Pardosa* 종 / **[설계]** 게임용 움직임·판정 / **[미확인]** 대상종 직접 근거 없음.

## 1. 생물학적 운동 근거와 적용 한계
- [근거] 늑대거미과의 배회·기습형 거미: `탐색/대기 → 방향 정렬 → 접근·돌진 → 다리·위턱 제압 → 섭식`; **정착 포획그물에 의존하지 않음**. [P04][P06]
- [종 사례] *P. amentata*는 성체 수컷 5.5–6.5mm·암컷 6.0–8.0mm, *P. agrestis*는 수컷 4.5–5.0mm·암컷 약 5.0mm. **속 공통 크기·속도 아님**. [P03][P07]
- [근거] 지표·풀·낙엽·농경지·물가를 종별로 이용; *P. amentata*의 수면 접촉은 속 전체의 지속 수면 추격 능력으로 일반화 금지. [P03][P15]
- [근거] 작은 절지동물을 포식하며 *Pardosa*의 톡토기 DNA 양성 약 20%는 특정 연구 장소의 검출 빈도이지 포획 성공률이 아님. [P05]
- [미확인] *Sminthurides aquaticus* 직접 포식·연못 동시출현·지속 수면 보행·종별 반응 거리·달리기 속도·공격 피해량.
- [설계] 2DGP의 적 역할은 종의 확정 생태관계가 아닌 **가상 전투/회피 상호작용**. 성별·성숙도·구체 종을 정하기 전 크기·스프라이트 비율 고정 금지.

## 2. 이동·행동 카탈로그 (`state`와 표현 `clip` 분리)
| AI 행동/클립 | 진입·전환 | `pre` 준비 | `mid` 핵심/루프 | `end` 정리 |
|---|---|---|---|---|
| `idle_scan` | 초기·표적 없음 | 발 지지 확인 | 몸 낮춤·촉지·머리 시선 탐색 | 다음 목표로 방향 정렬 |
| `patrol` | 경로·지면 유효 | 첫 발 옮김 | 여덟 다리 보행 주기·지면 이동 | 속도 감속·발 정착 |
| `orient` | 감지 단서 수신 | 탐지 방향 평가 | 몸통 회전·앞다리 재배치 | 표적 확인 또는 탐색 복귀 |
| `stalk` | 표적 접근 허용 | 경로/장애물 확인 | 느린 접근·간헐적 정지 | 돌진거리 진입 또는 포기 |
| `rush` | 공격 기회 [설계] | 앞다리 지지·가속 준비 | 짧은 돌진·목표 추적 제한 | 사정거리 도달/초과속도 제동 |
| `strike_grasp` | 현재 적대 대상 유효 | 위턱·앞다리 준비 | 접촉 검사→단발 붙잡기/물기 | 공격 영역 해제·발 복귀 |
| `feed` | 포획/먹이 자원 유효 | 입을 대상으로 이동 | 구기 반복·작업 조건 재검사 | 입·몸통 정리 |
| `evade_hide` | 교란·피격·경로 막힘 | 방향/은신처 평가 | 빠른 회피·엄폐 | 위협 사라짐 확인 |
| `recover` | 돌진·피격 후 | 현재 운동 유지 | 시간/접촉 조건에 따른 자세 회복 | `idle_scan`/`patrol` |
- [근거] 회피는 달리기·식생 틈 숨기기 사례를 반영; `rush` 거리·AI 전환·정확한 보행 리듬은 **[설계]**이며 실측값이 아니다.
- [설계] 일부 유체의 실을 통한 분산은 `juvenile_dispersal` **환경 연출만 선택**; 모든 성체의 자력 비행·전투 이동 기술로 만들지 않는다. [P08]

## 3. AI·물리·사건 소유권
- `physics_root`와 실제 지면 충돌/속도는 **시뮬레이션**이 소유; 애니메이션 `body_ctrl`은 시각 오프셋만 변경한다.
- AI 입력: `target_visible`, `vibration_hint`, `obstacle`, `support_valid`, `threat`, `target_in_range`는 **[설계] 센서**; 탐지 반경·확률은 `null`.
- 우선순위 제안: `despawn/dead > hit_reaction > immediate_hazard > strike_active > evade > stalk/patrol > idle`; 중복 신호는 결정적 tie-break.
- 수직 낙하/모서리 이탈은 물리에서 발생; 지지 상실 시 발 IK 해제, `airborne_fall` 표현을 선택하되 점프·비행 능력으로 오인하지 않는다.
- `attack_instance_id`별 활성 구간에서만 명중; 동일 대상은 선언된 hit policy 범위 내 1회 처리하고 **같은 프레임 반복 표시로 추가 피해 없음**.
- 공격 실패·시야 상실·대상 소멸은 짧은 `end`/`recover`로 복귀; 원거리 강제 텔레포트·지면 관통 추적 금지.
- toktogi의 Capsule 접촉과 피격 영역 분리; 실제 피격·넉백·실패는 플레이어 전투/물리 규칙이 담당하고 거미 클립이 직접 결정하지 않는다.

## 4. `pre–mid–end`와 혼합 규약
- 각 클립에 `phase`, `phase_instance_id`, `phase_u(0..1)`, `loop_id`, `marker_ids`를 저장; 단계 재진입 때 인스턴스 갱신.
- `patrol.mid`는 속도에 맞춘 보행 위상 재생; 방향 변환에 시각 보간 가능하지만 **지지 발 월드 좌표를 순간 반전하지 않음**.
- `strike_grasp.mid`의 `hit_window_open/close`와 물리 타격 검사는 별개; 프레임 시킹·일시정지·취소로 실제 명중을 중복 확정하지 않는다.
- 느린 접근→돌진은 `pre`→`mid` 전이로 구분; `speed_weight`는 자세 변형에만 사용하고 공격 권한을 생성하지 않는다.
- 전신 우선순위는 공중·피격 > 공격 > 회피 > 이동 > 정지; 눈/촉지·복부의 추가 레이어는 충돌/타격 영역을 바꾸지 않는다.
- 전이 중 `outgoing_blend`는 이전 자세 스냅샷만 사용하며 오래된 공격·구기 마커는 재실행하지 않는다.

## 5. 3D 리깅 채널·접지
| 채널 | 목적 | 필수 검증 |
|---|---|---|
| `physics_root / visual_root` | 월드 충돌 기준 / 화면 표현 기준 분리 | 피벗 변경 시 위치 불변 |
| `cephalothorax / abdomen` | 몸통 방향·무게중심의 시각 이동 | 지면·복부 침투 금지 |
| `leg_L1..L4 / leg_R1..R4` | 4쌍 총 8개 다리, 발끝/지지 IK | 보행에서 유효한 지지 발만 고정 |
| `chelicerae_L/R`, `fang` | 제압·물기 가동 | 활성 영역과 입 위치 정합 |
| `pedipalp_L/R`, `eye_4_2_2` | 탐색·촉지, 늑대거미형 눈 배열 | 큰 두 눈은 **후중안(PME)** |
| `spinneret`, `silk_optional` | 이동실·배경 난낭 묘사 | 포획그물 제작과 혼동 금지 |
- 좌우는 개체 기준. 골격 회전·발목 경로·IK 가중치·rest pose는 출력 방향마다 같은 규약 사용; 3D의 임의 수치가 생물학적 실측치를 뜻하지 않는다.

## 6. 3D → 픽셀풍 2D 출력·재생 계약
- `rig/action/variant → pre·mid·end 포즈 표본 → 동일 카메라 멀티패스 → 크롭·피벗·마커 → atlas/manifest → 2D 재생`.
- 각 표본은 `asset_id, revision, clip, phase, sample_time, view, pivot, foot_markers, attack_socket, bbox`를 함께 기록.
- Base Color·Alpha·Normal·AO·Roughness/Metallic을 같은 실루엣/프레임으로 출력; 색상은 선언 색공간, **Normal/ORM은 수치 데이터**.
- 재질은 실제 조명에 반응하는 경로를 검증; `DEC-06`의 view·Normal 공간·Depth·앵커 최종 좌표는 **보류**, 시험용 설정을 양산값으로 승격 금지.
- 3D는 호환 클립/부위별 포즈 가중치 혼합 가능. 2D는 선택된 프레임/전이 클립을 재생하며 **두 PNG의 알파 중첩을 관절 보간으로 취급하지 않음**.
- `attack_socket`/눈/발끝 마커와 색·재질 픽셀을 최종 출력 아틀라스에서 검사; 단순 nearest 확대 및 실제 화면 크기에서 가독성 확인.

## 7. 실행 데이터(설계 예시)
```yaml
npc_id: spider_pardosa
rank: genus
mode: cursorial_ambush
capture_web: false
ai_state: idle_scan
phase: mid
phase_instance_id: null
support_id: null
attack_instance_id: null
target_id: null
speed_u_s: null
perception_range_u: null
attack_range_u: null
damage: null
water_surface_pursuit: unverified
asset_contract: DEC-06-deferred
```

## 8. 수락 시험·근거
- `P-MOV-01` 대기→접근→돌진→물기→정리에서 8다리·촉지·턱 동작과 단계가 끊기지 않음.
- `P-MOV-02` 발판 모서리 이탈·착지 때 발 IK는 실제 지지만 따르고 가짜 도약 충격이 없음.
- `P-MOV-03` 빠른 목표 이동·공격 취소·동일 공격 프레임 반복에서 공격 인스턴스의 중복 피해 없음.
- `P-MOV-04` 속/종 대체 시 크기·서식·수면 추격 능력이 잘못된 고정값으로 승계되지 않음.
- `P-MOV-05` 방향 전환·픽셀 확대·광원 변경 시 8발·눈·위턱 가독성 및 재질 맵 정합 확인.
- `P-MOV-06` toktogi 접촉을 실제 종 수준 포식·20% 포획률로 기록하지 않고 게임용 상호작용으로 표시.
- 출처: [P01](https://wsc.nmbe.ch/), [P03](https://araneae.nmbe.ch/data/153/Pardosa_amentata), [P05](https://doi.org/10.1016/j.biocontrol.2010.06.009), [P06](https://doi.org/10.1002/edn3.272), [P07](https://araneae.nmbe.ch/data/82/Pardosa_agrestis).
- **미결정:** 정확한 종·성숙 단계, 색·크기·속도·공격 범위·피해, 허용 지형, 렌더러·방향 수·좌표(DEC-06). 모든 시험은 실행 전 `NOT_RUN`.
