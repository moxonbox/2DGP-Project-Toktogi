---
object_id: plant_wolffia_arrhiza
asset_class_candidate: B
asset_folder_code: "B03"
group: floating_plants
taxon: "Wolffia arrhiza"
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 분개구리밥 (*Wolffia arrhiza*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B03`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_wolffia_arrhiza` / `floating_plants` |
| 명칭 | 분개구리밥 — *Wolffia arrhiza* |
| 배치 카테고리 / 폴더 코드 | `B` / `B03` |
| 구역 | `Z1_floating_mat` |
| 톡토기 연계 | **B/C** — 1mm 톡토기와 비슷한 크기의 부유식물; 먹이·산란기질로 확인되지 않음 [H07] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 엽상체 약 0.5–1.5 × 0.4–1.2 mm; 길이 0.5–1.5× |
| 실루엣 | 뿌리가 없는 극소형 둥근~타원형 부유 덩어리 |
| 고유 식별점 | 잎·줄기처럼 펼쳐진 구조보다 미세 타원형 엽상체; 뿌리 없음 |
| 색·표면 | 녹색 미세 표면; 거친 결·표면털의 임의 추가 금지 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `tiny_frond` | 핵심 형상 |
| `daughter_body_optional` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 단독 |
| Variant 2 | 미세 군락 |
| Variant 3 | 크기 변형 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 1mm 톡토기와 비슷한 크기의 부유식물; 먹이·산란기질로 확인되지 않음 [H07] [H17]
- **게임 설계:** `background_floating`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 미세 배경 점유; 톡토기 게임의 발판 판정은 별도 [설계] 승인
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `floating` |
| `motion_profile` | `ambient_float` |
| `anchor` | `frond_center` |
| `habitat_zone` | `Z1_floating_mat` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_wolffia_arrhiza
asset_class_candidate: B
folder_code: "B03"
evidence_level: "B/C"
zone: "Z1_floating_mat"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_wolffia_arrhiza_movement.md
model_spec: plant_wolffia_arrhiza_model.md
```
## 7. 미확인 값·검수
- **미확인:** 특정 지역 개체 크기분포, 톡토기 이용, 재질 파라미터.
- **동정/구조:** 절대 뿌리를 생성하지 않음; 축척 0.5~1.5× 유지.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B03`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H07] [Kew POWO, Wolffia arrhiza](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:1044795-2/general-information)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
