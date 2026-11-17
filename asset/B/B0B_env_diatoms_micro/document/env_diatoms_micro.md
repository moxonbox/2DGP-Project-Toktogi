---
object_id: env_diatoms_micro
asset_class_candidate: B
asset_folder_code: "B0B"
group: microfood
taxon: null
evidence_level: "B"
version: "1.0"
source: toktogi_habitat.md
---
# 규조류 미세 표현 (환경 요소) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B0B`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `env_diatoms_micro` / `microfood` |
| 명칭 | 규조류 미세 표현 |
| 배치 카테고리 / 폴더 코드 | `B` / `B0B` |
| 구역 | `Z5_shallow_underwater / Z2_emergent_objects` |
| 톡토기 연계 | **B** — 규조류 섭식은 *Sminthurides* 속 수준 안내; 이 톡토기 종의 주식 구성 미확인 [H16] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 세포·규조 껍질 종별 치수 원문 미제시; 1mm 기준 임의 배율 금지 |
| 실루엣 | 현미경 시점의 규조류 유리질 껍질 무늬를 텍스처·장식 표면으로 표현 |
| 고유 식별점 | 갈색조 미세 조류 패턴; 종 동정 없이는 일정한 기하 형상 단정하지 않음 |
| 색·표면 | 투명·황갈색 미세 텍스처; 굴절·광택 수치 미정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `diatom_microtexture` | 핵심 형상 |
| `microscopy_overlay` | 분리 메시·재질 또는 선택 세부 요소 |
| `substrate_mask` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 작은 부착군 |
| Variant 2 | 현미경 확대 설명층 |
| Variant 3 | 바닥 미세 텍스처 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 규조류 섭식은 *Sminthurides* 속 수준 안내; 이 톡토기 종의 주식 구성 미확인 [H16] [H17]
- **게임 설계:** `background_microtexture / microscopy_view[설계]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 기본 톡토기 접촉면은 해당 기질이 소유; 규조류는 장식 레이어
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `micro_visual` |
| `motion_profile` | `static_microtexture` |
| `anchor` | `substrate_uv / microscope_focus` |
| `habitat_zone` | `Z5_shallow_underwater / Z2_emergent_objects` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: env_diatoms_micro
asset_class_candidate: B
folder_code: "B0B"
evidence_level: "B"
zone: "Z5_shallow_underwater / Z2_emergent_objects"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: env_diatoms_micro_movement.md
model_spec: env_diatoms_micro_model.md
```
## 7. 미확인 값·검수
- **미확인:** 개별 규조 종·치수·출현량·섭식량.
- **동정/구조:** 현미경 확대 컷이 실시간 게임 스케일의 원생물 크기와 혼동되지 않음.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B0B`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H16] [Australian Freshwater Invertebrates, Collembola](https://www.mdfrc.org.au/bugguide/display.asp?class=15&type=2)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
