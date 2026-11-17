---
object_id: predator_hydrometra_martini
scientific_name: Hydrometra martini
taxonomic_rank: species
korean_name: null
version: '1.0'
review_date: '2026-11-17'
role_2dgp: experimental_surface_predator_npc
prey_toktogi_evidence: different_sminthurides_species_rearing
---
# *Hydrometra martini* — 2DGP 이동·행동·애니메이션 명세
> 기준: ZIP의 같은 ID 생물 명세 v1.0·`nonspider_predator_objects_index.md` + `toktogi_movement.md`·거미류 Movement 공통 파이프라인·3Dconv2D/플랫포머 설계.
> **역할:** `toktogi`가 플레이어, 본 객체는 NPC/환경 위험 **설계 후보**. `[종 근거]`와 `[게임 설계]`, `[미확인]`을 별도 관리.

## 1. 생물학적 운동 근거·범위
- [종 표본] 수컷 7.7–8.5mm(n=10), 암컷 8.8–10.15mm(n=10) 지역 연구 표본; 속의 표준 크기·평균으로 고정 금지. [H02]
- [종 형태] 가늘고 긴 머리·몸·여섯 다리, 눈은 머리 뒤쪽, 갈색계, 접힌 흡즙형 주둥이; 비슷한 *H. australis*와 정밀 동정 필요. [H02][H03]
- [서식] 북미 호수·연못·개울의 수초 많은 얕은 가장자리, 부유잎·젖은 기질을 이용; 한국 출현 미확인. [H01][H02]
- [종 실험] 2000년 사육에서 먹이 *Sminthurides malmgreni*와 *Drosophila melanogaster*, 기질 젖은 여과지와 개구리밥을 교차 사용. [H01]
- [종 실험] 여과지+*S. malmgreni*, 개구리밥+초파리에서 생존 측면의 유리함이 보고됨; 야생 선호 먹이·공격 성공 확률 아님. [H01]
- [사육조건] 28±1°C·명12h/암12h; *Sminthurides* 약 20마리/용기/일은 **공급량**이지 섭식량이 아님. 깔따구 우화 성충 섭식 관찰도 있음. [H01]
- [제약] 해당 실험 먹이 종은 *S. aquaticus*가 아님. 한국 연못·톡토기의 직접 접촉, 개체당 탐지거리·속도·피해는 미확인. [H01][H04]

## 2. 행동 카탈로그 — AI 상태와 표현 클립 분리
| `action/clip` | 진입 가드 | `pre` 준비 | `mid` 동작·반복 | `end` 종료 |
|---|---|---|---|---|
| `wait` | 수면/식물 유효 지지 | 다리 지지·주둥이 접힘 | 몸 흔들림 최소 대기 | 상태 변경에 자세 전달 |
| `surface_walk` | 수면 경로 존재 | 발 접촉/균형 | 긴 다리의 느린 교대 보행 | 발 정지 |
| `plant_cross` | 개구리밥·젖은 기질 경계 | 유효 접촉 탐색 | 표면·발판 ID 전환 | 새 지지 확정 |
| `detect` | 먹이·진동 단서 [설계] | 단서/기질 종류 판정 | 머리·더듬이 방향 정렬 | 접근/포기 |
| `approach` | 표적 유효·경로 확보 | 공격 접근 준비 | 지지 경로를 따라 이동 | 접촉거리 진입 |
| `rostrum_probe` | 도달·활성 공격 허용 | 주둥이 세움/목표 맞춤 | 1회 관통 판정; 확률은 미정 | 주둥이 접기 |
| `suck_feed` | 활성 먹이 자원 존재 | 주둥이 접촉 확인 | 흡즙 시각 루프·효과 재검사 | 자원 해제/회수 |
| `evade` | 교란·수면 장애 | 방향 전환 | 식물 위/수면 후퇴 | 대기로 복귀 |
| `support_lost` | 지지 소실 | 발 지면 IK 해제 | 실제 낙하/충돌 추종 | 새 지지 확인 |
- [설계] 사육 프로필 `food_type`과 `substrate_type`은 분석용 메타데이터; 자연 연못에서 먹이 선호 AI 자동 확정 금지.
- [설계] 알 부착·약충 성장·성충 월동은 별도 환경 연출만 허용, 현재 2DGP 공격 진행 조건 아님.

## 3. AI·물리·전투 이벤트 소유권
- **AI 의도·행동 상태·물리·리그 표현의 소유권 분리:** `physics_root`와 이동·지지/수중 경계는 서식 레이어별 시뮬레이션이 소유하고, 클립은 시각 자세만 담당한다.
- 센서 `target_visible`, `surface_vibration`, `range_ok`, `support_valid`, `hazard`는 [설계] 입력이며 감지 거리/확률은 출처로 검증되기 전 `null`이다.
- `attack_instance_id`·`target_id`·`active_interval`·`effect_committed`를 분리하고, 동일 공격에 같은 피격 대상의 효과는 명시된 횟수 이하로 제한한다.
- 사건 경계의 입력→물리 접촉→공격 활성→결과 확정 순서를 동일 틱에서 일관되게 적용한다. UI/일시정지·저장복원 시 과거 마커 재생은 무효다.
- 애니메이션 마커는 **효과 발생 후보**이며 실제 성공은 시뮬레이션의 현재 거리·유효 대상·접촉·피격 가능 상태로 결정한다.
- `toktogi`는 플레이어 Capsule/체력·넉백 판정을 소유; 적의 시각 클립만으로 낙하·피격·잡힘·게임오버를 강제하지 않는다.
- 전투 접촉은 단발 상호작용으로 종료·정리한다. 지속 파트너·구애·결속·공동 도약·공유 입력 관계 시스템을 생성하지 않는다.

## 4. `pre–mid–end`, 가중치·취소 처리
- 단계 `pre`=지지·목표 정렬 / `mid`=루프 또는 실제 공격 후보 / `end`=기관·자세 회수; 시간·각도·보폭은 생물 실측이 아닌 **[설계] 프로필**이다.
- 상태·단계 변경마다 `state_generation`·`phase_instance_id`·`cycle_id`를 관리하고 오래된 `phase_done`, `attack`, `feed` 마커는 폐기한다.
- 행동 `pre/mid/end`는 시간 진행 순서, `speed_weight`·`turn_weight`·`hit_weight`는 **호환 포즈 변형** 선택/혼합; 가중치만으로 판정·공격 권한을 생성하지 않는다.
- `outgoing_blend`는 기존 포즈 스냅샷만 섞고 공격/섭식 이벤트는 **재실행하지 않는다**. 행동 취소는 end 클립 완료를 기다리지 않는다.
- 발/지느러미 접촉·타격 소켓·입/혀 위치는 같은 표시 시각에서 정합; 실제 공격은 물리 시간·유효 active 구간에서만 수행한다.
- 3D 포즈 혼합은 가능하지만 출력된 **2D PNG 두 장을 알파 중첩하는 방식은 관절 보간이 아니다**. 부족한 전이 자세는 3D에서 추가 표본 출력한다.

## 5. 3D 리깅·표면 접촉 채널
| 리그 채널 | 동작 역할 | 필수 검수 |
|---|---|---|
| `head_long/body_long` | 가늘고 긴 머리·몸통 | 유사종과 다른 눈 위치 보존 |
| `legs_3pairs` | LF/LM/LH·RF/RM/RH 발끝 | 식물/수면 표면에서 유효한 지지만 IK |
| `antenna_L/R,eyes` | 탐색 방향 | 머리 끝과 눈 혼동 금지 |
| `rostrum_ctrl,rostrum_tip` | 흡즙·공격 소켓 | 시각 접촉과 공격 판정 일치 |
| `wing_form_optional` | 축소 날개형 외형 | 장시형 비행 자동 지원 금지 |
- [설계] 실험적 기질에 따른 발육/생존 차이는 AI 시뮬레이션 값으로 자동 대입하지 않는다.

## 6. 3D → 픽셀풍 2D 스프라이트 파이프라인
- **공통 파이프라인:** `원본 3D 모델+리그 → Action별 pre/mid/end → 고정 시점·포즈 샘플 → Base/Alpha/Normal/AO/ORM 출력 → 크롭/피벗/소켓 → Atlas/Manifest → 2D 재생`.
- 메타데이터: `asset_id, revision, action, phase, variant, sample_time, display_duration, view, pivot, bbox, support_markers, attack_socket`를 동일 프레임 묶음으로 보존한다.
- Base Color/Emissive 등 색 채널은 선언된 색공간으로, **Normal/ORM/Depth/coverage는 수치 데이터로** 디코딩한다. 픽셀풍 정수배 확대·경계/알파 검증.
- 실제 조명에 대한 Normal·Roughness/Metallic 반응을 시험하며 일부 정적 배경 베이크만 허용한다. 완성 조명 RGBA를 Albedo로 재조명하지 않는다.
- `DEC-06`의 방향 수·Normal 공간·Depth·앵커/좌표계는 **보류**. 한 시점 교정만으로 다방향 양산을 통과 처리하지 않는다.
- 3D IK·본 블렌드는 오프라인 제작에서 해결하고 2D 런타임은 클립·방향·표본/전이 선택. 시킹·FPS 변화·저장복원에서 사건 중복을 막는다.

## 7. 실행 데이터 예시(수치는 미결정)
```yaml
npc_id: predator_hydrometra_martini
allowed_habitat: [pond_margin,shallow_surface,floating_vegetation,wet_plant]
locomotion: deliberate_surface_walking
prey_evidence: Sminthurides_malmgreni_only_experiment
phase: pre
target_id: null
support_id: null
attack_instance_id: null
damage: null
predation_probability: null
feeding_study_prey: [Sminthurides_malmgreni, Drosophila_melanogaster]
substrate_study: [wet_filter_paper, duckweed]
lab_temperature_c: 28_plusminus_1
diet_sminthurides_aquaticus: unverified
occurrence_south_korea: unverified
attack_speed_u_s: null
asset_contract: DEC-06_deferred
```

## 8. 수락 시험 / 연구 검증 구분
- `HM-MOV-01` 느린 수면 보행·부유식물 경계·지지 소실 처리.
- `HM-MOV-02` 단서·접근·흡즙 공격이 분리되고 활성 구간 밖 피해 없음.
- `HM-MOV-03` 28°C 사육값·먹이 공급량을 게임 섭식률로 적용하지 않음.
- `HM-MOV-04` *S. malmgreni*와 *S. aquaticus* 분류를 혼동하지 않음.
- `HM-MOV-05` 6발·주둥이·머리 및 출력 재질/마커 정합.
- 실행·3D 리그·스프라이트 렌더 시험은 현재 **NOT_RUN**. 근거 미확인값은 `0`이 아니라 `null`/`unverified`.

## 9. 출처·업데이트 규칙
- [H01] [자료](https://doi.org/10.2307/3496223) — 먹이/기질 교차 사육실험.
- [H02] [자료](https://conservancy.umn.edu/bitstreams/6692aaac-8c04-4da7-af65-9b444f8523cc/download) — 표본 크기·형태·분포.
- [H03] [자료](https://www.bugguide.net/node/view/19769) — *Hydrometra* 형태 참조.
- [H04] [자료](https://www.nibr.go.kr/aiibook/catImage/22/National%20Species%203.pdf) — 한국 다른 실소금쟁이.
- 프로젝트 공통: `toktogi_movement.md`(31장면 근거 구분), `3Dconv2D.md`, `toktogi_playable_action_animation_spec.md` v2.1.
- **변경 원칙:** 객체 학명·분류수준·먹이 동정·관찰 장면·장소·생애단계·원문 URL을 연결한다. 다른 먹이 종이나 지역의 사육 수치를 `S. aquaticus` 실측치로 전용하지 않는다.
