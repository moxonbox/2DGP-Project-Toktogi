---
object_id: predator_microvelia_reticulata
scientific_name: Microvelia reticulata
taxonomic_rank: species
korean_name: 얼룩깨알소금쟁이
version: '1.0'
review_date: '2026-11-17'
role_2dgp: fast_surface_predator_npc
prey_toktogi_evidence: collembola_unspecified_species_observed
---
# 얼룩깨알소금쟁이 (*Microvelia reticulata*) — 2DGP 이동·행동·애니메이션 명세
> 기준: ZIP의 같은 ID 생물 명세 v1.0·`nonspider_predator_objects_index.md` + `toktogi_movement.md`·거미류 Movement 공통 파이프라인·3Dconv2D/플랫포머 설계.
> **역할:** `toktogi`가 플레이어, 본 객체는 NPC/환경 위험 **설계 후보**. `[종 근거]`와 `[게임 설계]`, `[미확인]`을 별도 관리.

## 1. 생물학적 운동 근거·범위
- [종 카드] 성체 몸길이 1.4–1.8mm(지역 관찰); 짙은 몸색과 흰빛 방수 미세털, 앞가슴등판의 끊긴 연황색 띠·겹눈·여섯 다리. [M01]
- [서식] 초목 밀집 연못 가장자리·부유잎·수면 이동; 한국 수서곤충 목록 등재이나 특정 연못의 `toktogi` 동시출현은 미확인. [M01][M04]
- [종 행동] 방수털/수면장력 이용해 빠르게 걷고 미끄러지듯 이동하며 흡즙형 주둥이로 소형 절지동물 섭식. [M01][M02]
- [직접 관찰] 미동정 **수면 톡토기**를 흡즙하는 현장 보고. *S. aquaticus* 종명을 기재한 먹이 근거가 아님. [M01]
- [종 실험] *Podura aquatica* 방어 물질에 대한 포식자 반응은 별도의 먹이 종을 이용한 결과; 회피률을 `toktogi`에 직접 대입 금지. [M03]
- [날개/발육] 성체 무시형이 흔하고 유시형은 드묾; 약충은 성체 무시형과 구분. 원문은 약충 **4령/5령 설명 충돌**, 정확한 령 수 보류. [M01][M02]
- [미확인] 실제 공격 속도·최대 이동속도·탐지거리·먹이 비율·종별 포식률·수중 완전 잠수 능력.

## 2. 행동 카탈로그 — AI 상태와 표현 클립 분리
| `action/clip` | 진입 가드 | `pre` 준비 | `mid` 동작·반복 | `end` 종료 |
|---|---|---|---|---|
| `rest` | 수면 지지 유효 | 여섯 발 위치 안정 | 더듬이·몸의 약한 대기 | 다음 행동 준비 |
| `scurry` | 수면 경로·접촉 유효 | 빠른 발 주기 진입 | 빠른 보행/활주 표현·물리 이동 | 감속·착지 발 정돈 |
| `leaf_cross` | 부유잎/수면 경계 | 선행 발/몸 방향 맞춤 | 지지 표면 재선택 | 선택 접촉 발 유지 |
| `scan` | 주변 단서 [설계] | 더듬이·머리 정렬 | 작은 회전/일시 정지 | 표적 또는 복귀 |
| `approach` | 작은 대상·경로 유효 | 진입 각도 정렬 | 단거리 추적·회피 가능 | 공격 사정거리 도달 |
| `pierce_probe` | 대상 닿을 거리 | 주둥이 돌출 준비 | 활성 구간 중 1회 관통 판정 | 입 접기·공격 종료 |
| `feed` | 섭식 가능한 대상 | 입 접촉 유효성 재검사 | 흡즙 시각 루프/자원 효과 | 해제 후 정리 |
| `evade` | 위험·방해 | 방향 재선택 | 수면/부유잎 쪽 회피 | 안정 지지 복구 |
| `lose_surface` | 실제 수면 지지 상실 | 발 IK 해제 | 낙하/이탈 물리 결과 추종 | 새 지지 시 복귀 |
- [설계] 유시형의 비행·약충 발육은 환경 확장 전용; 무시형 성체의 일반 공중기동으로 설정 금지.
- [설계] 먹이를 찌른 사실과 실제 섭식·피해 적용을 분리하며, 잘못된 먹이 종 승격을 방지한다.

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
| `thorax/abdomen/head` | 타원 몸·머리 회전 | 끊긴 연황색 띠와 테두리 윤곽 |
| `legs_3pairs,foot_contacts` | 여섯 다리 수면 지지·빠른 주기 | 방수털 외형과 물리 접촉 분리 |
| `antenna_L/R,compound_eye_L/R` | 탐색 방향 | 종별 더듬이/눈 가독성 |
| `rostrum_ctrl,rostrum_tip` | 찌르기·흡즙 소켓 | 다른 종의 턱으로 대체 금지 |
| `wing_variant_optional` | 무시형·유시형 분기 | 약충 혼동·필수 비행 방지 |
- [설계] 번식 시 식물/부유물 산란, 지역별 세대수는 배경 생태 연출로만 기록; 기본 AI의 공격 능력과 무관하다.

## 6. 3D → 픽셀풍 2D 스프라이트 파이프라인
- **공통 파이프라인:** `원본 3D 모델+리그 → Action별 pre/mid/end → 고정 시점·포즈 샘플 → Base/Alpha/Normal/AO/ORM 출력 → 크롭/피벗/소켓 → Atlas/Manifest → 2D 재생`.
- 메타데이터: `asset_id, revision, action, phase, variant, sample_time, display_duration, view, pivot, bbox, support_markers, attack_socket`를 동일 프레임 묶음으로 보존한다.
- Base Color/Emissive 등 색 채널은 선언된 색공간으로, **Normal/ORM/Depth/coverage는 수치 데이터로** 디코딩한다. 픽셀풍 정수배 확대·경계/알파 검증.
- 실제 조명에 대한 Normal·Roughness/Metallic 반응을 시험하며 일부 정적 배경 베이크만 허용한다. 완성 조명 RGBA를 Albedo로 재조명하지 않는다.
- `DEC-06`의 방향 수·Normal 공간·Depth·앵커/좌표계는 **보류**. 한 시점 교정만으로 다방향 양산을 통과 처리하지 않는다.
- 3D IK·본 블렌드는 오프라인 제작에서 해결하고 2D 런타임은 클립·방향·표본/전이 선택. 시킹·FPS 변화·저장복원에서 사건 중복을 막는다.

## 7. 실행 데이터 예시(수치는 미결정)
```yaml
npc_id: predator_microvelia_reticulata
allowed_habitat: [pond_margin,water_surface,floating_leaf,wet_vegetation]
locomotion: water_surface_scurry
prey_evidence: unspecified_surface_springtail_observation
phase: pre
target_id: null
support_id: null
attack_instance_id: null
damage: null
predation_probability: null
wing_morph: usually_apterous
nymphal_instars: null # 원본에 4령/5령 충돌
diet_sminthurides_aquaticus: unverified
occurrence_korea: recorded_species
speed_u_s: null
attack_range_u: null
asset_contract: DEC-06_deferred
```

## 8. 수락 시험 / 연구 검증 구분
- `MR-MOV-01` 수면 빠른 이동/부유잎 경계의 지지와 충돌 일치.
- `MR-MOV-02` 찌르기 활성 구간과 흡즙 루프의 피해 중복 없음.
- `MR-MOV-03` 날개 없는 성충에서 비행 생성 금지.
- `MR-MOV-04` 4/5령 불일치와 미동정 톡토기 먹이를 확정 값으로 승격 금지.
- `MR-MOV-05` 머리 띠·6발·rostrum 마커의 프레임/광원 정합.
- 실행·3D 리그·스프라이트 렌더 시험은 현재 **NOT_RUN**. 근거 미확인값은 `0`이 아니라 `null`/`unverified`.

## 9. 출처·업데이트 규칙
- [M01] [자료](https://www.wanzen-im-ruhrgebiet.de/artenprofile/veliidae/microvelia-reticulata/) — 형태·수면 톡토기 흡즙.
- [M02] [자료](https://www.naturespot.org/species/microvelia-reticulata) — 이동·산란·5령 서술.
- [M03] [자료](https://doi.org/10.1078/S0031-4056(04)70041-4) — 다른 톡토기 방어 반응.
- [M04] [자료](https://www.nibr.go.kr/aiibook/catImage/22/National%20Species%203.pdf) — 한국 분류 목록.
- 프로젝트 공통: `toktogi_movement.md`(31장면 근거 구분), `3Dconv2D.md`, `toktogi_playable_action_animation_spec.md` v2.1.
- **변경 원칙:** 객체 학명·분류수준·먹이 동정·관찰 장면·장소·생애단계·원문 URL을 연결한다. 다른 먹이 종이나 지역의 사육 수치를 `S. aquaticus` 실측치로 전용하지 않는다.
