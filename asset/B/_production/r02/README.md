# B 정적 배경 r02 인계

2026-11-17 · AssetPipeLine v2.3 / AssetSize 기준 · 11종 모델·디테일·시점 보완.

- B01: 비대칭 볼륨 잎·표면에 붙인 3개 잎맥·곡선 단일 뿌리·뿌리 싸개를 보완했다.
- B02: 7개 표면 잎맥·7개 곡선 뿌리와 끝마개·자주색 아랫면을 보완했다. 35mm 뿌리의 길이비를 유지했다.
- B03: 무근 타원체를 더 도톰하게 만들고 윗면을 살짝 평평하게 조정했다. 두께 0.44×길이는 각색이다. 뿌리·털·맥은 없다.
- B04: 한 쌍의 오목한 잎·주맥/측맥·잎당 8무리×3가닥 곡선 털·입체 분지 수중 잎을 보완했다. 털 수와 수중 잎 크기는 각색이며 수중 잎은 뿌리가 아니다.
- B05: 곡선 줄기·둥근 마디 접합·2회 갈라지는 잎을 보완했다. 5BU 절편·4마디·마디당 6잎은 제작값이다.
- B06: 꽃이삭 끝을 둥글게 하고, 도톰한 곡선 띠잎·잎집·세로 무늬를 보완했다.
- B07: 타원 알갱이 꽃차례를 가는 가지와 깃털형 작은 이삭으로 바꾸고 마디·잎집을 보완했다.
- B08: 연속된 화살형 잎·마디집·아래 가시·굽은 꽃자루·입체 꽃잎/꽃받침을 보완했다.
- B09: 분리된 평판 층을 하나의 요철 퇴적층 메시로 바꾸고 불규칙 자갈·굽은 잔가지·작은 입자를 보완했다.
- B0A: 얇은 요철 막·낮은 군집·고정 얼룩과 가변 투명도를 보완했다. Alpha 상한은 178/255이며 외곽선은 없다.
- B0B: 8개 장식 껍질의 외곽 테두리·줄무늬·형태 차이를 보완했다. 종 동정용이 아닌 현미경 전용 개념도다. Alpha 상한 216/255, 무외곽선.

- 편집 가능한 Blend 11개, 종당 15뷰/5패스, 총 165셀. 8개 순환 yaw + 별도 right가 톡토기 카메라와 일치한다. 6개 `ortho_*`는 검수 전용이다. [원본 방향 계약](reference/c011_view_contract.json)의 DEC-06 보류 상태는 해제하지 않았다.
- [전체 색인](../../ASSET_INDEX.md) · [미리보기](overview.png) · [전후 비교](before_after.png) · [톡토기 9방향 1×](c011_directions_1x.png) · [고정 장면 1×](comparison_1x.png) · [회색조](comparison_grayscale_1x.png) · [이동 광원 A](comparison_light_260.png) / [B](comparison_light_680.png)
- [ZIP](backgrounds_r02.zip) / [잠금](backgrounds_r02.source.json). 독립 [로더](tools/background_bundle.py)는 직사각형 셀·straight Alpha·8셀 LRU·피벗을 지원한다. `maps(asset_id, view='left')`, `draw(canvas, asset_id, world_position, camera=(0,0), view='left')`. B0B는 월드 draw를 거부하고 별도 현미경 maps만 허용한다.
- [런타임 검사](runtime_validation.json): 165셀 5패스 일치, 9종 잘못된 입력 거부. 120프레임/4개 배경 CPU 합성 p95 2.123ms, 최대 3.177ms. [방향 검사](direction_validation.json): 앵커 414개, 최대 오차 0.00007013px < 0.002px.
- 전체 방향을 모두 RGBA로 디코딩하면 674,027,520bytes (642.8MiB). ZIP은 22,650,029bytes. 긴 B02 뿌리·B04 잎 쌍의 높은 해상도가 주요 비용이다. 전체 선로딩을 권장하지 않으며 8셀 캐시도 실기 메모리 예산 합격을 뜻하지 않는다.
- 기존 r01 GPT 시트를 재사용하고 메시/텍스처를 수정했다. 4단 광원 뒤 역할별 13색·고정 UV 무늬·Nearest. B0A/B0B는 가변 Alpha와 무외곽선. 원본 생물 문서 33개와 r01 산출물은 보존한다. 생성물은 종 동정/실측 자료가 아니다.
- [입력 해시](source_documents.json) · [도구 기록](tool_execution.json) · [파일 목록](release_files.json). 원본 외부 자료의 권리 검토는 이번 범위에 포함하지 않는다. 새 외부 사진/모델은 사용하지 않았다.
- Blender MCP 연결 실패 → 설치된 Blender 5.3.0 CLI. Computer-Use 없음. 본게임/Pico2D/SDL 업로드·최종 장치 60fps·DEC-06 미검증. 바람·성장·충돌·발판·먹이·부력 이벤트는 제작하지 않았다.

재생성: 프로젝트 루트에서 아래 순서로 실행한다. 필요 패키지 bpy(Blender 내장), NumPy, Pillow. Blender 실행 파일 경로는 설치 환경에 맞춘다.

```powershell
blender -b --python asset/B/_production/r02/tools/build_backgrounds.py
blender -b --python asset/B/_production/r02/tools/export_backgrounds.py
python asset/B/_production/r02/tools/package_backgrounds.py
python asset/B/_production/r02/tools/finalize_records.py
```

r01은 원래 경로에 남아 있다. 복원은 ASSET_INDEX_r01.md로 이전 파일을 선택하면 된다. 최신 색인 덮어쓰기 12개 외에는 추가 배포이며 이전 모델/ZIP 교체·삭제·이동은 없다.
