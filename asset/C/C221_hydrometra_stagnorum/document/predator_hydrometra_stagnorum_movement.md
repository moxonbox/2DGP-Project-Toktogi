---
object_id: predator_hydrometra_stagnorum
scientific_name: Hydrometra stagnorum
taxonomic_rank: species
korean_name: null
version: '1.0'
review_date: '2026-11-17'
role_2dgp: water_edge_surface_predator_npc
prey_toktogi_evidence: photo_report_species_identification_unverified
---
# *Hydrometra stagnorum* — 2DGP 이동·행동·애니메이션 명세
> 기준: ZIP의 같은 ID 생물 명세 v1.0·`nonspider_predator_objects_index.md` + `toktogi_movement.md`·거미류 Movement 공통 파이프라인·3Dconv2D/플랫포머 설계.
> **역할:** `toktogi`가 플레이어, 본 객체는 NPC/환경 위험 **설계 후보**. `[종 근거]`와 `[게임 설계]`, `[미확인]`을 별도 관리.

## 1. 생물학적 운동 근거·범위
- [종 카드] 성체 몸길이 9–12.5mm(영국 자료 약 9–13mm); 가는 막대형 몸·긴 머리·여섯 가는 다리. 최대치·평균 게임 배율 혼동 금지. [T02][T03]
- [종 형태] 눈은 머리의 뒤쪽에 위치; 눈 앞쪽 머리 길이가 눈 뒤쪽보다 약 두 배라는 감별 단서, 짧은/긴 날개형의 변이. 장시형 비행을 필수 능력으로 만들지 않음. [T02]
- [서식] 유럽·북아프리카·중앙아시아의 고요한 수역·얕은 물가·젖은 식물·돌을 오감; 한국 분포는 이 자료에서 미확인. [T02][T03]
- [행동] 수면 진동 단서 → 천천히 접근 → 접힌 주둥이(rostrum)로 찌르기 → 흡즙; 사냥과 사체 청소를 구분. [T02][T03]
- [먹이] 프랑스 Beaumont 사진 캡션에 *S. aquaticus* 섭식 표기가 있으나 독립적인 양쪽 종 동정·반복 관찰은 미확인. [T01]
- [생애] 식물 등에 알 하나씩 세워 붙이는 종별 관찰; 알 길이 약 0.869–1.10mm·폭 약 0.248–0.314mm(2024년 연구). 이동 AI의 고정 크기로 전용 금지. [T04]
- [제약] *H. martini*의 *S. malmgreni* 사육실험이나 지역별 연 2세대·월동 사례를 본 종의 먹이 성공률·생활사 수치로 전용 금지. [T02][T05]

## 2. 행동 카탈로그 — AI 상태와 표현 클립 분리
| `action/clip` | 진입 가드 | `pre` 준비 | `mid` 동작·반복 | `end` 종료 |
|---|---|---|---|---|
| `rest_on_surface` | 유효 수면·부유물 접촉 | 여섯 다리 지지·주둥이 접힘 | 미세 머리/더듬이 탐색 루프 | 상태 변경 시 접지 자세 전달 |
| `surface_walk` | 이동 경로 유효 | 앞다리 목표·걸음 진입 | 느린 수면 보행·물리 루트 이동 | 발 정착·감속 |
| `edge_transition` | 수면↔젖은 식물 연결 | 다리·몸 기울기 정렬 | 지지 재선택·접촉점 변경 | 새 표면 지지 확정 |
| `detect_vibration` | 감지 이벤트 수신 [설계] | 단서 유효성 평가 | 머리·앞다리 방향 정렬 | 접근 또는 관찰 복귀 |
| `approach` | 표적·진입 경로 유효 | 장애물·표면 확인 | 과속 없는 단거리 접근 | 사정거리 정렬 또는 포기 |
| `probe` | 공격 허용·주둥이 닿을 거리 | 주둥이 준비·정렬 | 접촉 활성 구간에 1회 찌르기 판정 | 주둥이 접고 타격 종료 |
| `feed_or_scavenge` | 유효 먹이/사체 대상 | 주둥이 접촉 목표 재확인 | 흡즙 표현, 효과는 별도 승인 | 접촉·자원 참조 해제 |
| `withdraw` | 방해·사냥 실패 | 몸 방향 전환 | 수면/식물 위로 이탈 | 안정 발 지지 복구 |
| `fall_or_invalid_surface` | 지지 소실·허용 영역 밖 | 발 IK 해제 | 시뮬레이션 낙하/실패 표시 | 유효 접촉이면 정상 복귀 |
- [설계] 수면 정지와 먹이 포획을 자동 성공으로 묶지 않는다. 생체 공격과 사체 섭식은 `prey_status`로 구별한다.
- [설계] 장시형 이륙·착륙, 알 부착, 월동은 제작 승인된 배경 연출에만 포함하며 기본 적 공격 AI가 아니다.

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
| `body_long/head_long` | 가는 머리·몸의 직선성/굽힘 | 머리의 길이·방향 유지 |
| `leg_LF/LM/LH,leg_RF/RM/RH` | 여섯 다리와 지지 발 IK | 수면/잎에서 현재 유효 다리만 고정 |
| `antenna_L/R,eye_pair` | 진동/탐색 지향 | 동정용 눈 위치·더듬이 구별 |
| `rostrum_ctrl,rostrum_tip` | 흡즙 공격·먹이 접촉 소켓 | 실제 입 끝과 공격 판정 위치 정합 |
| `wing_morph_optional` | 단시형/장시형 외형 분기 | 기본 비행 기능 미추가 |
- [설계] 생식·발육은 비플레이어 연출 참고로만 보존하며 필수 `attack`/`movement` 상태가 아니다.

## 6. 3D → 픽셀풍 2D 스프라이트 파이프라인
- **공통 파이프라인:** `원본 3D 모델+리그 → Action별 pre/mid/end → 고정 시점·포즈 샘플 → Base/Alpha/Normal/AO/ORM 출력 → 크롭/피벗/소켓 → Atlas/Manifest → 2D 재생`.
- 메타데이터: `asset_id, revision, action, phase, variant, sample_time, display_duration, view, pivot, bbox, support_markers, attack_socket`를 동일 프레임 묶음으로 보존한다.
- Base Color/Emissive 등 색 채널은 선언된 색공간으로, **Normal/ORM/Depth/coverage는 수치 데이터로** 디코딩한다. 픽셀풍 정수배 확대·경계/알파 검증.
- 실제 조명에 대한 Normal·Roughness/Metallic 반응을 시험하며 일부 정적 배경 베이크만 허용한다. 완성 조명 RGBA를 Albedo로 재조명하지 않는다.
- `DEC-06`의 방향 수·Normal 공간·Depth·앵커/좌표계는 **보류**. 한 시점 교정만으로 다방향 양산을 통과 처리하지 않는다.
- 3D IK·본 블렌드는 오프라인 제작에서 해결하고 2D 런타임은 클립·방향·표본/전이 선택. 시킹·FPS 변화·저장복원에서 사건 중복을 막는다.

## 7. 실행 데이터 예시(수치는 미결정)
```yaml
npc_id: predator_hydrometra_stagnorum
allowed_habitat: [shallow_surface,pond_edge,emergent_plant,wet_bank]
locomotion: slow_surface_walking
prey_evidence: photographic_caption_both_species_unverified_identification
phase: pre
target_id: null
support_id: null
attack_instance_id: null
damage: null
predation_probability: null
source_species_identification: photo_caption_needs_independent_check
occurrence_south_korea: unverified
wing_morph: configurable_not_flight_by_default
detect_range_u: null
approach_speed_u_s: null
probe_damage: null
asset_contract: DEC-06_deferred
```

## 8. 수락 시험 / 연구 검증 구분
- `HS-MOV-01` 수면↔젖은 줄기 전환 시 실제 지지 보존·다리 매달림 없음.
- `HS-MOV-02` 진동·접근·찌르기·흡즙 순서와 공격 구간 일치.
- `HS-MOV-03` 사체/생체 구분·공격 취소·동일 프레임 중복 피해 차단.
- `HS-MOV-04` 단시형의 비행 자동 재생 금지·한국 분포 미확인 보존.
- `HS-MOV-05` 긴 머리·6발·주둥이 소켓과 최종 색/Normal 정합.
- 실행·3D 리그·스프라이트 렌더 시험은 현재 **NOT_RUN**. 근거 미확인값은 `0`이 아니라 `null`/`unverified`.

## 9. 출처·업데이트 규칙
- [T01] [자료](https://www.jbnature.com/insectes/hemipteres/hydrom%C3%A9trid%C3%A9s) — 프랑스 종명 기재 사진 캡션.
- [T02] [자료](https://www.wanzen-im-ruhrgebiet.de/artenprofile/hydrometridae/hydrometra-stagnorum/) — 몸길이·형태·서식·날개.
- [T03] [자료](https://www.iucn-uk-peatlandprogramme.org/wildlife-explorer/invertebrates/bugs/common-water-measurer) — 수면 진동·포식·청소.
- [T04] [자료](https://academic.oup.com/mam/article/30/5/978/7731631) — 알·산란 관찰.
- [T05] [자료](https://doi.org/10.2307/3496223) — 다른 Hydrometra 종 사육실험.
- 프로젝트 공통: `toktogi_movement.md`(31장면 근거 구분), `3Dconv2D.md`, `toktogi_playable_action_animation_spec.md` v2.1.
- **변경 원칙:** 객체 학명·분류수준·먹이 동정·관찰 장면·장소·생애단계·원문 URL을 연결한다. 다른 먹이 종이나 지역의 사육 수치를 `S. aquaticus` 실측치로 전용하지 않는다.
