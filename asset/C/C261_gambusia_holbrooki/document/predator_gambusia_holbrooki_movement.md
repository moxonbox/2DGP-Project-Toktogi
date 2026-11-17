---
object_id: predator_gambusia_holbrooki
scientific_name: Gambusia holbrooki
taxonomic_rank: species
korean_name: null
version: '1.1'
review_date: '2026-11-17'
role_2dgp: subsurface_fish_predator_npc
prey_toktogi_evidence: Sminthurides_genus_found_in_diet_study
---
# *Gambusia holbrooki* (동부모기고기; 번역명) — 2DGP 이동·행동·애니메이션 명세
> 기준: ZIP의 같은 ID 생물 명세 v1.0·`nonspider_predator_objects_index.md` + `toktogi_movement.md`·거미류 Movement 공통 파이프라인·3Dconv2D/플랫포머 설계.
> **역할:** `toktogi`가 플레이어, 본 객체는 NPC/환경 위험 **설계 후보**. `[종 근거]`와 `[게임 설계]`, `[미확인]`을 별도 관리.

## 1. 생물학적 운동 근거·범위
- [분류] 조기어강 **송사리목** 태생어과 종; *G. affinis*와 별개. 한국 국명은 원본에서 비공식 번역으로 취급. [G02][G03]
- [크기] 암컷 최대 약 6cm, 수컷 최대 약 3.5cm는 **표준체장(SL)** 사례; 전장(TL)·평균 크기와 혼동하지 않음. [G03]
- [형태] 위를 향한 입, 방추형 몸, 둥근 꼬리지느러미·등/가슴/배/뒷지느러미; 암컷 임신반점·수컷 gonopodium은 성별 외형. [G02][G03]
- [서식] 얕은 연못·호수·수초 물가의 수중 유영과 표층 먹이 포획. **수면 위 걷기·톡토기형 도약은 금지**; 수면 돌파·공중 체공은 종별 습성으로 검증되지 않은 **게임 연출 옵션**. [G01][G03]
- [식성 연구] 스페인 Banyoles호에서 ***Sminthurides* sp.**가 먹이로 검출; 해당 종은 *S. aquaticus*로 동정되지 않음. [G01]
- [식성 차이] 연안 물벼룩·깔따구 성충 등 다양한 먹이와 성장단계별 식성 변화; 모기 유충만 먹는 전문 포식자로 제한 금지. [G01][G04]
- [생활사/안전] 내부수정 후 새끼를 낳는 태생성 어류(알 덩이 산란 금지), 여러 지역 침입외래종. 한국 출현·자연 수역 방류는 별도 검증/금지. [G02][G04]

## 2. 행동 카탈로그 — AI 상태와 표현 클립 분리
| `action/clip` | 진입 가드 | `pre` 준비 | `mid` 동작·반복 | `end` 종료 |
|---|---|---|---|---|
| `hover_or_school` | 수중 경계/유영 공간 | 꼬리·가슴지느러미 안정 | 제자리 유영·무리 간격 표현 | 경로 지정 |
| `cruise` | 수중 항로 유효 | 몸·꼬리 파동 진입 | 꼬리지느러미 추진·실제 물리 이동 | 유영 속도 감소 |
| `turn` | 목표 방향/장애물 | 몸통 롤·요 진입 | 회전/꼬리 스트로크 조절 | 새 방향 안정 |
| `surface_rise` | 표층 탐색 [설계] | 상승 궤적·수면 높이 확인 | 꼬리 추진을 낮추며 **서서히 상승** | `surface_peek`·`surface_snap` 분기 |
| `surface_peek` | 수면 아래 몸체/입 소켓 유효 [설계] | 몸통 속도 감속 | **입끝만 수면 밖으로 노출**, 몸은 잠긴 상태 유지 | 표층에 위치 고정 |
| `surface_gape` | `surface_peek` 완료 [설계] | 입 벌림 준비 | **뻐끔거림**(입 열기↔닫기 반복), 물결/물방울 선택 | 입 닫고 잠수로 전환 |
| `surface_submerge` | 노출 종료·위협 [설계] | 입 닫기·몸 방향 하향 | **입끝을 수면 아래로 내리고 잠수** | `cruise` 복귀 |
| `surface_snap` | 표층 먹이가 사정거리 안 | 입 개방·가속 준비 | 활성 시간에 1회 입 접촉 검사 | 입 닫기·수중 정렬 |
| `swallow` | 먹이 자원 확인 | 입/인두 정렬 | 삼킴 연출·효과 1회 반영 | 입·턱 복귀 |
| `forage_cruise` | 작은 먹이/먹이군 가능 | 수초 경로 변경 | 짧은 추적·반복 물속 탐색 | 타깃 해제 |
| `evade_or_dive` | 위협/충돌 | 몸 방향 전환 | 급회전·아래쪽 피하기 | 수중 경로 복귀 |
| `breach_launch` | 수면 돌파 허용·수면 상부 공간 확보 [설계] | 수면 쪽 가속/꼬리 추진 | **몸통이 수면 밖으로 튀어오름** | 수중 추진 종료·공중 상태 |
| `airborne_arc` | 몸통이 수면 위로 완전히 이탈 [설계] | 출수 순간 자세 유지 | **상승→순간 공중에 뜸→정점 통과**; 중력에 따른 탄도 운동(정지 비행 아님) | 하강 전환 |
| `surface_fall` | 공중 정점 이후 [설계] | 몸·꼬리 재입수 방향 정렬 | **공중에서 수면으로 낙하** | 수면 충돌 시 `water_reentry` |
| `water_reentry` | 실제 수면 교차·물 부피 존재 [설계] | 물튀김·물결 1회 | **수면을 뚫고 다시 잠김**, 수중 저항 적용 | 자세 안정 후 `cruise` |
| `out_of_water` | **의도된 돌파 시퀀스 밖에서** 수역 이탈 | 유영 추진 비활성 | 중력/실패 판정 [설계] | 실제 수면 재진입 시 조건 복구 |
- [설계] 기본은 **수중 `water_column` NPC**. 예외적으로 승인된 돌파 시퀀스에서만 `airborne`으로 전환하며, 수면 지지·밟기 판정은 없다.
- [설계] 무리 형성은 간격 제어 표현일 뿐 협동 공격·결속 관계는 아님. `surface_gape`는 **호흡 필요성의 증거가 아닌 시각 연출**이며, `surface_snap`과 구분한다.

### 2.1 수면 연속 시퀀스·전이 계약
- **입 노출형:** `cruise → surface_rise → surface_peek → surface_gape(반복 가능) → surface_submerge → cruise`; 위협 시 `surface_submerge`로 취소.
- **돌파형:** `cruise → breach_launch → airborne_arc → surface_fall → water_reentry → cruise`; 물에 닿지 못하면 `out_of_water`로 분기하며 순간이동 복귀 금지.
- **분리 조건:** 입끝의 수면 교차(`mouth_tip`)와 몸 중심의 수면 이탈(`body_ref`)을 별도 검출. `surface_peek`은 입끝만 밖에 두고, 돌파형만 몸 전체가 공중 진입 가능.
- **상태 소유권:** `water_column/surface_boundary/airborne` 판정·추진→중력→수중저항 전환은 물리 담당, 꼬리·입 포즈와 물튀김/파문은 애니메이션·VFX 담당. 속도·체공시간·최대 높이는 `null`인 **게임 튜닝값**.

## 3. AI·물리·전투 이벤트 소유권
- **AI·물리·리그 분리:** `physics_root`와 수면/공중 교차는 시뮬레이션이 소유하고, 클립은 시각 자세만 담당한다. `breach_launch` 출수 시 추진을 종료하고 `airborne_arc/surface_fall`은 초기 속도·중력에 따른 물리 이동으로 처리한다.
- 센서 `target_visible`, `surface_vibration`, `range_ok`, `support_valid`, `hazard`, `water_surface_height`, `body_submerged`, `mouth_tip_exposed`, `airspace_clear`는 [설계] 입력. 반경·확률·임계치는 `null`.
- `attack_instance_id`·`target_id`·`active_interval`·`effect_committed`를 분리하고, 동일 공격에 같은 피격 대상의 효과는 명시된 횟수 이하로 제한한다.
- 사건 경계의 입력→물리 접촉→공격 활성→결과 확정 순서를 동일 틱에서 일관되게 적용한다. UI/일시정지·저장복원 시 과거 마커 재생은 무효다.
- 마커는 **효과 후보**이며 실제 타격은 현재 거리·접촉·활성구간으로 결정한다. `surface_gape`는 기본적으로 **비공격/무피해**. `breach_launch` 역시 별도 공격 규칙 없이는 피해 없음.
- `toktogi`는 플레이어 Capsule/체력·넉백 판정을 소유; 적의 시각 클립만으로 낙하·피격·잡힘·게임오버를 강제하지 않는다.
- 전투 접촉은 단발 상호작용으로 종료·정리한다. 지속 파트너·구애·결속·공동 도약·공유 입력 관계 시스템을 생성하지 않는다.

## 4. `pre–mid–end`, 가중치·취소 처리
- 단계 `pre`=목표·수면 정렬 / `mid`=루프·행동 / `end`=자세 회수. 뻐끔거림은 `surface_gape.mid` 루프, 공중은 1회 시퀀스; 시간·각도·높이는 **[설계]**.
- 상태·단계 변경마다 `state_generation`·`phase_instance_id`·`cycle_id`를 관리하고 오래된 `phase_done`, `attack`, `feed` 마커는 폐기한다.
- 행동 `pre/mid/end`는 시간 진행 순서, `speed_weight`·`turn_weight`·`hit_weight`는 **호환 포즈 변형** 선택/혼합; 가중치만으로 판정·공격 권한을 생성하지 않는다.
- `outgoing_blend`는 기존 포즈 스냅샷만 섞고 공격/섭식 이벤트는 **재실행하지 않는다**. 행동 취소는 end 클립 완료를 기다리지 않는다.
- 지느러미·입 소켓·수면 교차 및 공격 마커는 같은 시점에서 정합; 표층 뻐끔거림을 자동 섭식으로 해석하지 않으며, 공격은 별도 `surface_snap`의 유효 구간만 사용한다.
- 3D 포즈 혼합은 가능하지만 출력된 **2D PNG 두 장을 알파 중첩하는 방식은 관절 보간이 아니다**. 부족한 전이 자세는 3D에서 추가 표본 출력한다.

## 5. 3D 리깅·표면 접촉 채널
| 리그 채널 | 동작 역할 | 필수 검수 |
|---|---|---|
| `physics_root,fish_body,head` | 수중 경로·몸 굴곡 분리 | 몸 반응/화면 피벗 독립 |
| `tail_peduncle,caudal_fin` | 꼬리 추진 파동 | 유영 속도와 클립 위상 맞춤 |
| `dorsal,pectoral,pelvic,anal_fins` | 회전·균형 지느러미 | 물고기에 여섯 다리 적용 금지 |
| `jaw_upper/lower,mouth_tip` | 위향 입·반복 개폐·표층 포획 | `surface_peek/gape`에서 입끝 수면 교차·입 개폐 가독성 |
| `eye_L/R,sex_variant_optional` | 시선·성별 외형 | gonopodium은 수컷만 |
- [설계] `waterline_intersection`(수면 위치·마스크), `body_ref`(몸 중심), `splash_emitter`(출수/입수 파문)는 리그 외 시뮬레이션·VFX 앵커로 분리. 성별 외형은 생물 특징일 뿐 공격 조건 아님.

## 6. 3D → 픽셀풍 2D 스프라이트 파이프라인
- **공통 파이프라인:** `원본 3D 모델+리그 → Action별 pre/mid/end → 고정 시점·포즈 샘플 → Base/Alpha/Normal/AO/ORM 출력 → 크롭/피벗/소켓 → Atlas/Manifest → 2D 재생`.
- 메타데이터: `asset_id, revision, action, phase, variant, sample_time, display_duration, view, pivot, bbox, attack_socket, mouth_tip, body_ref, waterline_state, splash_marker`를 프레임별 보존.
- Base Color/Emissive 등 색 채널은 선언된 색공간으로, **Normal/ORM/Depth/coverage는 수치 데이터로** 디코딩한다. 픽셀풍 정수배 확대·경계/알파 검증.
- 실제 조명에 대한 Normal·Roughness/Metallic 반응을 시험하며 일부 정적 배경 베이크만 허용한다. 완성 조명 RGBA를 Albedo로 재조명하지 않는다.
- `DEC-06`의 방향 수·Normal 공간·Depth·앵커/좌표계는 **보류**. 한 시점 교정만으로 다방향 양산을 통과 처리하지 않는다.
- 3D 본 블렌드는 제작 시 해결하고 2D는 클립·방향·전이 선택. **수면 위/아래 가림, 수중 색감, 출수·재입수 파문**을 프레임 마커에 맞추고 시킹·복원 시 VFX 중복 금지.

## 7. 실행 데이터 예시(수치는 미결정)
```yaml
npc_id: predator_gambusia_holbrooki
allowed_habitat: [shallow_water,vegetated_margin,water_column,surface_boundary]
locomotion: tail_fin_swimming
locomotion_modes: [water_column, surface_boundary, airborne_optional]
surface_sequences: [peek_gape_submerge, breach_arc_fall_reentry]
breach_enabled: false # [설계] 별도 활성화 필요
surface_gape_is_attack: false
body_submerged: null
mouth_tip_exposed: null
airspace_clear: null
water_surface_height: null
breach_launch_speed_u_s: null
airtime_s: null
surface_gape_cycle_s: null
prey_evidence: Sminthurides_sp_diet_study_species_unidentified
phase: pre
target_id: null
water_volume_id: null
attack_instance_id: null
damage: null
predation_probability: null
adult_max_SL_cm_examples: {female: 6.0, male: 3.5}
aquatic_habitat: true
terrestrial_locomotion: false
diet_sminthurides_genus: gut_study_record
diet_sminthurides_aquaticus: unverified
occurrence_south_korea: needs_verification
swim_speed_u_s: null
asset_contract: DEC-06_deferred
```

## 8. 수락 시험 / 연구 검증 구분
- `GH-MOV-01` 물고기의 지느러미 추진과 실제 수중 이동·회전 일치.
- `GH-MOV-02` 표층 접근/입 접촉/삼킴은 각기 다른 사건, 중복 효과 없음.
- `GH-MOV-03` 수면 위 걷기·furca 도약·범위 밖 추적 없음. 승인된 `airborne`만 예외 허용.
- `GH-MOV-04` 성별 SL 치수 구별, *G. affinis*와 포식 연구 오인 방지.
- `GH-MOV-05` 수면 경계/물속 배경의 조명·입 소켓·재질 맵 정합.
- `GH-MOV-06` 서서히 상승→입끝만 노출→뻐끔거림 반복→잠수: 몸체 수중 유지, 입 소켓·가림·파문 정합, **피격/섭식 이벤트 없음**.
- `GH-MOV-07` 수면 돌파→상승→정점→낙하→재입수: 상태·중력 전환, 입수 시 파문/물방울 **각 1회**, 실제 물 부피 확인.
- `GH-MOV-08` 취소·물 미도달·일시정지·재생 위치 이동·저장복원 시 클립/효과 중복 및 공중 정지·텔레포트 없음.
- 실행·3D 리그·스프라이트 렌더 시험은 현재 **NOT_RUN**. 근거 미확인값은 `0`이 아니라 `null`/`unverified`.

## 9. 출처·업데이트 규칙
- [G01] [자료](https://doi.org/10.1006/jfbi.1999.0983) — *Sminthurides* sp. 식성 검출.
- [G02] [자료](https://www.mdb.fish/fish-fact-sheets/eastern-gambusia) — 생활사·형태.
- [G03] [자료](https://fishesofaustralia.net.au/home/species/3636) — SL·성별·생식.
- [G04] [자료](https://www.iucngisd.org/gisd/speciesname/Gambusia%2Bholbrooki) — 침입외래종 경계.
- 프로젝트 공통: `toktogi_movement.md`(31장면 근거 구분), `3Dconv2D.md`, `toktogi_playable_action_animation_spec.md` v2.1.
- **v1.1 추가:** `surface_peek/gape/submerge`와 `breach_launch/airborne_arc/surface_fall/water_reentry`는 **게임 표현 요구사항**; *G. holbrooki*의 공중 도약 빈도·입 노출 호흡 습성의 실증 근거로 사용 금지. 먹이 자료의 *Sminthurides* sp.를 *S. aquaticus*로 승격하지 않는다.
