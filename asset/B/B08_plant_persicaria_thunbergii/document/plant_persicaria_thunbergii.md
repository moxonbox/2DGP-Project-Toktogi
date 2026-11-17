---
object_id: plant_persicaria_thunbergii
asset_class_candidate: B
asset_folder_code: "B08"
group: riparian_herbs
taxon: "Persicaria thunbergii"
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 고마리 (*Persicaria thunbergii*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B08`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_persicaria_thunbergii` / `riparian_herbs` |
| 명칭 | 고마리 — *Persicaria thunbergii* |
| 배치 카테고리 / 폴더 코드 | `B` / `B08` |
| 구역 | `Z3_wet_bank / Z4_riparian_vegetation` |
| 톡토기 연계 | **B/C** — 육상-수면 전이의 낮은 초본·그늘·연결 구조; 대상 톡토기 이용 미확인 [H13] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 뻗는 줄기 길이 약 1 m; 잎 개별 길이 미확인 |
| 실루엣 | 젖은 둑을 따라 뻗고 다른 구조물에 걸리는 초본 |
| 고유 식별점 | 각진 줄기, 아래쪽을 향한 가시, 분홍/흰 꽃 |
| 색·표면 | 녹색 잎·녹갈색 줄기·연분홍 또는 흰 꽃; 세부 RGB 미정 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `angular_stem` | 핵심 형상 |
| `leaves` | 분리 메시·재질 또는 선택 세부 요소 |
| `downward_prickles` | 분리 메시·재질 또는 선택 세부 요소 |
| `flowers` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 잎 위주 |
| Variant 2 | 꽃 있음/없음 |
| Variant 3 | 물가 가로로 뻗은 형태 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 육상-수면 전이의 낮은 초본·그늘·연결 구조; 대상 톡토기 이용 미확인 [H13] [H17]
- **게임 설계:** `background_cover / bank_connection`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** 줄기 일부 물가의 접촉 후보; 플레이어 경로로 쓰려면 별도 검증
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `rooted` |
| `motion_profile` | `wind_sway` |
| `anchor` | `stem_nodes / flower_tip` |
| `habitat_zone` | `Z3_wet_bank / Z4_riparian_vegetation` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_persicaria_thunbergii
asset_class_candidate: B
folder_code: "B08"
evidence_level: "B/C"
zone: "Z3_wet_bank / Z4_riparian_vegetation"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_persicaria_thunbergii_movement.md
model_spec: plant_persicaria_thunbergii_model.md
```
## 7. 미확인 값·검수
- **미확인:** 잎 너비·가시 개수/배열·실측 줄기 굵기·톡토기 기질 이용.
- **동정/구조:** 가시는 줄기의 아래쪽 방향; 갈대·부들과 독립된 저층 실루엣.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B08`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H13] [국립수목원 생물도감, 고마리](https://www.bris.go.kr/portal/book/childIlustbkDetailPopup.do?ilustbkNo=307&menuId=114)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
