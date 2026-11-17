# B 배경 에셋 제작 r01

2026-11-17 · [AssetPipeLine v2.3 원문 스냅샷](reference/AssetPipeLine.md) · [AssetSize v1.1](reference/AssetSize.md)

11종 정적 배경을 제작했다. GPT 시트 11장, 편집 가능한 .blend 11개, Blender 검수 시트 11장, 7방향 × 11종 = 77셀, 셀당 5패스다. 독립 번들 검증은 통과했고 본게임 연결은 보류다.

| ID | 논리 ID | 삼각형 | 게임 방향 셀 px | 크기 정책 |
|---|---|---:|---|---|
| [B01](../B01_plant_lemna_perpusilla/ASSET_INDEX.md) | plant_lemna_perpusilla | 924 | 192×128 | display_relative |
| [B02](../B02_plant_spirodela_polyrhiza/ASSET_INDEX.md) | plant_spirodela_polyrhiza | 1,172 | 432×2384 | display_relative |
| [B03](../B03_plant_wolffia_arrhiza/ASSET_INDEX.md) | plant_wolffia_arrhiza | 528 | 96×64 | display_relative |
| [B04](../B04_plant_salvinia_natans/ASSET_INDEX.md) | plant_salvinia_natans | 2,328 | 1232×688 | display_relative |
| [B05](../B05_plant_ceratophyllum_demersum/ASSET_INDEX.md) | plant_ceratophyllum_demersum | 4,732 | 272×416 | design_module |
| [B06](../B06_plant_typha_orientalis/ASSET_INDEX.md) | plant_typha_orientalis | 760 | 272×512 | distant_background |
| [B07](../B07_plant_phragmites_australis/ASSET_INDEX.md) | plant_phragmites_australis | 12,968 | 304×624 | distant_background |
| [B08](../B08_plant_persicaria_thunbergii/ASSET_INDEX.md) | plant_persicaria_thunbergii | 8,868 | 576×224 | distant_background |
| [B09](../B09_env_sediment/ASSET_INDEX.md) | env_sediment | 1,164 | 448×192 | design_module |
| [B0A](../B0A_env_periphyton_biofilm/ASSET_INDEX.md) | env_periphyton_biofilm | 2,112 | 240×96 | design_module |
| [B0B](../B0B_env_diatoms_micro/ASSET_INDEX.md) | env_diatoms_micro | 1,792 | 240×96 | microscopy_only |

## 열기

- [전체 미리보기](overview.png): 각 항목 맞춤 축소, 상대 크기 비교용 아님.
- [C011과 1× 비교](comparison_1x.png) · [회색조](comparison_grayscale_1x.png) · [광원 왼쪽](comparison_light_260.png) · [광원 오른쪽](comparison_light_680.png)
- [런타임 ZIP](backgrounds_r01.zip) · [잠금/해시](backgrounds_r01.source.json) · [독립 로더 검사](runtime_validation.json)
- [원문 해시](source_documents.json) · [실행 경로·제약](tool_execution.json) · [생성 프롬프트/제작값](assets.json)

1× 비교판은 동일 화면 좌표·C011 원본 Sprite·동일 BU/px를 사용한다. 큰 원거리 식물의 일부는 960×560 검수 창 밖으로 나갈 수 있지만 원본 셀은 잘리지 않았다. 물리 발판 배치나 실제 플레이 증거는 아니다.

## 크기·상태 계약

- B01/B02/B03/B04의 선택 잎 길이는 2.5/6/1/10mm, 연출 계수 1이다. C011 몸길이 대용값 0.965396BU와 같은 카메라 픽셀 밀도로 변환했다. B02 뿌리 35mm는 별도 축이다.
- B06/B07은 미터 규모 식물을 원거리 배경으로 축소했다. 계수 0.006/0.0045를 기록했고 실측 동등 거리 표시로 주장하지 않는다. B08은 줄기 길이와 직선 폭이 다른 설계 대용 모듈이다.
- B05/B09/B0A/B0B의 생물 길이는 null이다. B0B는 현미경 전용이며 일반 월드 draw를 차단한다. 배경 분류만으로 애니메이션·부력·충돌·먹이·발판을 만들지 않았다.
- B0A/B0B는 반투명 표면 예외로 Alpha 178/216·외곽선 없음. 다른 Sprite/Base Alpha는 0/255. 데이터 패스의 A=255는 coverage가 아니다.

## 재현

현재 B 폴더에서 실행한다. Blender 5.3.0, Python 3.13, NumPy 2.5.5, Pillow 13.0.0을 사용했다. Python 검수판 글꼴 경로는 Windows 맑은 고딕이다.

```powershell
& 'C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe' --background --factory-startup --python-exit-code 1 --python _production/tools/build_backgrounds.py
& 'C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe' --background --factory-startup --python-exit-code 1 --python _production/tools/export_backgrounds.py
python _production/tools/package_backgrounds.py
python _production/tools/finalize_records.py
```

Blender 명령 뒤 `-- B01 B02`를 붙여 해당 모델/출력만 재현할 수 있다. 생성 시트는 에셋 안에 저장되어 재생성할 때 도구 생성 캐시가 필요하지 않다. 모델/패스 변경 후 패커·기록도 다시 실행한다. 변경 전 원본의 별도 보존은 호출자의 책임이다.

## 독립 연결 예시

```python
from pathlib import Path
from PIL import Image
from background_bundle import BackgroundBundle

bundle = BackgroundBundle(Path('_production/backgrounds_r01.zip'))
canvas = Image.new('RGBA', (960, 560))
bundle.draw(canvas, 'plant_lemna_perpusilla', world_position=(300, 320), camera=(0, 0))
maps = bundle.maps('plant_lemna_perpusilla', 'game')
bundle.close()
```

`background_bundle.py`가 있는 `_production/tools`를 import 경로에 둔다. draw는 월드 좌표에서 카메라를 빼고 피벗을 한 번 적용한다. Sprite 표시용 API이며 재조명에는 Base/Normal/RM/Emissive와 같은 월드 광원을 사용한다. 현행 C011 전용 로더에 이 ZIP을 바로 전달하면 안 된다.

## 검증 범위

- 저장 Blend 재개방·외부/packed 해시·UV 유한성/범위·비퇴화 삼각형·뿌리 개수·77셀 5패스 정합·최소 여백·Normal 길이·0발광·RM 채널·숨은 RGB를 검사했다.
- 최소 Sprite 여백 12px, Normal UNORM 길이 오차 최대 0.00659. 기존 C011 검증 수치를 가져온 결과가 아니다.
- 독립 로더의 잘못된 schema/패스/피벗/rect/누락셀/중복셀/해시 및 현미경 월드 배치 거부 8개 음성 검사를 통과했다.
- 전 방향 RGBA 원본 280,222,720byte, ZIP 7,023,805byte. 로더는 최대 8셀 LRU다. 런타임에 전 방향을 동시에 올리지 않는다.
- 정적 배경 4개·960×560·120프레임 Pillow CPU 합성 p95 1.811ms, 최대 2.331ms. 셰이딩·SDL 업로드·게임 전체 16.7ms 예산의 측정은 아니다.
- 동일 power 0.82·ambient 0.34·두 월드 광원 위치에서 C011과 B를 합성했다. 반투명 및 색상/회색조 검수판을 보존했다.

## 보류·차이

- Blender MCP/CLI MCP가 연결 실패·시간 초과되어 직접 CLI를 사용했다. [관찰 기록](tool_execution.json). Computer-Use는 사용하지 않았다.
- GPT 다면 시트에는 일부 원근·겹침·치수선 비례가 남는다. 에셋별 보충 계약에서 해당 차이를 수정 규칙으로 고정하고 같은 메시의 Blender 정투영을 후속 기준으로 남겼다. 시트에 존재하지 않는 생물 사실을 만들지 않았다.
- 본게임/Pico2D·StageLevel의 두 Level·충돌 발판·SDL 성능·DEC-06·실기 승인은 미완료다. 이번 결과는 별도 정적 배경 묶음이며 기존 C011 실행 번들을 교체하지 않는다.
- UV는 저대비 반복 기본색용이다. 비대칭 고해상도 페인팅·수치 기반 텍셀 밀도 검수·일반 3D 물리용 용접/관통 검사는 수행하지 않았다.
- 이전 3D 파일이 없어 7z 복원 지도는 해당 없음. FBX·추가 variation·바람/부유 모션·Bloom은 제작하지 않았다.
