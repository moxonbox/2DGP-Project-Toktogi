---
object_id: predator_stenus
scientific_name: Stenus
taxonomic_rank: genus
korean_name: 딱부리반날개속
version: '1.0'
review_date: '2026-11-17'
role_2dgp: bank_ambush_predator_npc
prey_toktogi_evidence: springtail_capture_multiple_stenus_species
---
# 딱부리반날개속 (*Stenus*) — 2DGP 이동·행동·애니메이션 명세
> 기준: ZIP의 같은 ID 생물 명세 v1.0·`nonspider_predator_objects_index.md` + `toktogi_movement.md`·거미류 Movement 공통 파이프라인·3Dconv2D/플랫포머 설계.
> **역할:** `toktogi`가 플레이어, 본 객체는 NPC/환경 위험 **설계 후보**. `[종 근거]`와 `[게임 설계]`, `[미확인]`을 별도 관리.

## 1. 생물학적 운동 근거·범위
- [분류] 딱정벌레목 반날개과의 **속**. 한국의 *S. koreanus* 표본 몸길이 3.2–3.3mm는 종 사례이고 속의 공통 크기 아님. [S04]
- [형태] 큰 겹눈, 짧은 딱지날개와 노출된 배, 여섯 다리, 끈적한 포획 패드가 있는 **사출형 아랫입술(labium)**. [S01][S03]
- [종 차이] *S. comma*는 지상 빠른 추격이 가능하지만 식생·부식질 중심 종은 대기/기습 의존이 높음. 같은 AI 속도로 고정하지 않음. [S06]
- [종 실험] 여러 *Stenus*의 톡토기 포획 비교에서 아랫입술이 위턱보다 효과적인 종이 많지만, 사냥 장치 사용 빈도·거리·성공률은 종별 차이. [S01]
- [종 사례] *S. comma*는 위턱 공격도 활용, 큰/강모 많은 톡토기는 접착 패드에서 떨어질 수 있음. [S02]
- [조건부] 일부 *Stenus*의 배 끝 분비물 이용 수면 스키밍은 **속 전체 기본 능력 아님**. 수면 포식 필수 NPC로 설정 금지. [S03][S05]
- [미확인] *S. aquaticus* 직접포식, 한국의 특정 연못 동시출현, 공격거리·속도·확률·먹이별 방어 반응.

## 2. 행동 카탈로그 — AI 상태와 표현 클립 분리
| `action/clip` | 진입 가드 | `pre` 준비 | `mid` 동작·반복 | `end` 종료 |
|---|---|---|---|---|
| `rest_scan` | 지상/식생 지지 | 여섯 발 안정 | 큰 눈·더듬이로 탐색 | 경로 선택 |
| `ground_search` | 식생/토양 경로 | 보행 진입 | 이동/정지 섞인 탐색 | 방향 정렬 |
| `stalk` | 포획가능 지면·표적 | 몸 낮춤·입 준비 | 천천히 접근 | 공격 사정거리 진입 |
| `fast_run_variant` | 민첩형 종 프로필 [설계] | 방향/속도 준비 | 빠른 지상 이동 | 제동·발 정리 |
| `align_capture` | 표적 접촉 후보 | 몸·머리·아랫입술 정렬 | 공격 모드 선택 | 사출/위턱 중 하나 |
| `labium_strike` | 사출형 프로필·공격 자격 | labium 접기·발 지지 | 사출→패드 접촉 검사 1회 | 수축·대상 해제 |
| `mandible_strike` | 위턱형 공격 가능 | 머리·위턱 정렬 | 짧은 돌진/물기 판정 1회 | 위턱 복귀 |
| `feed` | 획득된 먹이 자원 | 협각이 아닌 위턱과 입 접촉 | 구기 반복·효과 조건 검사 | 자원 놓기 |
| `evade_or_skimming` | 위협·수면 경계 | 방향 결정/종 프로필 확인 | 지상 회피 또는 승인된 skimming | 안정 접지 복귀 |
- [설계] 기본 포획은 **사출 아랫입술 또는 위턱** 중 공격 프로필이 선택한 하나만 발동; 둘을 자동 중복 타격으로 처리 금지.
- [설계] 일부 종 수면 스키밍, 완전변태의 유충·번데기·산란은 비필수 옵션으로 보존.

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
| `head/compound_eyes` | 머리 방향·큰 겹눈 | 종별 눈·턱 역할 보존 |
| `thorax/abdomen/elytra` | 짧은 앞날개·노출 복부 | 몸통 굽힘, 배끝 분비관 |
| `legs_3pairs,foot_targets` | 여섯 발과 보행/기습 | 속 유형별 지지 정책 |
| `labium_root,labium_pad` | 사출·접착 소켓 | 끝점과 명중 영역 일치 |
| `mandible_L/R,abdomen_tip` | 턱 공격·선택 skimming | 공격 수단/방어 분비 구분 |
- [설계] 선택 종 미정 상태에서 `Stenus` 속 전체의 특정 공격 비율·수면 주행을 기본값으로 확정하지 않는다.

## 6. 3D → 픽셀풍 2D 스프라이트 파이프라인
- **공통 파이프라인:** `원본 3D 모델+리그 → Action별 pre/mid/end → 고정 시점·포즈 샘플 → Base/Alpha/Normal/AO/ORM 출력 → 크롭/피벗/소켓 → Atlas/Manifest → 2D 재생`.
- 메타데이터: `asset_id, revision, action, phase, variant, sample_time, display_duration, view, pivot, bbox, support_markers, attack_socket`를 동일 프레임 묶음으로 보존한다.
- Base Color/Emissive 등 색 채널은 선언된 색공간으로, **Normal/ORM/Depth/coverage는 수치 데이터로** 디코딩한다. 픽셀풍 정수배 확대·경계/알파 검증.
- 실제 조명에 대한 Normal·Roughness/Metallic 반응을 시험하며 일부 정적 배경 베이크만 허용한다. 완성 조명 RGBA를 Albedo로 재조명하지 않는다.
- `DEC-06`의 방향 수·Normal 공간·Depth·앵커/좌표계는 **보류**. 한 시점 교정만으로 다방향 양산을 통과 처리하지 않는다.
- 3D IK·본 블렌드는 오프라인 제작에서 해결하고 2D 런타임은 클립·방향·표본/전이 선택. 시킹·FPS 변화·저장복원에서 사건 중복을 막는다.

## 7. 실행 데이터 예시(수치는 미결정)
```yaml
npc_id: predator_stenus
allowed_habitat: [wet_bank,litter,vegetation,ground]
locomotion: ground_run_or_vegetation_stalk
prey_evidence: springtail_capture_experiment_not_S_aquaticus
phase: pre
target_id: null
support_id: null
attack_instance_id: null
damage: null
predation_probability: null
species_selected: null
example_body_length_mm_stenus_koreanus: [3.2, 3.3]
capture_tool: labium_or_mandible_profile
surface_skimming: species_dependent_disabled_default
diet_sminthurides_aquaticus: unverified
attack_range_u: null
asset_contract: DEC-06_deferred
```

## 8. 수락 시험 / 연구 검증 구분
- `ST-MOV-01` 지상 탐색·기습/민첩형 변형이 종 프로필대로 분기.
- `ST-MOV-02` labium 사출·복귀와 패드 타격 영역 일치.
- `ST-MOV-03` 위턱/아랫입술 중복 피해 없음·접착 실패도 정상 종료.
- `ST-MOV-04` 속의 수면 스키밍 기능 무조건 활성화 금지.
- `ST-MOV-05` 짧은 딱지날개·6발·눈·입 마커 및 2D Normal 정합.
- 실행·3D 리그·스프라이트 렌더 시험은 현재 **NOT_RUN**. 근거 미확인값은 `0`이 아니라 `null`/`unverified`.

## 9. 출처·업데이트 규칙
- [S01] [자료](https://doi.org/10.1111/j.1469-7998.1998.tb00058.x) — 아랫입술/위턱 포획 비교.
- [S02] [자료](https://www.sciencedirect.com/science/article/pii/S0003347205803495) — *S. comma* 종별 공격 사례.
- [S03] [자료](https://ask.ifas.ufl.edu/publication/IN272) — 반날개류·Stenus 일반 생태.
- [S04] [자료](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002052478) — 한국 속 기록.
- [S05] [자료](https://www.sciencedirect.com/science/article/abs/pii/S1467803913000236) — 수면 스키밍 기작.
- [S06] [자료](https://www.sciencedirect.com/science/article/pii/S0929139398000560) — 지면·식생 사냥형 차이.
- 프로젝트 공통: `toktogi_movement.md`(31장면 근거 구분), `3Dconv2D.md`, `toktogi_playable_action_animation_spec.md` v2.1.
- **변경 원칙:** 객체 학명·분류수준·먹이 동정·관찰 장면·장소·생애단계·원문 URL을 연결한다. 다른 먹이 종이나 지역의 사육 수치를 `S. aquaticus` 실측치로 전용하지 않는다.
