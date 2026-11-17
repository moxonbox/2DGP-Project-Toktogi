---
object_id: plant_lemna_minor
asset_class_candidate: A
asset_folder_code: "A01"
group: floating_plants
taxon: "Lemna minor"
evidence_level: "A+B"
version: "1.0"
source: toktogi_habitat.md
---
# 나도좀개구리밥 (*Lemna minor*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `A01`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_lemna_minor` / `floating_plants` |
| 명칭 | 나도좀개구리밥 — *Lemna minor* |
| 배치 카테고리 / 폴더 코드 | `A` / `A01` |
| 구역 | `Z1_floating_mat / Z0_water_surface` |
| 톡토기 연계 | **A+B** — 물알둥근톡토기의 산란홈·알·배설물 덮개가 직접 사진으로 확인된 유일한 특정 식물 [H02] [H03] [H04] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 엽상체 2.5–6 × 1.5–4 mm; 톡토기(암컷 최대 1 mm) 대비 길이 2.5–6× |
| 실루엣 | 납작한 타원~거꿀달걀형 엽상체; 일반 잎·줄기 구조로 오해하지 않음 |
| 고유 식별점 | 희미한 잎맥 보통 3개; 엽상체마다 단일 뿌리, 아래쪽 뿌리골무 |
| 색·표면 | 녹색(붉은 기 가능), 얇고 비교적 매끈한 수면 접촉 표면 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `frond` | 핵심 형상 |
| `root_single` | 분리 메시·재질 또는 선택 세부 요소 |
| `daughter_frond` | 분리 메시·재질 또는 선택 세부 요소 |
| `root_cap` | 분리 메시·재질 또는 선택 세부 요소 |
| `oviposition_cup` | 분리 메시·재질 또는 선택 세부 요소 |
| `eggs` | 분리 메시·재질 또는 선택 세부 요소 |
| `pellet_cover` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 단독 엽상체 |
| Variant 2 | 어미·딸 연결체 |
| Variant 3 | 산란홈 있음/없음 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 물알둥근톡토기의 산란홈·알·배설물 덮개가 직접 사진으로 확인된 유일한 특정 식물 [H02] [H03] [H04] [H17]
- **게임 설계:** `walk_on[A·설계 접촉] / oviposit_on[A] / float[설계 표현]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 엽상체 상면 보행 접촉, 가장자리와 수면 경계 별도 관리; 산란홈 위치는 원본 사진 참조
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `floating; spawning_pocket` |
| `motion_profile` | `float_bob` |
| `anchor` | `frond_top / root_tip / oviposition_site` |
| `habitat_zone` | `Z1_floating_mat / Z0_water_surface` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_lemna_minor
asset_class_candidate: A
folder_code: "A01"
evidence_level: "A+B"
zone: "Z1_floating_mat / Z0_water_surface"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_lemna_minor_movement.md
model_spec: plant_lemna_minor_model.md
```
## 7. 미확인 값·검수
- **미확인:** 뿌리 길이, 산란홈 깊이, 알 직경, 부유속도, 표면 강성, PBR 수치.
- **동정/구조:** 1개 뿌리/엽상체; 3맥은 약하게; 산란홈은 일반 먹이 구멍이 아님.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `A01`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H02] [Janssens & Huskens (2016), S. aquaticus 산란](https://www.collembola.org/publicat/eggdepos.htm)
- [H03] [Kew POWO, Lemna minor](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:526194-1/general-information)
- [H04] [국립생물자원관 국가생물종목록](https://www.nibr.go.kr/aiibook/access/ecatalogt.jsp?Dir=20&start=172)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
