---
object_id: predator_mesovelia_vittigera
scientific_name: Mesovelia vittigera
taxonomic_rank: species
korean_name: 물노린재
version: '1.0'
review_date: '2026-11-17'
role_2dgp: floating_vegetation_predator_candidate_npc
prey_toktogi_evidence: habitat_overlap_not_confirmed_predation
---
# 물노린재 (*Mesovelia vittigera*) — 2DGP 이동·행동·애니메이션 명세
> 기준: ZIP의 같은 ID 생물 명세 v1.0·`nonspider_predator_objects_index.md` + `toktogi_movement.md`·거미류 Movement 공통 파이프라인·3Dconv2D/플랫포머 설계.
> **역할:** `toktogi`가 플레이어, 본 객체는 NPC/환경 위험 **설계 후보**. `[종 근거]`와 `[게임 설계]`, `[미확인]`을 별도 관리.

## 1. 생물학적 운동 근거·범위
- [국내 연구] *M. vittigera*는 2024년 고양 일산호수공원·의왕 왕송저수지·여러 지역 표본이 보고된 한국 출현종. `toktogi`와 같은 연못 동시 출현은 별도 확인 필요. [V01]
- [종 형태] 몸길이 2.0–3.5mm(태국 문헌 사례), 녹색빛 황록·황갈색의 길쭉한 몸·겹눈·긴 더듬이·여섯 다리. [V02][V03]
- [형태 변이] 무시형과 장시형 존재, 한국 표본에 장시형 수컷 기록; 외형만으로 모든 개체의 비행을 허용하지 않음. [V01]
- [서식] 호수·논·저수지·기수 연못의 잎/줄기·수면에서 이동하며, 식물 군락 변화 시 지지 표면도 달라짐. [V01][V03]
- [과/속 생태] 수면 진동으로 작은 수생무척추동물을 탐지하고 주둥이로 흡즙, 사체도 이용. 해당 종의 표준 먹이비율은 미확인. [V02]
- [타종 기록] *M. furcata*와 *Smynthurus* 섭식은 1917년의 1893년 기록 재인용, *M. mulsanti* 약충은 공격 중 뒤집힘 사례. *M. vittigera* 포획 성공 증거 아님. [V07]
- [제약] *S. bifidus*와 *Mesovelia* sp.의 개구리밥 공존 사진은 양측 종이 다름; 본 종의 물알둥근톡토기 직접 포식은 미확인. [V06]

## 2. 행동 카탈로그 — AI 상태와 표현 클립 분리
| `action/clip` | 진입 가드 | `pre` 준비 | `mid` 동작·반복 | `end` 종료 |
|---|---|---|---|---|
| `rest_leaf` | 부유잎/줄기 접촉 | 여섯 발·몸 안정 | 더듬이 작은 스캔 | 다음 행동 전환 |
| `leaf_walk` | 식물 지지점 연결 | 앞다리 지지 전환 | 잎 위 보행·물리 루트 이동 | 기존 발 고정 해제 |
| `surface_cross` | 허용 수면 구간 | 잎에서 수면으로 자세 낮춤 | 표면 보행·접촉 ID 갱신 | 새 잎/물가 지지 |
| `vibration_orient` | 진동 단서 [설계] | 방향·표면 평가 | 머리·더듬이 방향 정렬 | 접근 또는 탐색 |
| `approach` | 대상/진입 경로 유효 | 충돌·도달거리 검사 | 짧은 이동·느린/빠른 변형 | 접촉 거리 정렬 |
| `rostrum_probe` | 공격 허용 | 주둥이 끝점 조준 | 활성 구간에서 1회 접촉 판정 | 주둥이 접기 |
| `feed_scavenge` | 생체/사체 자원 유효 | 입 접촉 확인 | 흡즙 루프·유효 자원 검사 | 입과 자원 해제 |
| `evade_reset` | 위협/표면 흔들림 | 안정 방향 결정 | 잎·식생으로 이탈 | 지지 복원 |
| `fall_from_leaf` | 지지 상실 | 현재 발 IK 해제 | 물리 낙하/접촉 결과 추종 | 새 지지 유효 시 복귀 |
- [설계] 역사문헌의 *M. furcata* 사냥·*M. mulsanti* 뒤집힘은 선택적 타종 참고이며 본 종 필수 공격/실패 모션이 아니다.
- [설계] 장시형 비행, 식물 조직 산란(속 수준)은 비필수 환경 확장으로 유지한다.

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
| `head/thorax/abdomen` | 길쭉한 황록 몸 | 녹색 톤/가슴·복부 형태 유지 |
| `legs_3pairs,foot_targets` | 식물/수면에 닿는 여섯 발 | 잎 기울기와 지지 IK |
| `antennae,compound_eyes` | 수면 진동 방향 표시 | 탐지 확정은 AI 소유 |
| `rostrum,rostrum_tip` | 찌르기·흡즙 | 생체/사체 처리 구분 |
| `wings_variant_optional` | 무시/장시 외형 | 모든 개체의 비행 자동 생성 금지 |
- [설계] 수컷 복부 제8복판 등 종 동정 형질은 외형 검수용; 교미·산란 등 관계·생식 플레이는 범위 밖.

## 6. 3D → 픽셀풍 2D 스프라이트 파이프라인
- **공통 파이프라인:** `원본 3D 모델+리그 → Action별 pre/mid/end → 고정 시점·포즈 샘플 → Base/Alpha/Normal/AO/ORM 출력 → 크롭/피벗/소켓 → Atlas/Manifest → 2D 재생`.
- 메타데이터: `asset_id, revision, action, phase, variant, sample_time, display_duration, view, pivot, bbox, support_markers, attack_socket`를 동일 프레임 묶음으로 보존한다.
- Base Color/Emissive 등 색 채널은 선언된 색공간으로, **Normal/ORM/Depth/coverage는 수치 데이터로** 디코딩한다. 픽셀풍 정수배 확대·경계/알파 검증.
- 실제 조명에 대한 Normal·Roughness/Metallic 반응을 시험하며 일부 정적 배경 베이크만 허용한다. 완성 조명 RGBA를 Albedo로 재조명하지 않는다.
- `DEC-06`의 방향 수·Normal 공간·Depth·앵커/좌표계는 **보류**. 한 시점 교정만으로 다방향 양산을 통과 처리하지 않는다.
- 3D IK·본 블렌드는 오프라인 제작에서 해결하고 2D 런타임은 클립·방향·표본/전이 선택. 시킹·FPS 변화·저장복원에서 사건 중복을 막는다.

## 7. 실행 데이터 예시(수치는 미결정)
```yaml
npc_id: predator_mesovelia_vittigera
allowed_habitat: [floating_vegetation,pond_surface,rice_paddy,brackish_pond_examples]
locomotion: leaf_and_surface_walking
prey_evidence: toktogi_direct_predation_unverified
phase: pre
target_id: null
support_id: null
attack_instance_id: null
damage: null
predation_probability: null
occurrence_korea: confirmed_species_2024
wing_morph: [apterous, macropterous]
diet_sminthurides_aquaticus: unverified
candidate_basis: shared_floating_vegetation_habitat
detection_range_u: null
probe_damage: null
asset_contract: DEC-06_deferred
```

## 8. 수락 시험 / 연구 검증 구분
- `MV-MOV-01` 잎→수면→잎 이동 중 실제 지지·발끝 정합.
- `MV-MOV-02` 진동 탐색·주둥이 활성·섭식/사체 청소 구분.
- `MV-MOV-03` *M. furcata*의 먹이기록을 이 종의 확정 결과로 바꾸지 않음.
- `MV-MOV-04` 장시/무시형을 올바르게 렌더하고 날개 없는 개체 비행 차단.
- `MV-MOV-05` 한국 발생 기록과 `toktogi` 직접포식 미확인을 별도 표시.
- 실행·3D 리그·스프라이트 렌더 시험은 현재 **NOT_RUN**. 근거 미확인값은 `0`이 아니라 `null`/`unverified`.

## 9. 출처·업데이트 규칙
- [V01] [자료](https://pmc.ncbi.nlm.nih.gov/articles/PMC11494210/) — 한국 종 동정·분포.
- [V02] [자료](https://www.mdfrc.org.au/bugguide/display.asp?Family=49&Order=3&Subclass=&class=17&couplet=0&fromcouplet=8&genus=&species=&type=5) — 과 수준 감각·포식.
- [V03] [자료](https://www.mdpi.com/1424-2818/14/6/466) — 크기·동남아 서식.
- [V06] [자료](https://www.bugguide.net/node/view/1138706/bgimage) — 다른 톡토기·물노린재 동시 관찰.
- [V07] [자료](https://doi.org/10.1155/1917/57095) — 근연종 톡토기 섭식 재인용.
- 프로젝트 공통: `toktogi_movement.md`(31장면 근거 구분), `3Dconv2D.md`, `toktogi_playable_action_animation_spec.md` v2.1.
- **변경 원칙:** 객체 학명·분류수준·먹이 동정·관찰 장면·장소·생애단계·원문 URL을 연결한다. 다른 먹이 종이나 지역의 사육 수치를 `S. aquaticus` 실측치로 전용하지 않는다.
