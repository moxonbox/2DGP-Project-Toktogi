---
object_id: plant_spirodela_polyrhiza
asset_class_candidate: B
asset_folder_code: "B02"
group: floating_plants
taxon: "Spirodela polyrhiza"
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 개구리밥 (*Spirodela polyrhiza*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B02`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_spirodela_polyrhiza` / `floating_plants` |
| 명칭 | 개구리밥 — *Spirodela polyrhiza* |
| 배치 카테고리 / 폴더 코드 | `B` / `B02` |
| 구역 | `Z1_floating_mat` |
| 톡토기 연계 | **B/C** — 대형 다근형 부유식물로 수면 군락의 크기 대비 제공; 대상 톡토기 산란 미확인 [H06] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 엽상체 약 5–8 × 4–6 mm; 길이 5–8×; 뿌리 약 3–5 cm(별도 측정축) |
| 실루엣 | 상대적으로 넓고 큰 납작한 부유 엽상체 |
| 고유 식별점 | 맥 5–11개, 엽상체당 뿌리 5–11개; 아랫면 자주색 |
| 색·표면 | 위쪽 녹색, 뒷면 보라색 또는 자주색; 색 편차 가능 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `large_frond` | 핵심 형상 |
| `vein_set` | 분리 메시·재질 또는 선택 세부 요소 |
| `hanging_multi_roots` | 분리 메시·재질 또는 선택 세부 요소 |
| `daughter_frond` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 단독 |
| Variant 2 | 군락형 |
| Variant 3 | 뿌리 개수 변형(5~11) |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 대형 다근형 부유식물로 수면 군락의 크기 대비 제공; 대상 톡토기 산란 미확인 [H06] [H17]
- **게임 설계:** `background_floating / optional_occluder[설계]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 뿌리는 수중에 위치; 물 표면과 접촉하는 윗면은 별도로 정의
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `floating` |
| `motion_profile` | `ambient_float` |
| `anchor` | `upper_frond / root_bundle` |
| `habitat_zone` | `Z1_floating_mat` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_spirodela_polyrhiza
asset_class_candidate: B
folder_code: "B02"
evidence_level: "B/C"
zone: "Z1_floating_mat"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_spirodela_polyrhiza_movement.md
model_spec: plant_spirodela_polyrhiza_model.md
```
## 7. 미확인 값·검수
- **미확인:** 일정한 뿌리 길이/개수, 톡토기 산란, 개체별 색상 수치.
- **동정/구조:** 단일 뿌리의 Lemna와 혼동 금지; 뿌리 5~11개 별도 메쉬.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B02`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H06] [농촌진흥청 개구리밥 식물 정보](https://www.nongsaro.go.kr/mig_img/rda/tech06_image/R_Study/Rice/Control/Weeds/w_list/weeds01_26.htm)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
