---
object_id: predator_pergamasus_crassipes
scientific_name: Pergamasus crassipes
taxonomic_rank: species
korean_name: null
version: '1.0'
review_date: '2026-11-17'
role_2dgp: soil_micro_predator_optional_npc
prey_toktogi_evidence: terrestrial_collembola_prey_not_aquaticus
---
# *Pergamasus crassipes* — 2DGP 이동·행동·애니메이션 명세
> 기준: ZIP의 같은 ID 생물 명세 v1.0·`nonspider_predator_objects_index.md` + `toktogi_movement.md`·거미류 Movement 공통 파이프라인·3Dconv2D/플랫포머 설계.
> **역할:** `toktogi`가 플레이어, 본 객체는 NPC/환경 위험 **설계 후보**. `[종 근거]`와 `[게임 설계]`, `[미확인]`을 별도 관리.

## 1. 생물학적 운동 근거·범위
- [분류] 응애류(Acari) 기생응애과(Parasitidae)의 종으로 **거미목 Araneae가 아님**. 성체 다리 4쌍; 생물학적 거미 공격·그물 리그 복제 금지. [P01]
- [형태] 종별 체장 미확인, 속 수준의 대략 0.8–1.5mm는 참고 사례. 주황·적갈색 타원형 몸·등판/강모·협각, 수컷 일부의 제2다리 변형. [P02]
- [서식] 숲 낙엽·토양·잔해 틈의 지상 포식성 응애; 1962년 연구 개체는 뉴욕 Tully Forest 토양에서 채집. 연못 수면 상시생활 근거 없음. [P01]
- [먹이 연구] *P. crassipes*와 *Amblygamasus septentrionalis*의 연구에서 톡토기·갑옷응애·진딧물 등 섭식; 두 종의 혼합 범위 수치 분리 유의. [P01]
- [행동] 토양 틈 탐색 → 접근 → 협각 접촉/포획 → 섭식은 자료를 게임용으로 단계화한 모델. 종별 접근속도·포획 지속시간은 미측정. [P01]
- [사육조건] 20°C·상대습도 약 90%에서 알 부화 24–36시간, 산란 약 3주 뒤 성체 발육 기록. 자연 수명·전체 지역 공통값 아님. [P01]
- [제약] *S. aquaticus* 수면 직접 포식·수면 보행·한국 분포 미확인. **수면 주요 천적**으로 배치하지 않음.

## 2. 행동 카탈로그 — AI 상태와 표현 클립 분리
| `action/clip` | 진입 가드 | `pre` 준비 | `mid` 동작·반복 | `end` 종료 |
|---|---|---|---|---|
| `hide_in_litter` | 토양 틈 지지 | 몸 낮춤·발 고정 | 미세 입/몸 움직임 | 틈 접근/탐색 |
| `creep` | 토양 경로 유효 | 앞다리 접촉 탐색 | 여덟 다리 짧은 보행·루트 이동 | 발 안정 |
| `edge_probe` | 틈·잔해 경계 | 앞다리 접촉/높이 검사 | 지지 가능한 틈 횡단 | 새 표면에 발 정착 |
| `detect_contact` | 먹이 접촉 단서 [설계] | 몸·앞다리 방향 조절 | 작은 촉각 탐색 | 접근 또는 복귀 |
| `approach` | 먹이/지상 경로 유효 | 협각·발 준비 | 느린 접근 | 접촉 범위 진입 |
| `chelicera_bite` | 협각 닿을 거리·공격 승인 | 입기관 정렬 | 활성 구간에서 1회 물기 판정 | 턱 복귀 |
| `feed` | 섭취 가능한 대상 | 협각 접촉 확인 | 구기 반복·자원 조건 검사 | 먹이 접촉 해제 |
| `retreat` | 진동·광량 등 위협 [설계] | 안정 틈 경로 선택 | 짧은 후퇴·숨기 | 숨기/탐색 복귀 |
| `fall_between_crumbs` | 지지 상실 | 발 IK 해제 | 물리 낙하·다른 흙 표면 접촉 | 안정 지지 확인 |
- [설계] 토양을 실제 3D 볼륨으로 모두 채울 필요 없이, 지원한 2D 플랫폼/잔해 틈에서 지상 이동만 검증한다.
- [설계] 원본의 단독 개체 산란·유충/약충·연 4~5세대 추정은 비전투 환경 연출; 물 표면 기능으로 확대하지 않는다.

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
| `idiosoma_dorsal/ventral` | 타원형 몸·등판 | 배 부분과 털/강모 윤곽 |
| `legs_L1..L4/R1..R4` | 성체 다리 8개·접촉 | 종/성별 제2다리 변형은 옵션 |
| `gnathosoma,chelicerae_L/R` | 입기관·먹이 고정 소켓 | 거미 독니·노린재 주둥이와 구별 |
| `setae_overlay` | 강모 가독성 | 저해상도에서 떨림 최소화 |
| `contact_feet,terrain_probe` | 토양 지지/틈 접근 | 지지 발만 IK 적용 |
- [설계] 속 사진만으로 종을 확정할 수 없으므로 최종 외형 승인 전에 동정 가능한 형태 자료를 요구한다.

## 6. 3D → 픽셀풍 2D 스프라이트 파이프라인
- **공통 파이프라인:** `원본 3D 모델+리그 → Action별 pre/mid/end → 고정 시점·포즈 샘플 → Base/Alpha/Normal/AO/ORM 출력 → 크롭/피벗/소켓 → Atlas/Manifest → 2D 재생`.
- 메타데이터: `asset_id, revision, action, phase, variant, sample_time, display_duration, view, pivot, bbox, support_markers, attack_socket`를 동일 프레임 묶음으로 보존한다.
- Base Color/Emissive 등 색 채널은 선언된 색공간으로, **Normal/ORM/Depth/coverage는 수치 데이터로** 디코딩한다. 픽셀풍 정수배 확대·경계/알파 검증.
- 실제 조명에 대한 Normal·Roughness/Metallic 반응을 시험하며 일부 정적 배경 베이크만 허용한다. 완성 조명 RGBA를 Albedo로 재조명하지 않는다.
- `DEC-06`의 방향 수·Normal 공간·Depth·앵커/좌표계는 **보류**. 한 시점 교정만으로 다방향 양산을 통과 처리하지 않는다.
- 3D IK·본 블렌드는 오프라인 제작에서 해결하고 2D 런타임은 클립·방향·표본/전이 선택. 시킹·FPS 변화·저장복원에서 사건 중복을 막는다.

## 7. 실행 데이터 예시(수치는 미결정)
```yaml
npc_id: predator_pergamasus_crassipes
allowed_habitat: [soil,moist_litter,ground_crumbs,under_debris]
locomotion: ground_creeping
prey_evidence: soil_collembola_study_not_aquaticus
phase: pre
target_id: null
support_id: null
attack_instance_id: null
damage: null
predation_probability: null
body_length_mm_species: null
reference_genus_length_mm: [0.8, 1.5]
water_surface_hunting: unverified_not_enabled
diet_sminthurides_aquaticus: unverified
lab_egg_hatch_hours_20c: [24, 36]
attack_range_u: null
asset_contract: DEC-06_deferred
```

## 8. 수락 시험 / 연구 검증 구분
- `PC-MOV-01` 성체 여덟 다리와 토양/낙엽 틈 발 접촉 유지.
- `PC-MOV-02` 협각 접촉·한 공격의 피해 횟수·섭식 효과 구분.
- `PC-MOV-03` 수면 보행/점프/거미 독니·거미줄 자동 생성 금지.
- `PC-MOV-04` 20°C·90% 사육 발육 시간을 AI 속도/회복으로 전용하지 않음.
- `PC-MOV-05` 강모·제2다리 선택형과 최종 픽셀/Normal/IK 정합.
- 실행·3D 리그·스프라이트 렌더 시험은 현재 **NOT_RUN**. 근거 미확인값은 `0`이 아니라 `null`/`unverified`.

## 9. 출처·업데이트 규칙
- [P01] [자료](https://doi.org/10.1093/aesa/55.2.196) — 토양 포식성 응애 사육·섭식·발육.
- [P02] [자료](https://jessica-joachim.com/arachnides-2/acariens/paasitidae/pergamasus-sp/) — 속 수준 외형 참조.
- 프로젝트 공통: `toktogi_movement.md`(31장면 근거 구분), `3Dconv2D.md`, `toktogi_playable_action_animation_spec.md` v2.1.
- **변경 원칙:** 객체 학명·분류수준·먹이 동정·관찰 장면·장소·생애단계·원문 URL을 연결한다. 다른 먹이 종이나 지역의 사육 수치를 `S. aquaticus` 실측치로 전용하지 않는다.
