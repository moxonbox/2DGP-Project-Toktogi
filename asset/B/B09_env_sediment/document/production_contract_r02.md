# B09 정적 배경 제작 계약 r02

2026-11-17 · AssetPipeLine v2.3 · `background-r02` · 모델·디테일·다시점 보완.

분리된 평판 층을 하나의 요철 퇴적층 메시로 바꾸고 불규칙 자갈·굽은 잔가지·작은 입자를 보완했다.

입경·퇴적 두께 미선정. 명목 폭 6BU는 설계값이며 발판/충돌체가 아니다.

- [r01 제작 계약](production_contract_r01.md)의 생물 근거·시트 검토·미정 값은 유지한다. 위 r02 변경이 충돌하는 제작값보다 우선한다. 원본 생물 문서 3개는 수정하지 않았다.
- [r01 GPT 시트](../sheet/env_sediment_sheet_r01.png)를 참조한 편집 가능 메시를 수정했다. 이번에는 GPT 시트를 새로 생성하지 않았다. [r02 15시점 검수판](../sheet/env_sediment_blender_reference_r02.png)은 같은 저장 모델에서 만든 후속 출력이다.
- `env_sediment` / `B09_env_sediment`의 `_`와 기존 철자를 보존한다. 정적 `static/static`, sample 0, hold, duration null. 본·리그·애니메이션·이벤트·충돌·먹이·부력은 없다.
- 기준 개체는 S. aquaticus 암컷 성체 최대 1mm. C011 몸 대용값 0.965396BU × 길이비 × 연출 계수. BU를 생물학적 m/mm로 선언하지 않는다. 크기·기관 수 미측정 값을 제작값으로 확정하지 않는다.
- 목표 기준 길이 6.00000000BU. 전체 외접 범위·앵커는 [모델 manifest](../3D/model_manifest_r02.json), `measure_kind=tile_width_design`. 고정 밀도 128/1.78 px/BU, 게임 1×. 모든 셀을 128²로 줄이지 않는다.
- 톡토기와 같은 고정 카메라 Euler 및 월드 +Z yaw를 사용한다. `left=0`, 순환 yaw 45° 간격 8방향, 별도 호환 `right=2.00151174696589rad`. right와 yaw_180은 다르다. `ortho_*` 6개는 정투영 검수 전용이다. r01의 정투영 `left/right`와 r02 게임 방향의 의미를 혼용하지 않는다.
- 메시·Normal·모든 앵커를 함께 회전해 재출력한다. mirror false. 픽셀 피벗은 크롭에 따라 달라지지만 같은 모델 원점을 가리킨다. [독립 투영 검증](../../_production/r02/direction_validation.json)
- 3,480삼각형 / 24메시 / 0본. 예산 20,000삼각형·512² 기본색·셀 한 변 최대 4096px·최소 여백 8px. 둥근 기관의 접합에는 의도한 메시 겹침이 있다. 용접된 3D 충돌체 보증은 없다.
- 종별 팔레트는 모델 manifest `palette_roles`에 저장한다. 16개 UV 역할 타일·4% 내부 여백·의도한 역할 재사용·고정 얼룩·선형 bilinear UV 표본을 사용한다. 얇은 선은 픽셀 해상도에 따라 일부 간헐적으로 보일 수 있다.
- Sprite는 C011 4단 광원 배율 뒤 역할당 13색으로 양자화한다. r01의 역할당 4색보다 약한 표면 무늬가 남는다. 고유 식물색 유지, 디더·AA·mipmap 없음, 확대 Nearest. Sprite에만 #22313B 반경 2px 외곽선. B0A/B0B는 무외곽선·반투명이다.
- W×(H×5) PNG의 순서는 Sprite/Base/Normal/RM/Emissive. Base는 무조명 sRGB, 데이터 패스 A=255, Base A로 마스크한다. Normal은 카메라 R 오른쪽·G 위·B 카메라 방향. 발광 RGB=0. 모든 패스가 같은 셀·피벗·포즈·크롭이다.

| 방향 | 셀 W,H px | Sprite bbox | 최소 여백 px |
|---|---|---|---|
| left | [448, 192] | [19, 12, 429, 180] | 12 |
| right | [432, 208] | [14, 15, 418, 193] | 14 |
| yaw_045 | [336, 224] | [12, 13, 324, 211] | 12 |
| yaw_090 | [384, 224] | [13, 13, 371, 211] | 13 |
| yaw_135 | [480, 192] | [19, 15, 461, 177] | 15 |
| yaw_180 | [448, 208] | [19, 19, 429, 189] | 19 |
| yaw_225 | [336, 224] | [12, 12, 324, 212] | 12 |
| yaw_270 | [384, 224] | [13, 20, 371, 204] | 13 |
| yaw_315 | [480, 192] | [19, 20, 461, 172] | 19 |
| ortho_front | [336, 112] | [15, 18, 321, 94] | 15 |
| ortho_back | [336, 112] | [15, 18, 321, 94] | 15 |
| ortho_left | [480, 112] | [12, 18, 468, 94] | 12 |
| ortho_right | [480, 112] | [12, 18, 468, 94] | 12 |
| ortho_top | [480, 336] | [12, 15, 468, 321] | 12 |
| ortho_underside | [480, 336] | [12, 15, 468, 321] | 12 |

- [저장본·UV·출력 검사](../2D/background-r02/validation.json) · [2D manifest](../2D/background-r02/manifest.json) · [UV left](../2D/background-r02/review/uv_checker_left.png) · [UV top](../2D/background-r02/review/uv_checker_ortho_top.png)
- 저장 Blend 재개방·packed/외부 이미지 해시·유한 UV·비퇴화 삼각형·기관 수·15시점 5패스·여백·Normal 길이 검사 통과. 독립 번들 165셀/9종 오류 거부 검사 통과.
- Blender MCP 연결 실패로 설치된 Blender 5.3.0 CLI를 사용했다. Computer-Use는 사용하지 않았다. 본게임/Pico2D 연결·SDL 업로드·최종 장치 성능·DEC-06은 보류다.
- r01 모델/출력/ZIP은 원래 경로에 그대로 보존한다. 삭제·이동이 없어 7z 중복 정리를 하지 않았다. 이전 색인은 ASSET_INDEX_r01.md로 보존하고 최신 색인만 바꾼다.
