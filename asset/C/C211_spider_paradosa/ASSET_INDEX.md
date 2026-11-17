# C211 Pardosa — idle-r02

2026-11-17 · AssetPipeLine v2.2 / AssetSize v1.1 · **3D·idle·독립 번들 검증 완료, 게임 연결 보류**

- [현재 Blend](3D/spider_pardosa_idle_r02.blend) · [idle 미리보기](PardosaIdlePreview.html) · [GPT Image 시트](sheet/spider_pardosa_sheet_r02.png)
- [톡토기와 크기 비교](comparison/scale_color_left.png) · [오른쪽 비교](comparison/scale_color_right.png) · [idle 비교 APNG](comparison/idle_comparison_left.png) · [공유 이동 광원 APNG](comparison/shared_light_left.png)
- [출력 manifest](2D/idle-r02/manifest.json) · [ZIP](2D/idle-r02/spider_pardosa_idle_r02.zip) · [잠금](2D/idle-r02/spider_pardosa_idle_r02.source.json) · [제작·검수 근거](document/production_r02.json)

## 적용 범위와 식별

이번 수정은 종·체장 선택, C011과의 스타일/픽셀 밀도 정합, `idle_scan`의 저장본·출력·독립 로더 검증까지다. AI·전투·이동·다른 동작과의 전환·Pico2D·Bloom은 구현 완료가 아니다.

| 구분 | 현재 값 |
| --- | --- |
| 폴더 / asset_id | `C211_spider_paradosa` — 기존 철자와 `_` 유지 |
| 생물·명세 object_id | `spider_pardosa` |
| 외형 variation | `adult_female_stylized` |
| 클립 / 구간 / 표본 / revision | `idle_scan` / `mid` / 0–23 / `idle-r02` |
| 번호 규칙 | C2xx 유지. 신규 16진수 배정·DEC-06 양산 좌표는 미정 |
| 현행 프레임 | `2D/idle/idle_scan/<left|right>/<0..23>.png` |
| 제작 아틀라스 | `2D/idle-r02/` |

원본 [외형](document/spider_pardosa_model.md)·[행동](document/spider_pardosa_movement.md)·[생물](document/spider_pardosa.md) 문서는 속 수준 근거다. 사용자가 이번 에셋에 선택한 **Pardosa agrestis 암컷 성체 약 5mm**를 [제작 계약](document/source_contract.json)에 별도 고정했다. 색·기관 비율·잔동작은 게임 각색이며 종 동정용 실측 형상으로 주장하지 않는다.

## 크기와 스타일 변경

- C011 기준은 *S. aquaticus* 암컷 성체 **최대 약 1mm**다. 평균 체장이 아니다. 생물 길이비 5 × 연출 계수 1 × C011 몸길이 대용값 0.965396 BU = **4.82698 BU**다.
- 새 모델의 머리가슴 앞끝→배 뒤끝 로컬 Y 길이 실측은 **4.8269798756 BU**, 비율 **4.9999998711배**다. 눈·촉지·다리·실젖은 체장 측정에서 제외한다. 전체 외접은 약 **7.6608 × 6.2532 × 2.1218 BU**다.
- 이 값은 상대 화면 연출이다. `1BU=1m` 실측 모델로 해석하지 않는다. 다리 편길이·체폭·체고는 과학적 실측값이 아니며 충돌 프로필은 `null`이다.
- r01의 2.25 BU / 192px / 42.67px·BU⁻¹에서 r02의 4.82698 BU / 640px / **71.910112px·BU⁻¹**로 갱신했다. C011과 같은 **0.01390625 BU/px**, 표시 1×다. 체장비는 셀 크기 비율로 계산하지 않았다.
- C011 직교 카메라 방향과 호환 `right` yaw 2.001511747을 사용한다. `right`는 좌우 미러나 180° 뷰가 아니다. 스케일 8.9 BU, 좌우 여백 균형을 위한 카메라 가로 오프셋 ±12px를 기록했다. 피벗은 left **(332,440)**, right **(308,440)**다.
- 좌우 모두 Sprite 외접 **608 × 297–298px**, Base **604 × 293–294px**, 최소 투명 여백 **16px**다. 사전 기준 8px를 통과했다. 아틀라스 패딩 2px와 셀 여백은 별개다. [48표본 크기 검사](2D/idle-r02/size_validation.json)
- 몸통을 더 둥글게, 다리를 약 25% 도톰하게 조정했다. 세밀한 반점을 넓고 절제된 갈색 무늬로 줄였다. 흰 몸·6다리 같은 C011의 고유 형질은 복제하지 않았다.
- 외곽색 RGB **(34,49,59)**, Base 외접 대비 사방 **2px** 확장을 48장 모두 확인했다. 눈은 비발광 반사 재질이다. 몸/다리 roughness .77, 배 .84, 눈 .48이다.
- 3D 미리보기는 NPR_Toon Size .55 / Smooth .035, AgX / None, 개체 크기에 비례한 스튜디오 광원이다. Sprite는 4단계 명암이다. 실제 재조명 비교는 C011 `lighting.py`를 재사용해 **같은 장면 광원·power .82·ambient .34·높이 116px**에서 객체별 위치 벡터를 계산했다. C011 128px 원본과 바이트 일치를 확인했다.
- 색상·회색조·좌우·8초 idle 및 이동 광원 비교를 `comparison/`에 남겼다. 이것은 독립 검수 장면이며 실제 게임 환경·전환 검수는 아니다.

## 시트·3D·idle

- 새 시트는 기존 거미 시트, C011 idle 표시 이미지, C011 실제 Blend 6시점 렌더를 GPT Image 참조로 전달했다. [프롬프트](sheet/spider_pardosa_sheet_r02_prompt.txt), 입력 해시·생성 이력은 제작 기록에 있다. 반환되지 않은 모델 버전·seed는 `null`이다.
- 정면·좌·우·후·상·하면에서 8다리와 4·2·2 눈 배열을 대조했다. 겹쳐 보이는 관절은 명세를 우선했다. 시트의 치수를 생물 실측으로 사용하지 않았다. 기존 `sheet/sheet.png` 등 톡토기 자료는 모델링 입력에서 제외하고 보존했다.
- 편집 메시 **4,750정점 / 9,192삼각형**, 리그 **77본**, BaseColor **1024²**. 예산 16,000삼각형 / 96본 안이다. 시트·텍스처는 Blend에 패킹했다.
- 앞 -Y / 위 +Z / 개체 왼쪽 +X. 메시·리그·루트 스케일은 1이다. `physics_root`와 `visual_root`의 게임 이동은 없으며 8개 IK 지지발을 고정한다. 바닥은 실제 발마디 최저 정점으로 맞췄다.
- UV는 부위별 차트와 2px 패딩이다. 미세 털은 생략했고 텍셀 밀도는 부위별로 다르다. 0면적 UV·미할당 웨이트는 0이다. 체크 타일의 시각적 늘어짐 판정은 별도 보류다.
- `C211_idle_scan_mid_r02`: **2초**, 제작 **48fps**, 프레임 1–96 / 경계 97, 출력 **24표본 × 좌우 = 48장**, 표본 간격 1/12초. 주기적 Hermite/Bezier 이징으로 끝/시작 속도를 연결했다. 중복 끝셀은 출력하지 않는다.
- 몸통 중심 이동 범위는 약 **(4.63,0.084,3.41)px**다. 몸 yaw .02rad, 촉지 yaw .08rad와 두 배 주기 잔동작을 사용한다. 2초 주기는 C011 1.6초보다 느린 대기 연출이며 생물 측정 속도가 아니다.
- 중립 진입/복귀 경계는 첫 자세다. 별도 `pre/end`·타 행동 전환은 아직 없다. 효과 목록은 비어 있고 공격 소켓은 비활성이다. 저장본의 내장/외부 [선택기](3D/tools/select_idle.py)로 시간 선택이 가능하다.

## 출력과 검증 상태

- 개별 PNG는 **640×3840 RGBA**이며 Sprite / Base / Normal / AO / RM / Emissive 6패스를 적층한다. C011의 5패스 파일과 다르다.
- Sprite/Base는 sRGB, 수치 패스는 선형이다. Normal RGB는 카메라 오른쪽·위·카메라 방향 UNORM이며 재정규화·Base A 마스크를 적용한다. RM R=roughness/G=0/B=0, Emissive=0. AO는 0.22BU 내 5방향 검사다.
- 카메라 깊이 검사 범위를 평가 메시의 최후면 +1BU로 수정했다. 확대 후 뒤쪽 다리를 자르던 고정 20BU 제한을 제거했고 **384개 발 마커가 Base coverage 3px 이내**인지 재검증했다.
- [저장본 검사](3D/saved_validation.json): 193개 키 사이 자세, 정순·역순·임의 seek, 루프, 접지 검사 통과. 교차는 4프레임 간격의 서로 다른 다리 표면을 검사하며 의도된 몸통 부착부는 제외한다. 모든 관통이 없다는 전역 보증은 아니다.
- [크기·리듬 검사](3D/style_validation.json): 5배 체장, 루프 속도 오차 <.025BU/s, 시작 위상 4종의 10/15/20/30/60fps 표본 선택 확인. 10fps에서는 24표본 중 20개가 표시된다.
- [출력 검사](2D/idle-r02/export_validation.json)와 [패키지 검사](2D/idle-r02/package_validation.json): 여백·눈 픽셀·Normal·6패스 Alpha·24개 서로 다른 표본·APNG 2초·CRC/SHA256 통과.
- [번들 검사](2D/idle-r02/bundle_validation.json): 별도 ZIP에서 48셀 디코딩, schema/revision/기반·원본 서명 확인. 중복 표본·누락 뷰/패스·0 시간·경계 밖 rect·비유한 마커·잘못된 참조/전환·손상 ZIP 등 10종을 거부한다. 실패를 idle로 대체하지 않는다.
- HTML의 시간 경계·seek·일시정지·광원·평탄 Normal 분기는 Node의 합성 픽셀 검사로 확인했다. 실제 브라우저 UI 조작은 수행하지 않았다.
- [성능·메모리 측정](2D/idle-r02/performance_validation.json): 로드/24표본 워밍업과 120프레임 p95·최대를 구분했다. 640px 단일 개체 left 뷰의 CPU 재조명·RGBA 전달·SDL 소프트웨어 합성을 측정한다. 실 GPU 업로드·창 합성·게임 AI는 미측정이다.
- 측정 장치 **AMD RYZEN AI MAX+ 395 w/ Radeon 8060S**: 고정 광원 캐시 p95 **4.17ms** / 최대 **4.63ms**, 이동 광원 CPU p95 **287.76ms** / 최대 **318.94ms**. 16.7ms 이동 광원 예산 미달. 프로세스 peak working set **147.5MiB**.
- 원시 고유 셀은 **450MiB**, 전체 디코딩 아틀라스는 약 **455.64MiB**, 한 뷰 고정 광원 캐시는 **37.5MiB**다. 브라우저는 base64·캔버스 사본을 추가로 소비한다. ZIP 크기를 메모리 비용으로 보지 않는다. 원시 셀 예산 512MiB, 셰이딩 캐시 예산 128MiB이며 실제 게임 총예산은 미확정이다.
- **기존 게임 로더는 128px·integrated-r5 전용**이다. 새 640px·6패스는 [독립 로더](3D/tools/idle_bundle.py)와 비교 장면에서만 검증했다. 기존 C011 실행 번들을 교체하지 않았다. 게임 상태·충돌·효과 연결, 표시 예산 달성, 실기 검증 전에는 게임 사용 가능으로 표시하지 않는다.

## 이전 버전 보존·재현

[복원 지도](3D/versions/restore_map_r01.json)는 이전 95파일을 `archive:` / `current:`로 구분한다. 덮어쓸 61파일은 SHA256 기반 비중복 [7z](3D/versions/spider_pardosa_previous_r01.7z)에 보관했다. 별도 폴더에서 7z 검사·전체 트리 복원·95파일 해시 일치를 확인했다. r01 Blend·아틀라스 등 기존 버전 파일은 그대로 남겼다.

Blender MCP는 연결 실패로 사용할 수 없었다. Blender 5.3.0의 독립 백그라운드 CLI로 제작·재개방·출력했다. Computer-Use는 사용하지 않았다. 코드와 입력 해시는 제작 기록, 전달 파일 해시는 [delivery_files.json](delivery_files.json)에 있다.

아래 명령은 **에셋의 작업 사본 루트**에서 실행한다. Blender 5.3.0, Python/Pillow/Pygame, Node가 필요하다. 빌더는 그 백그라운드 Blender 장면을 초기화한다.

```powershell
& 'C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe' -b --factory-startup --python-exit-code 1 --python 3D/tools/build_spider.py
& 'C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe' -b 3D/spider_pardosa_idle_r02.blend --python-exit-code 1 --python 3D/tools/verify_style.py
& 'C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe' -b 3D/spider_pardosa_idle_r02.blend --python-exit-code 1 --python 3D/tools/export_idle.py
python 3D/tools/package_idle.py
node 3D/tools/verify_preview.mjs
python 3D/tools/verify_bundle.py
python 3D/tools/compare_assets.py ../../..
python 3D/tools/benchmark_idle.py
```
