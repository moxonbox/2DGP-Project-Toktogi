---
object_id: predator_gambusia_holbrooki
asset_id: C261_gambusia_holbrooki
model_spec_id: predator_gambusia_holbrooki_model
scientific_name: Gambusia holbrooki
taxonomic_rank: species
version: '1.1'
date: '2026-11-17'
scope: external_morphology_3d_and_animation_support
parent_spec: predator_gambusia_holbrooki.md
movement_spec: predator_gambusia_holbrooki_movement.md@1.1
---
# *Gambusia holbrooki* — 3D 모델·리깅 명세서 v1.1

> **기준:** 업로드된 모델 명세 v1.0과 Movement v1.1. **[생물]** 실물 형태·성차 / **[설계]** 게임 동작과 렌더 요구사항 / **[미확인]** 근거·수치 부족.
> **적용 경계:** `surface_peek/gape/submerge`와 `breach_launch/airborne_arc/surface_fall/water_reentry`는 **[설계] 연출**이다. 이 종의 공중 도약 습성·공기 호흡 행동이 검증됐다는 의미가 아니다.

## 1. 전체 형태·측정 기준
| 요소 | 모델링 기준 |
|---|---|
| 체형 | [생물] 약간 측편된 방추형 몸, 등쪽이 다소 납작한 머리, 위로 향한 작은 입, 둥근 꼬리지느러미. 다리·더듬이·날개 없음. |
| 지느러미 | 등 1개, 가슴 1쌍, 배 1쌍, 뒷지느러미 1개, 꼬리 1개. 부드러운 지느러미막·광조 구조는 종 사진으로 보정. |
| 몸길이 | 성체 암컷 **최대 약 60mm SL**, 수컷 **최대 약 35mm SL**이라는 문헌 사례 [G1]; 평균이나 전장(TL)이 아님. |
| 측정점 | **SL** = 주둥이 앞끝~미부 척추 끝(꼬리지느러미 시작 부근), **TL** = 주둥이~꼬리지느러미 끝. 두 값을 서로 변환하는 상수 없음. |
| 톡토기 기준 | `AssetSize.md`의 *S. aquaticus* 암컷 최대 1mm 대비 SL의 숫자상 상한은 암컷 약 60×, 수컷 약 35×. 제작 BU·픽셀 배율은 별개. |
| 유어/성차 | 태생 출생 후 작은 물고기 형태; 유어는 성체 균일 축소 금지. 수컷은 가늘고 뒷지느러미가 생식기(gonopodium)로 변형, 암컷은 배가 깊고 성숙 시 임신반점 가능. |

## 2. 부위별 필수 메시
| 메시/기관 | 외형·움직임 준비 사항 |
|---|---|
| `body`·`head` | 머리~꼬리자루를 연속 표면으로 만들되, 몸통 굽힘을 위한 변형 루프 확보. 공중 포즈에서 과도한 몸체 압축 금지. |
| `jaw_upper`, `jaw_lower` | 위향 입 틈을 실제로 열고 닫을 수 있도록 분리·가중치 설정. 반복 개폐에도 표면 관통, 머리 찢어짐, 턱 뒤집힘 없어야 함. |
| `eyes_L/R` | 어류 눈 1쌍과 눈 주변 얼굴 형태; 공중·수면 장면에서 위쪽으로 향한 입과 구별되게 구현. |
| `operculum_L/R` | 아가미덮개와 틈. 선택적 작은 개폐 가능하나 `surface_gape`를 호흡 실측 행위로 연결하지 않음. |
| `caudal_peduncle`, `caudal_fin` | 꼬리자루의 연속 굴곡 및 꼬리지느러미 좌우 추진; 출수 뒤에는 **물속 추진력 비활성**이지만 꼬리 시각 포즈는 가능. |
| `dorsal_fin`, `pectoral_L/R`, `pelvic_L/R`, `anal_fin` | 지느러미를 독립 제어. 상승·정지·방향전환·입수 시 서로 다른 편향 포즈 지원. |
| `sex_variant` | 수컷 `gonopodium`/암컷 복부 볼륨·임신반점 분리; 두 변형의 SL과 피벗을 각각 검수. |
| `skin` | 올리브~갈색 등, 회은빛 옆, 밝은 배, 반투명 지느러미·점무늬. 비늘은 텍스처/노멀 우선; 정확한 PBR 수치 미정. |

## 3. 리그·앵커 계약
| 노드/소켓 | 소유권과 사용 목적 |
|---|---|
| `physics_root` | [설계] 실제 위치·속도·중력·수중저항·수면 교차는 시뮬레이션 소유. 애니메이션이 위치를 순간 이동시키지 않음. |
| `visual_root`, `fish_body`, `head` | 리그 내부 자세만 담당. 수중/공중 포즈 간 원활히 혼합. |
| `spine_01..N`, `tail_peduncle`, `caudal_fin` | 수중 꼬리 파동, 출수 직전 가속 포즈, 공중 관성 포즈, 입수 뒤 안정화. `N`은 제작 시 결정. |
| `jaw_upper/lower_ctrl` | `surface_gape`의 반복 개폐; `surface_snap`의 공격 개폐와 클립·마커를 구별. |
| `mouth_tip` | **애니메이션으로 이동하는 실제 입끝** 앵커. `surface_peek`의 입 노출 검사용이며 공격은 별도 소켓·활성 판정. |
| `body_ref` | 몸통 기준점. `mouth_tip_exposed`와 별도로 수면 위/아래 및 전체 출수 여부 판정. |
| `waterline_intersection` | **고정 본 아님**. 현재 수면 메시/높이와 변형된 몸 메시의 교차로 매 프레임 계산하는 마스크·접촉 데이터. |
| `splash_emitter`, `ripple_origin` | **수면과 실제 교차한 지점**에 VFX 배치하는 이벤트 위치; 출수/재입수 파문·물방울 중복 발생 금지. |
| `attack_socket` | `surface_snap`의 유효 공격에만 사용. `surface_gape`·`breach_launch`는 별도 승인 없으면 비공격·무피해. |

## 4. 이동 상태별 필수 포즈/변형 ([설계])
| Movement 상태 | 3D 모델·리그 표현 요구 |
|---|---|
| `hover_or_school`, `cruise`, `turn` | 몸통 측방 굽힘·꼬리 추진, 가슴지느러미 미세 안정화, 방향 전환 시 눈/입/지느러미 정합. |
| `surface_rise` | 깊은 곳에서 **서서히** 상승; 입은 수면에 접근하지만 임의로 입·몸을 분리 이동시키지 않음. |
| `surface_peek` | **입끝만** 수면 밖에 있고 몸통 대부분은 수중. `mouth_tip`와 `body_ref`의 수면 교차가 분명해야 함. |
| `surface_gape` | 몸의 수중 위치를 대체로 유지하며 턱을 열기↔닫기 반복. 입 주변 왜곡 없이 루프; **호흡·공격 자동 판정 없음**. |
| `surface_submerge` | 입 닫기 → 입끝 아래로 잠김 → 수중 유영 포즈 복귀. 수면 마스크를 관통하지 않도록 연속 변환. |
| `surface_snap`, `swallow` | 짧은 포획용 턱 동작 및 별도 섭식 포즈. `surface_gape`와 공격 마커 공유 금지. |
| `breach_launch` | 수중 추진·몸 방향 상향·꼬리 가속 포즈 → 몸이 수면 돌파. **실제 출수 판정은 물리**. |
| `airborne_arc` | 수면에서 완전히 벗어난 뒤 **상승→정점**까지 관성 자세 변화; 지느러미는 장식적 운동만, 정지 비행 없음. |
| `surface_fall` | 정점 통과 후 중력 낙하 자세와 재입수 방향 정렬. 공중 자세가 속도를 생성하지 않음. |
| `water_reentry` | 몸과 수면의 실제 충돌 시 물방울·파문 1회, 입수 후 꼬리/지느러미 추진 자세를 천천히 재개. |
| `out_of_water` | 승인된 돌파형 이외의 수역 이탈·재입수 실패: 유영 추진 제거, 낙하/실패 표현만; 텔레포트 복귀 없음. |

## 5. 수면 표현·프레임 제작
- [설계] **3개 표현층:** `underwater_body`(수중 색감/가림), `above_water_body`(공기 중 원색/광원), `surface_contact_fx`(파문·물방울). 전환 경계는 물리 수면과 `waterline_intersection`에 동기화.
- [설계] `surface_peek`은 머리 전체·몸통이 통째로 나오는 연출 금지. 입만 노출한 상태에서도 반사·수면 가림·턱 개폐가 식별되게 정면/측면 테스트.
- [설계] `breach_launch→airborne_arc→surface_fall→water_reentry`는 물 부피, 수면 높이, 몸통 교차를 기준으로 처리; 출수 순간 수중 추진을 끊고 공중에는 중력 사용.
- [설계] 각 동작을 `pre–mid–end`로 제작하고 `surface_gape.mid`만 자연스러운 반복 루프. 공중 동작의 프레임은 **물리 궤적을 묘사**하며 비행력을 부여하지 않음.
- [설계] 3D → 2D: 동일 카메라에서 `Base/Alpha/Normal/AO/ORM` 및 필요한 Depth·수면 마스크를 출력. Normal·ORM·Depth는 수치 데이터로 취급.
- [설계] 프레임 메타: `asset_id, action, phase, frame, view, pivot, bbox, mouth_tip, body_ref, attack_socket, waterline_state, splash_marker, cycle_id` 기록.
- [설계] 전이 포즈가 필요하면 **3D에서 추가 샘플링**. 2D PNG 두 장 알파 중첩을 관절 보간으로 간주하지 않음. `DEC-06` 시점/앵커/Normal 공간은 미확정.

## 6. 참조 시점·LOD·검수
- [ ] 좌우 측면: 암수 실루엣, 입·몸통·지느러미 및 SL/TL 측정점. 정면/등면: 위향 입, 눈·턱 가동, 꼬리·지느러미 정렬.
- [ ] `surface_peek→surface_gape→surface_submerge`: 입끝만 수면 밖, 몸 수중 유지, 반복 시 턱/피부 찢김·바닥 관통 없음, 공격/섭식 마커 0회.
- [ ] `breach_launch→airborne_arc→surface_fall→water_reentry`: 전신 수면 이탈, 정점 후 낙하, 실제 수면 교차에 파문·물방울 각 1회, 수중 유영 복귀.
- [ ] 재입수 실패·취소·일시정지·프레임 이동·저장복원: 유영 추진/공중 중력 상태 불일치, 임의 정지비행·순간이동·중복 VFX 없음.
- [ ] LOD0: 입 개폐/눈/성차·지느러미 형태와 수면 교차점 유지; LOD1+: 비늘·미세 점무늬 간소화. 작은 2D 출력에서도 입 뻐끔거림 판독 가능.
- [ ] 리깅·렌더·물리 연결은 **NOT_RUN**. 실제 구현·시뮬레이션 검증 전 완료 판정 금지.

## 7. 미확정 수치·생태 주의
- **[미확인]** 출수 빈도·최대 도약 높이·공중 체공시간·도약 초기속도, 입 뻐끔거림 주기·호흡 목적. 게임 파라미터는 모두 `null`에서 시작.
- **[미확인]** 체폭·체고·정확한 관절 각도·꼬리 굴곡 폭·턱 개구량·비늘 배열·PBR/RGB·충돌체 크기·카메라 스케일.
- ***Sminthurides* sp.**가 먹이로 보고된 사실을 ***S. aquaticus*** 직접 포식으로 승격하지 않음. [G4]
- 원본 자료의 생물 형태와 [설계] 수면 연출·공중 동작을 데이터·문서에서 구분하며, 연구 사실로 표현하지 않음.

## 8. 출처·버전
- [G1] [Fishes of Australia — *G. holbrooki*](https://fishesofaustralia.net.au/home/species/3636): SL·성차·형태.
- [G2] [Murray–Darling Basin species card](https://www.mdb.fish/fish-fact-sheets/eastern-gambusia): 외형·생활사.
- [G3] [Australian Museum — Eastern Gambusia](https://australian.museum/learn/animals/fishes/eastern-gambusia-gambusia-holbrooki-girard-1859/): 종 사진·외형.
- [G4] [Banyoles호 식성 연구](https://doi.org/10.1006/jfbi.1999.0983): 톡토기 속 수준 먹이 기록.
- [BASE] `predator_gambusia_holbrooki_model(1).md` v1.0, `predator_gambusia_holbrooki_movement.md` v1.1, `AssetSize.md`(SL/TL 분리).
- **v1.1 변경:** 턱 루프/입끝·몸통 수면 판정, 수면 돌파→공중→재입수 포즈, 물리/VFX 앵커, 2D 출력·수락 시험 추가. 생태 미검증 수치는 유지하지 않고 **미정** 처리.
