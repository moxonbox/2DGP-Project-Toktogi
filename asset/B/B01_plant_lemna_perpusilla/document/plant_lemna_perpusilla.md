---
object_id: plant_lemna_perpusilla
asset_class_candidate: B
asset_folder_code: "B01"
group: floating_plants
taxon: "Lemna perpusilla"
evidence_level: "B/C"
version: "1.0"
source: toktogi_habitat.md
---
# 좀개구리밥 (*Lemna perpusilla*) — 객체 상세 명세
> 범위: 원본 서식지 명세의 **생태·형태 사실**과 2DGP **게임 설계 제안**을 분리. 프로젝트 문서 폴더 코드는 `B01`다.
## 1. 정체성·배치
| 항목 | 명세 |
|---|---|
| ID / 범주 | `plant_lemna_perpusilla` / `floating_plants` |
| 명칭 | 좀개구리밥 — *Lemna perpusilla* |
| 배치 카테고리 / 폴더 코드 | `B` / `B01` |
| 구역 | `Z1_floating_mat` |
| 톡토기 연계 | **B/C** — 같은 부유식물대의 별도 종 예시; 물알둥근톡토기의 산란·섭식 직접 기록 없음 [H05] [H04] [H17] |
## 2. 외형·실제 크기
| 항목 | 요구사항 |
|---|---|
| 확인 치수 | 엽상체 약 1.5–4 × 0.7–2.5 mm; 길이 1.5–4× |
| 실루엣 | 비대칭 난형의 작은 부유 엽상체 |
| 고유 식별점 | 뿌리 1개; 뿌리 기부 싸개에 날개가 있는 동정 단서; 위쪽 미세 돌기 가능 |
| 색·표면 | 녹색 엽상체; 표면 미세 구조는 식물 사진 기준 |
| 크기 기준 | `toktogi` 암컷 최대 체장 **1.0mm = 길이비 1×**; 다른 치수축은 분리 [H17] |
## 3. 구성 부품과 변형
| 구성 | 용도 |
|---|---|
| `asymmetric_frond` | 핵심 형상 |
| `root_single` | 분리 메시·재질 또는 선택 세부 요소 |
| `root_sheath_wing` | 분리 메시·재질 또는 선택 세부 요소 |
| `daughter_frond` | 분리 메시·재질 또는 선택 세부 요소 |
| 변형 | 사용 상태 |
|---|---|
| Variant 1 | 단독 엽상체 |
| Variant 2 | 작은 연결 군락 |
| Variant 3 | 뿌리 싸개 확대형 |
## 4. 상호작용(실제 근거와 구현 분리)
- **기록·생태:** 같은 부유식물대의 별도 종 예시; 물알둥근톡토기의 산란·섭식 직접 기록 없음 [H05] [H04] [H17]
- **게임 설계:** `background_floating / optional_walk_surface[설계·미검증]`; 근거 C/B인 동작을 해당 톡토기 종의 확정 습성으로 사용하지 않는다.
- **접촉 영역:** B 배경 후보; 플레이어 접촉을 추가하려면 A 에셋으로 분리 승인 필요
- **동작 데이터:** 실제 충돌·부력·위치·자원 소모는 게임 시스템이 소유하고 모델 애니메이션은 표현만 담당.
## 5. 상태·프리셋
| 필드 | 값·제약 |
|---|---|
| `runtime_state` | `floating` |
| `motion_profile` | `ambient_float` |
| `anchor` | `frond_center / root_base` |
| `habitat_zone` | `Z1_floating_mat` |
| `biological_scale / display_scale` | 별도 저장; 현행 C011 BU를 실제 1mm로 자동 간주 금지 |
## 6. 구현용 최소 데이터 (제안)
```yaml
object_id: plant_lemna_perpusilla
asset_class_candidate: B
folder_code: "B01"
evidence_level: "B/C"
zone: "Z1_floating_mat"
length_mm: null # 위 출처 수치가 단일 체장값인 경우에만 채움
model_scale_bu: null
display_scale: null
collision_profile: null
movement_spec: plant_lemna_perpusilla_movement.md
model_spec: plant_lemna_perpusilla_model.md
```
## 7. 미확인 값·검수
- **미확인:** 정밀 잎맥·뿌리 길이·동일 장소 출현 및 톡토기 산란 여부.
- **동정/구조:** L. minor의 뿌리 싸개 특징을 그대로 복사하지 않기; 1뿌리 유지.
- **근거 경계:** 대상 종 직접 이용(A), 일반 생태(B), 게임 가정(C)을 혼동하지 않음.
- **에셋 번호:** `AssetLabelRule.txt` 기준 폴더 접두사는 `B01`다. variation·모션·프레임 번호는 별도 제작 시 확정한다.
## 8. 근거
- [H05] [Kew POWO, Lemna perpusilla](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:526212-1/general-information)
- [H04] [국립생물자원관 국가생물종목록](https://www.nibr.go.kr/aiibook/access/ecatalogt.jsp?Dir=20&start=172)
- [H17] `AssetSize(2).md` — 톡토기 암컷 1mm 기준; BU/픽셀은 별도
