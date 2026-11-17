---
object_id: spider_triaeris_stenaspis
scientific_name: Triaeris stenaspis
taxonomic_rank: species
family: Oonopidae
korean_name: null
version: '1.0'
review_date: '2026-11-17'
role_2dgp: ai_close_range_predator_candidate
prey_toktogi_status: unverified_species_level_predation
---
# *Triaeris stenaspis* — 2DGP 이동·행동·애니메이션 명세
> 기준: `spider_triaeris_stenaspis(1).md` v1.2, `toktogi_movement.md`, 플레이어/리그 상태 명세, `3Dconv2D.md`, 2DGP 기획서. **toktogi는 조작 캐릭터**, 본 거미는 적 후보 AI.
> 표기: **[종 실험]** 해당 종 직접 실험 / **[종 표본]** 동정·외형 / **[설계]** 게임 내 동작·효과 / **[미확인]** 근거 부재.

## 1. 이동·사냥에 관한 확인 사실
- [종 실험] 2014년 먹이 선택·공격 실험에서 **포획그물 없는 배회·직접 포획형**: `접근 → 앞다리로 붙잡아 유지(grasp and hold) → 물기 → 저항 시 추가 물기 → 섭식`. [T03]
- [종 실험] 제시된 10가지 먹이 유형 중 **톡토기류를 주로 포획**했고 흰개미·귀뚜라미는 드물게 포획; 나머지 먹이는 그 시험에서 포획되지 않았다는 뜻으로만 해석한다. [T03]
- [종 실험] 큰 톡토기에 **3회를 넘는 반복 물기**, 도약하는 먹이에 매달리는 사례가 관찰됨. 특정 *S. aquaticus* 대상의 포획·회피 성공률은 **미확인**. [T03]
- [종 표본] 성체 암컷 몸길이는 출처 표본별 **1.47 / 1.7 / 약 1.8mm** 사례. 범위·평균으로 통합하지 않는다. 수컷 성체 표본 미보고는 생물학적 불가능의 증거가 아님. [T02][T08][T10]
- [종 표본] **눈 6개**, 머리가슴 황적~주황빛, 배는 짙은 적갈색 경화판; 다리 8개, 앞 제1·2다리 가시·경화판 형질은 정밀 표본 참조. [T02][T07]
- [근거] 습한 온실·낙엽층·표토·돌 밑·화분의 틈 등에서 기록; **한국 자연 연못 서식·수면 추격/보행은 확인되지 않음**. [T01][T07][T08]
- [설계] 톡토기와 조우·공격은 가상 플랫포머의 선택적 적 상호작용. 자연 생태의 확정 포식 관계나 한국 연못의 토착 생물로 표시 금지.

## 2. AI 이동·행동 `pre / mid / end` 카탈로그
| 상태/애니메이션 | 진입 조건 [설계] | `pre` | `mid` 핵심·반복 | `end` |
|---|---|---|---|---|
| `idle_shelter` | 표적 없음·틈 안전 | 안정 지지·몸 낮춤 | 더듬이 대신 앞다리·촉지 미세 움직임 | 다음 목표 쪽 정렬 |
| `roam` | 경로·접촉 유효 | 첫 발 이동 | 저층 배회·지지 다리 교대 | 제동·발 정리 |
| `inspect_target` | 근거리 단서 발생 | 머리·앞다리 방향 선정 | 정지/짧은 접근·확인 | 추적/회피 결정 |
| `approach` | 표적 유효·경로 확보 | 발판 및 장애물 검사 | 짧은 추적 접근 | 사정거리 진입 또는 중단 |
| `grasp` | 현재 표적 접촉 가능 | 앞다리 벌림·턱 준비 | 붙잡기 시도·접촉 사건 확인 | 성공 시 `bite_hold`, 실패 시 해제 |
| `bite_hold` | 같은 공격의 붙잡기 성공 | 입·위턱 접촉 정렬 | 반복 물기(`bite_cycle`)·유효성 재검사 | 먹이 유지/방출 분기 |
| `feed` | 음식/포획 결과 유효 | 먹이 쪽 머리 정렬 | 구기 반복·대상 소모 확인 | 턱·앞다리 정리 |
| `release_escape` | 표적 이탈·거부·피격 | 잡기 제한 해제 | 후퇴·도주 또는 낙하 | 지지 회복·대기 |
| `recover` | 공격 종료·지지 재획득 | 현재 자세 안정화 | 잠깐 회복, 물리 운동 계속 | `idle_shelter`/`roam` |
- **실제 수면 점프 기술 없음:** 물 위로 이동하거나 능동 도약하는 NPC 클립은 현재 범위 밖. 먹이가 점프할 때 매달린 사례는 **먹이의 운동에 따른 수동 동반**이지 거미 자신의 도약기관 능력이 아니다.
- 포획그물 `build_web`, 실낙하 `balloon`은 원본 종의 기본 행동으로 지정하지 않는다. `spider_linyphiidae`의 그물 상태를 복사하지 않는다.

## 3. 물기·탈출 상호작용의 정확한 경계
- [설계] `target_id`는 **현재 공격 시도의 대상 식별자**일 뿐 파트너·지속 관계가 아니다. `grasp_action_id` 수명은 `grasp→bite_hold→release` 한 시도로 제한.
- `grasp` 성공에는 현재 범위·충돌·피격 가능 조건이 필요; 영상의 겹침이나 스프라이트 소켓 위치만으로 성공을 확정하지 않는다.
- 물기 반복은 `bite_cycle_id`별 `active_interval`을 만들고 대상/공격 이력을 함께 검사; 공격 프로필에서 여러 번 명중을 허용한 경우에만 추가 피해.
- `bite_hold` 도중 대상 소멸·점프 회피·충돌 분리·피격·새 장면 로딩이면 즉시 붙잡기 취소 및 `release_escape`.
- 붙잡기 연출에서 toktogi의 Capsule·실제 이동 권한·furca 점프를 거미의 애니메이션이 임의로 빼앗지 않는다; 이동 제한을 채택할 경우 **별도 게임 규칙**이 필요.
- 먹이가 점프하면서 잠시 거미가 끌려가는 장면은 단발 **시각적 또는 명시적 물리 접촉**만 허용; 결속/운반/공동 추진 등 이전에 제거한 지속 관계 기전은 도입 금지.
- 감지·접근·bite 판정은 시뮬레이션이 소유, 실제 피해는 플레이어 전투 처리에서 확정; 스프라이트 `bite` 마커는 시간 동기화 참고용.
- 다중 충돌체·동일 프레임 반복·시킹·일시정지·저장 복원 후 같은 `bite_cycle_id`의 중복 물기 확정 금지.

## 4. 3D 리그·형태와 지지 기관
| 리그/마커 | 동작 목적 | 제작·동정 검수 |
|---|---|---|
| `physics_root / visual_root` | 월드 이동·충돌 / 렌더 피벗 | 충돌형상과 아틀라스 원점 분리 |
| `cephalothorax / abdomen_scutum` | 머리가슴 정렬·복부 기울기 | 작은 둥근 배·짙은 경화판 구분 |
| `leg_L1..L4 / leg_R1..R4` | 8개 다리, 앞다리의 붙잡기와 나머지 지지 | 실제 지지하는 발만 접지 IK |
| `chelicerae_L/R`, `fang`, `bite_socket` | 물기·반복 물기 포즈 | 타격 검사 시 입 위치 정합 |
| `pedipalp_L/R` | 감지·구기 주변 포즈 | 더듬이로 잘못 제작하지 않음 |
| `eye_cluster_6` | 눈 6개의 실루엣·위치 | 다른 거미의 8안 배열 복제 금지 |
| `spine_detail_I_II` | 앞다리 경절·무릎마디 가시 | 원본 종 카드/현미경 관찰로 검증 |
- [종 표본] 앞 제1·2다리의 **경절 가시 5쌍·무릎마디 3쌍**, 발허리마디의 가시 부재 기재는 미세형태 기준이며 저해상도에서 모두 보일 필요는 없다. [T02]
- `grasp` 중의 앞다리 IK와 `bite_socket` 위치를 검증하되 포즈가 월드 충돌체를 당겨 실제 캐릭터를 이동시키지 않는다.

## 5. 3D → 2D 픽셀 애니메이션 계약
- `실측 형태 검토 → rig/action(타깃/몸/앞다리) → pre/mid/end·bite 루프 표본 → 동일 카메라 화면 패스 → atlas/manifest → 2D clip 선택`.
- 매 표본 기록: `asset_id, revision, clip, phase, phase_u, bite_cycle_id, sample_time, view, pivot, foot_marker, bite_socket, bbox`.
- Base Color·Alpha·Normal·AO·Metallic/Roughness는 같은 실루엣·시각·크롭·좌표에서 추출; 작은 눈·가시·턱은 확대 배율별 가독성을 따로 검사.
- 수치 맵에는 팔레트/감마/디더링을 색 이미지와 동일하게 강제하지 않음. 선언된 실제 조명 경로로 Normal과 R/M의 변화 확인.
- 3D에선 앞다리 `grasp_weight`·턱 `bite_weight`를 채널별 혼합 가능하나, **2D는 사전 출력된 변형 클립·프레임·전이 클립 선택**이 기본.
- `pre/mid/end`는 시간 단계; 가중치는 속도·접촉 강도·표현 변형에만 적용하고 **물기 피해나 붙잡기 성공을 가중치로 산정하지 않음**.
- 방향/view·Normal 좌표·Depth·피벗·마커의 최종 변환은 `DEC-06` 보류. 단일 시점 시험과 최종 다방향 생산을 분리한다.

## 6. 최소 실행 데이터(설계안)
```yaml
npc_id: spider_triaeris_stenaspis
rank: species
hunting_mode: grasp_and_hold
capture_web: false
ai_state: roam
phase: mid
grasp_action_id: null
bite_cycle_id: null
target_id: null
attack_instance_id: null
attack_range_u: null
bite_damage: null
water_surface_pursuit: unverified
asset_contract: DEC-06-deferred
```

## 7. 생활사·검증 및 주요 근거
- [종 실험] 암컷 단위생식, 납작한 난낭 **한 개당 알 2개**, 개체 생애 평균 **총 27알**, fertility 약 **59%**, 유체 **3령**, 성체 기간 평균 **약 6개월**은 **2009년 사육 실험조건**. 게임에서 번식/가족 AI를 기본 생성하지 않는다. [T04]
- `T-MOV-01` 가까운 표적에 `접근→붙잡기→물기 반복→해제`가 이어지고, 앞다리·턱·지지 발이 일치.
- `T-MOV-02` 큰 표적에 반복 물기 클립을 사용할 때 **공격 프로필에서 허용한 횟수만 피해**가 적용되며 3회 초과 관찰을 무조건 피해 4회로 오해하지 않음.
- `T-MOV-03` 도약하는 toktogi에게 순간 접촉·이탈이 있어도 NPC의 독립 점프, 지속 결속 또는 조작 불능이 자동 생성되지 않음.
- `T-MOV-04` 성체 암컷·눈 6개·앞다리 가시·경화판, 저해상도 눈/턱 가독성과 Normal/ORM 정합 검사.
- `T-MOV-05` 대상 실종·저장/복원·전이 취소·다중 접촉체에서 이전 `grasp_action_id`/`bite_cycle_id` 효과 재발생 없음.
- `T-MOV-06` 자연 연못 출현·*S. aquaticus* 직접 포식·먹이 선택률을 실험 근거 없이 확정하지 않음.
- 출처: [T01](https://wsc.nmbe.ch/spec-data/30859), [T02](https://araneae.nmbe.ch/data/1327/Triaeris_stenaspis), [T03](https://doi.org/10.1636/Hi12-90.1), [T04](https://doi.org/10.14411/eje.2009.028).
- **미결정:** 실제 레벨 출현 여부, 도달거리·탐지·피해·탈출 정책·크기 배율, 좌표(DEC-06). 모든 실게임 검증 상태는 `NOT_RUN`.
