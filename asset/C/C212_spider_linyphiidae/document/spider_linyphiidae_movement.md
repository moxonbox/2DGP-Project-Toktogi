---
object_id: spider_linyphiidae
scientific_name: Linyphiidae
taxonomic_rank: family
korean_name: 접시거미과
version: '1.0'
review_date: '2026-11-17'
role_2dgp: ai_predator_web_hazard
prey_toktogi_status: unverified_species_level_predation
---
# 접시거미과(Linyphiidae) — 2DGP 이동·행동·애니메이션 명세
> 기준: `spider_linyphiidae(1).md` v1.2, `toktogi_movement.md`, 플레이어 상태·리깅 명세, `3Dconv2D.md`, 2DGP 기획서. **toktogi가 플레이어**, 본 객체는 AI·환경 위험 후보.
> 근거 표기: **[과 일반]**, **[속/종 사례]**, **[설계]**(게임 연출·판정), **[미확인]**을 엄격히 구별한다.

## 1. 생물학적 운동·그물 근거
- [과 일반] 접시거미과는 **여러 속·기능형의 집합**. 기본형은 수평 시트그물 위의 방해실과 시트 **아래쪽**에서 대기하는 거미이며, 저층 그물·높은 돔/시트·그물 감소형이 공존한다. [L01][L03]
- [설계] 생성 전에 `functional_variant = low_sheet_roamer | elevated_sheet | reduced_web` 중 선택; **모든 개체에 같은 포획그물을 강제하지 않는다**.
- [과 일반] 몸길이 교육용 참조 약 **1.5–8mm**는 과의 절대 최소·최대·평균 아님. *Erigone atra* 성체 수컷 1.9–2.5mm·암컷 1.8–2.8mm는 **종 사례**. [L02][L11]
- [속/종 사례] *Bathyphantes gracilis* 1.5–2.5mm 범위의 성별 구분 사례; *Linyphia triangularis* 수컷 4.6–7.0mm·암컷 5–8mm. 서로 다른 종 값을 하나의 모델로 평균내지 않는다. [L12][L14]
- [과 일반] 그물 진동·촉각/화학 단서를 이용해 반응하고 짧게 접근·물기·섭식·수리를 한다. **접촉만으로 반드시 자동포획되는 접착면은 아님**. [L02][L03]
- [종/연구] 보리밭 **147개 그물** 연구의 위치·크기와 식단 관계는 조건부 사례; 2022년 DNA 연구 **300개체 처리/244개체 유효·먹이 89분류군은 5속 합계**. [L03]
- [미확인] 대상 물알둥근톡토기(*S. aquaticus*) 직접 포식, 같은 연못 상주, 과 전체 일정 그물 크기·탐지거리·포식률·수면 위 사냥.
- [근거 구분] 연구의 톡토기과 **Bourletiellidae** 검출을 대상 **Sminthurididae**의 검출로 바꾸지 않는다; 54.9%는 Linyphiidae+Hahniidae 혼합 표본값. [L03][L07]

## 2. AI 행동·`pre / mid / end` 클립 카탈로그
| AI 상태/클립 | 진입 조건 [설계] | `pre` | `mid`(루프·사건) | `end` |
|---|---|---|---|---|
| `choose_site` | 새 자리·그물 없음 | 지형/부착점 확인 | 위치·높이 선택 | 목표 지점 잠금 |
| `build_sheet` | 그물형·앵커 유효 | 실젖·다리 준비 | 앵커 사이 실 배치 반복 | 유효한 환경 `web` 확정 |
| `wait_under` | 그물 배치·지지 가능 | 시트 아래로 정렬 | 다리 지지·실 진동 감시 | 진동/교란에 반응 |
| `detect_vibration` | `web_event` 수신 | 이벤트 출처/진위 평가 | 감지 방향으로 몸·앞다리 회전 | 접근 또는 대기 복귀 |
| `web_rush` | 먹이 위치·실 경로 유효 | 경로 충돌 검사 | 짧은 실 위/아래 접근 | 공격 가능 거리 정렬 |
| `bite` | 현재 목표·도달 유효 | 위턱/촉지 정렬 | 명시한 active 구간 물기 | 물기 해제·복귀 |
| `feed` | 먹이 자원·접촉 유효 | 머리·입 정렬 | 구기 반복·자원 재검사 | 입 정리 |
| `repair_web` | 실 파손·기준점 유효 | 파손 부위 확인 | 실젖·다리로 실 교체 표현 | `web` 데이터 갱신 |
| `relocate` | 먹이 부족·그물 무효 | 위치 선택 | 보행·기존 그물 이탈 | 새 자리/대기 |
| `evade_drop` | 교란·피격·탈출 경로 | 발·실 해제 준비 | 도망 또는 실을 타고 낙하 | 지지 재확인 |
- `reduced_web`는 `build_sheet`/`repair_web`를 비활성화하거나 대체하고 `roam/search`를 사용; **기능형별 전이 그래프가 달라야 한다**.
- [과 일반] 작은 개체의 `ballooning`은 실과 바람에 의한 **수동적 공중분산**; 모든 성체의 입력형 점프·비행·추격 능력으로 만들지 않는다. [L06]
- [연구 한계] 풍속 약 4m/s 이상에서 분산 감소, 5.5m/s 이상 거의 미관찰은 **특정 조사 환경**의 값; 게임 바람 임계치로 자동 복사 금지. [L06]

## 3. 환경 `web`와 NPC의 책임 분리
- `spider_actor`는 AI, 공격, 실젖 애니메이션을 관리; `web_actor`는 앵커·실 위치·시트·센서·파손/수리를 관리. **사회적·짝 관계나 파트너 시스템은 없음**.
- `web_actor`의 센서 `web_contact`, `vibration`, `thread_break`는 월드 사건; 실제 포획/이동 제한은 별도 **[설계] 물리 프로필**의 승인 조건으로 처리.
- toktogi가 실에 닿으면 `contact→vibration→거미 반응→접근→active bite`를 구분; 겹침만으로 자동 기절·포획·피해 확정 금지.
- 실 충돌 범위와 보여지는 선은 구분하며, 탄성 잎·수면 접촉·플레이어 Capsule과의 판정 우선순위는 현재 게임 물리 계약을 따른다.
- 이동·낙하는 월드 물리가 소유; 실을 따라 떨어지는 표현은 지지·실 상태로 결정되고 sprite loop가 중력·위치를 직접 변경하지 않는다.
- `attack_instance_id`와 `target_id`/소비 이력으로 단발 명중; `bite` 반복 루프와 **반복 피해는 별도 공격 정책**이 없으면 연결하지 않는다.
- 파손된 그물·사라진 대상·변경된 장면에서 이전 `web_event_id`와 애니메이션 콜백을 무효화; 저장/복원 때 환경 실과 NPC 순서를 함께 복원한다.

## 4. 리그·실 움직임 기준
| 본/제어 채널 | 동작 | 한계·검수 |
|---|---|---|
| `physics_root / visual_root` | 충돌·이동 / 시각 오프셋 | 실 지지 소유권·피벗 분리 |
| `cephalothorax / abdomen` | 몸 방향·매달림·실젖 위치 | 시트 아래 포즈와 몸통 뒤집힘 구분 |
| `leg_L1..L4 / leg_R1..R4` | 8다리 보행·실 잡기·수리 | 실 접촉 발/지지 발만 IK |
| `pedipalp_L/R`, `chelicerae_L/R` | 진동 탐색·물기 | 실제 타격/입 마커 정합 |
| `spinneret`, `silk_emit`, `web_anchor` | 실 방출·고정·수리 | 실은 별도 `web_actor`가 생성 |
| `eye_cluster_variant` | 시야 표현 | 8안 흔하나 **예외**, 종 확정 전 눈 배열 고정 금지 |
- 리그는 선택한 실제 종의 형태를 우선하며, 시트·돔·저층의 실 배치 데이터는 스프라이트의 장식 그림과 별도다.
- 그물의 진동은 `web_event`에 따른 변형/펄스 레이어로 표현할 수 있지만 실제 탐지 성공은 센서/AI 규칙이 소유한다.

## 5. 3D → 2D 스프라이트·재질 출력
- `선택 종/기능형 확정 → 리그/그물 제작 → clip(pre/mid/end) 평가 → 방향·시점별 멀티패스 → atlas/manifest → 게임 재생`.
- `character`의 색·Alpha·Normal·AO·Roughness/Metallic은 동일 포즈·크롭·피벗 사용; `web`은 독립 레이어·가림·충돌 정보를 별도로 출력.
- `clip, variant, phase_u, loop_id, sample_time, view, pivot, foot_marker, mouth_socket, web_anchor, material_rev`를 표본마다 유지.
- 3D 단계에서는 다리·복부·실젖 가중치 혼합 가능; 2D 단계는 단계·프레임·별도 전이 클립 선택, **PNG 알파 합성은 골격 보간이 아님**.
- 가느다란 실·발끝은 최종 픽셀 배율에서 가독성/계단 깜빡임 시험; 실의 표시와 감지/충돌 판정을 동일 개념으로 묶지 않는다.
- 실제 재질 반응을 캐릭터/필요한 환경에 적용; 색상과 Normal/ORM 데이터 해석 분리. `DEC-06` 좌표·Normal/Depth·view/앵커는 **최종 결정 전**.

## 6. 최소 데이터 예시(미확정값은 `null`)
```yaml
npc_id: spider_linyphiidae
rank: family
functional_variant: null # 종/속 선정 후 필수 선택
ai_state: choose_site
phase: pre
web_id: null
web_status: absent
web_event_id: null
attack_instance_id: null
web_height_mm: null
web_area_mm2: null
sensing_range_u: null
damage: null
diet_s_aquaticus: unverified
asset_contract: DEC-06-deferred
```

## 7. 검증 기준·참고
- `L-MOV-01` 기능형별 `build_sheet / wait_under / roam` 전이가 맞고 과 전체 동일 그물 강제가 없음.
- `L-MOV-02` 시트 **아래쪽** 대기·진동→반응→접근을 움직이는 화면에서 확인, 그물 접촉만으로 피해 없음.
- `L-MOV-03` 실 파손·수리·세계 재시작·저장 복원에서 실/AI 상태와 이벤트 소비가 일관됨.
- `L-MOV-04` 다리 8개와 실젖 위치·지지/가림/발끝 정합 및 실제 2D 조명 반응 확인.
- `L-MOV-05` 30/60/120 렌더 FPS·시킹·클립 취소에서 공격/센서 이벤트 중복 없음.
- `L-MOV-06` 먹이 DNA의 Bourletiellidae, 54.9% 혼합 표본, 종 미확인 정보를 toktogi 포식률로 오용하지 않음.
- 출처: [L01](https://wsc.nmbe.ch/families), [L02](https://www.biokids.umich.edu/critters/Linyphiidae/), [L03](https://doi.org/10.1002/edn3.272), [L06](https://pubmed.ncbi.nlm.nih.gov/27527898/), [L11](https://araneae.nmbe.ch/data/234/Erigone_atra).
- **미결정:** 구현 대상 실제 종, 기능형, 그물 크기·앵커·물리/접촉 효과, AI 감지/피해값, 시점·좌표(DEC-06). 검증 상태 `NOT_RUN`.
