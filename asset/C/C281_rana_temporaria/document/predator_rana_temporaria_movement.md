---
object_id: predator_rana_temporaria
scientific_name: Rana temporaria
taxonomic_rank: species
korean_name: null
version: '1.0'
review_date: '2026-11-17'
role_2dgp: pond_bank_frog_predator_optional_npc
prey_toktogi_evidence: Podura_aquatica_experiment_not_aquaticus
---
# *Rana temporaria* (유럽공통개구리; 번역명) — 2DGP 이동·행동·애니메이션 명세
> 기준: ZIP의 같은 ID 생물 명세 v1.0·`nonspider_predator_objects_index.md` + `toktogi_movement.md`·거미류 Movement 공통 파이프라인·3Dconv2D/플랫포머 설계.
> **역할:** `toktogi`가 플레이어, 본 객체는 NPC/환경 위험 **설계 후보**. `[종 근거]`와 `[게임 설계]`, `[미확인]`을 별도 관리.

## 1. 생물학적 운동 근거·범위
- [종 형태] 성체 흔히 몸길이 6–8cm, 암컷이 큰 경향; 갈색·올리브·회색 변이, 눈 뒤 어두운 마스크, 긴 뒷다리·물갈퀴. [R02][R03]
- [서식] 유럽의 숲·초지·연못에 분포, 번식기는 수역, 평상시 육지/물가 이동. 한국 자생 개구리로 표시하지 않음. [R02][R03]
- [성체 행동] 육상 홉/큰 도약, 얕은 물 수영, 움직이는 작은 먹이를 시각 탐지하고 혀·입으로 포획. 도약 속도·혀 속도 정량 미확인. [R03]
- [종 실험] *Podura aquatica* 방어물질 반응 연구에 *R. temporaria*가 등장하며 뚜렷한 먹이 회피 효과가 없었음. 이는 ***S. aquaticus* 직접 포식 증거가 아님**. [R01]
- [먹이] 성체는 여러 소형 무척추동물을 먹지만 올챙이는 조류·유기물·미생물 등을 활용하는 별도 먹이형. 올챙이를 성체 포식 AI에 넣지 않는다. [R02][R05]
- [생애] 봄 얕은 수역의 젤리질 알 무더기·외부수정, 올챙이→변태 개구리; 지역별 700–4,500알 사례와 온도 의존 발육시간을 게임 고정값으로 전용 금지. [R02]
- [미확인] *S. aquaticus* 야외 섭식/포획률, 구체 한국 수역 동시출현, 공격 범위·점프 궤적·월동 조건의 게임 수치.

## 2. 행동 카탈로그 — AI 상태와 표현 클립 분리
| `action/clip` | 진입 가드 | `pre` 준비 | `mid` 동작·반복 | `end` 종료 |
|---|---|---|---|---|
| `rest_crouch` | 땅/물가 지지 유효 | 앞발·뒷발 정렬 | 호흡·몸 작게 움직이는 대기 | 점프/탐색 준비 |
| `ground_hop` | 지상 이동 의도 | 뒷다리 굽힘 | 짧은 홉 충격·공중 포즈 | 실제 접촉 시 앞/뒷발 착지 |
| `long_jump` | 허용 발판·목표·도약 권한 | 뒷다리 강한 압축 | 발사 1회·공중 모션·궤적 추종 | 물리 접촉 이후 회복 |
| `fall_land` | 지지 상실·낙하 | 접지 IK 해제 | 속도/중력 추종·몸 수축 | 착지 발 IK 조건부 복구 |
| `swim` | 수중 진입·안전 깊이 | 팔다리 물갈퀴 펼침 | 다리 젓기·수중 물리 이동 | 물밖 시 지지 자세 복원 |
| `orient_prey` | 성체/먹이 시각 단서 [설계] | 머리·눈 방향 전환 | 정지·먹이 거리 평가 | 혓바닥 공격 또는 무시 |
| `tongue_strike` | 유효 성체 표적/도달 범위 | 입 열기·혀 장전 | 활성 구간에서 1회 혀 충돌 검사 | 혀 회수/입 닫기 |
| `swallow` | 포획 확인 | 먹이·입 범위 유지 | 삼키기 시각 연출·효과 승인 | 입/머리 복구 |
| `evade_hide` | 교란/위험 | 도약 방향 탐색 | 지상 홉 또는 물로 회피 | 안정 지지/유영 복귀 |
- [설계] 개구리의 도약·착지는 `toktogi`의 furca/공중 상태와 독립; 같은 게임 물리 처리 순서와 객체별 발사 이벤트만 공유한다.
- [설계] 올챙이 수영·변태·젤리질 산란은 별도 연출/종 생태 모듈이며 성체 먹이 공격에 섞지 않는다.

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
| `body/head/neck_region` | 단단한 몸통·머리 회전 | 마스크 무늬·시선 안정 |
| `forelimb_L/R,hindlimb_L/R` | 4개 팔다리·긴 뒷다리 | 점프 압축·전방 착지 |
| `webbed_feet,foot_markers` | 발가락·물갈퀴·착지 | 유효 접촉 발만 IK |
| `jaw_upper/lower,tongue_base/tip` | 혀 사출·입 소켓 | 혀 시각 거리와 피격 판정 구분 |
| `eye_L/R,body_breath` | 시선·대기 호흡 | 복부/머리 시각 오프셋만 |
- [설계] 월동·포접·산란은 선택 배경 애니메이션이고, 지속 관계·교미 입력·협동 이동 등은 플레이 범위 밖이다.

## 6. 3D → 픽셀풍 2D 스프라이트 파이프라인
- **공통 파이프라인:** `원본 3D 모델+리그 → Action별 pre/mid/end → 고정 시점·포즈 샘플 → Base/Alpha/Normal/AO/ORM 출력 → 크롭/피벗/소켓 → Atlas/Manifest → 2D 재생`.
- 메타데이터: `asset_id, revision, action, phase, variant, sample_time, display_duration, view, pivot, bbox, support_markers, attack_socket`를 동일 프레임 묶음으로 보존한다.
- Base Color/Emissive 등 색 채널은 선언된 색공간으로, **Normal/ORM/Depth/coverage는 수치 데이터로** 디코딩한다. 픽셀풍 정수배 확대·경계/알파 검증.
- 실제 조명에 대한 Normal·Roughness/Metallic 반응을 시험하며 일부 정적 배경 베이크만 허용한다. 완성 조명 RGBA를 Albedo로 재조명하지 않는다.
- `DEC-06`의 방향 수·Normal 공간·Depth·앵커/좌표계는 **보류**. 한 시점 교정만으로 다방향 양산을 통과 처리하지 않는다.
- 3D IK·본 블렌드는 오프라인 제작에서 해결하고 2D 런타임은 클립·방향·표본/전이 선택. 시킹·FPS 변화·저장복원에서 사건 중복을 막는다.

## 7. 실행 데이터 예시(수치는 미결정)
```yaml
npc_id: predator_rana_temporaria
allowed_habitat: [damp_bank,grassland,woodland,breeding_pond,shallow_water]
locomotion: ground_hopping_and_swimming
prey_evidence: Podura_aquatica_response_test_only
phase: pre
target_id: null
support_id: null
attack_instance_id: null
damage: null
predation_probability: null
life_stage: adult
adult_body_length_cm_typical: [6, 8]
tadpole_feeding: separate_nonpredatory_life_stage
diet_podura_aquatica: reaction_study
diet_sminthurides_aquaticus: unverified
tongue_attack_range_u: null
asset_contract: DEC-06_deferred
```

## 8. 수락 시험 / 연구 검증 구분
- `RT-MOV-01` 큰 도약은 뒷다리 압축·1회 발사·물리 착지와 일치.
- `RT-MOV-02` 지상 홉→수영→지상 복귀에서 몸/팔다리/접지 전환.
- `RT-MOV-03` 혀 활성시간 밖 타격·한 사출 중복 피해 없음.
- `RT-MOV-04` 올챙이·성체 먹이 상태 분리, 유럽종을 한국 자생종으로 기록 금지.
- `RT-MOV-05` 움직이는 플랫폼/표층·발끝/혀 소켓·Normal 픽셀 검증.
- 실행·3D 리그·스프라이트 렌더 시험은 현재 **NOT_RUN**. 근거 미확인값은 `0`이 아니라 `null`/`unverified`.

## 9. 출처·업데이트 규칙
- [R01] [자료](https://doi.org/10.1078/S0031-4056(04)70041-4) — 다른 톡토기 종 반응 실험.
- [R02] [자료](https://reptiles-and-amphibians.linnaeus.naturalis.nl/linnaeus_ng/app/views/species/nsr_taxon.php?id=98989) — 형태·산란·변태.
- [R03] [자료](https://thehsi.org/native-reptiles-and-amphibians/common-frog/) — 서식·성체 먹이.
- [R05] [자료](https://www.thebhs.org/publications/the-herpetological-journal/volume-1-number-4-june-1987/1148-05-food-and-feeding-relations-of-common-frog-and-common-toad-tadpoles-rana-temporaria-and-bufo-bufo-at-a-pond-in-mid-wales) — 올챙이 먹이 차이.
- 프로젝트 공통: `toktogi_movement.md`(31장면 근거 구분), `3Dconv2D.md`, `toktogi_playable_action_animation_spec.md` v2.1.
- **변경 원칙:** 객체 학명·분류수준·먹이 동정·관찰 장면·장소·생애단계·원문 URL을 연결한다. 다른 먹이 종이나 지역의 사육 수치를 `S. aquaticus` 실측치로 전용하지 않는다.
