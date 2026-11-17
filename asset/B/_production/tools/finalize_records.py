"""Write the production contracts and immutable source/file inventories."""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT.parents[1]
PROD=ROOT/'_production'
CONFIG=json.loads((PROD/'assets.json').read_text(encoding='utf-8'))

NOTES={
 'B01':'엽상체 2.5×1.6mm를 범위 안에서 선택했다. 뿌리 1개와 싸개 날개를 유지했다. 뿌리 길이 0.90BU·굵기는 제작값이며 생물 실측이 아니다.',
 'B02':'엽상체 6×5mm, 뿌리 35mm를 원문 범위 안에서 선택했다. 뿌리 7개·맥 7개·자주색 아랫면을 구현했다. 긴 뿌리를 셀 크기에 맞춰 축소하지 않는다.',
 'B03':'엽상체 1.0×0.7mm를 범위 안에서 선택했다. 뿌리·털·맥·줄기는 없다. 두께 0.32×길이는 카툰 제작값이다.',
 'B04':'한 부유 잎 10×6mm를 선택했다. 잎 2개·짧은 연결 줄기·분지된 수중 잎을 구현했다. 수중 잎은 진짜 뿌리가 아니다. 수중 잎 길이와 털 15개/잎은 표현용 설계값이다.',
 'B05':'원문에 공통 확정 길이가 없어 생물 길이는 null로 유지한다. 5BU 절편, 4개 마디, 마디당 6개 2회 분지 잎은 제작 선택이다. 뿌리는 없다.',
 'B06':'성체 높이 1200mm를 범위 안에서 선택하고 원거리 배경 연출 계수 0.006을 적용한다. 높이 6.9508512BU. 잎 6개와 원통형 꽃이삭을 구현했다. 같은 지지면 위 실측 배율 비교에 사용하지 않는다.',
 'B07':'성체 높이 2000mm를 범위 안에서 선택하고 원거리 배경 연출 계수 0.0045를 적용한다. 높이 8.688564BU. 마디·어긋나는 잎·분지된 원뿔꽃차례를 구현했다. 꽃차례의 작은 이삭은 저면수 타원체로 단순화했다.',
 'B08':'약 1000mm는 원문의 뻗는 줄기 길이이며 모델의 직선 폭과 같지 않다. 연출 계수 0.008로 7.723168BU 모듈 폭을 정한 대용 표현이다. 잎 크기는 실측하지 않았다. 아래로 향하는 가시·각진 줄기·분홍 꽃을 구현했다.',
 'B09':'입경·퇴적층 두께·장소가 미선정이다. 6BU 명목 폭의 바닥 모듈과 자갈 6개는 설계값이다. 수면이나 톡토기 보행 발판으로 등록하지 않는다.',
 'B0A':'막의 실측 두께·면적·종조성은 null이다. 3BU 명목 폭·0.012BU 두께의 편집 가능한 부착층을 만들었다. Alpha 178/255·무외곽선은 얇은 막의 표현 선택이다. 식용 여부를 부여하지 않는다.',
 'B0B':'종·세포 치수와 실세계 배율은 미확정이다. 3BU 패턴은 현미경 검수 전용 개념 모듈이며 세포 길이비가 아니다. Alpha 216/255·무외곽선을 사용한다. 런타임 draw는 일반 월드 배치를 거부한다.'}

SHEET_NOTES={
 'B01':'생성 시트의 정면/측면 폭은 정밀 투영이 아니다. 치수와 단일 뿌리 계약을 우선하고 Blender 정투영 시트로 최종 방향을 교체한다.',
 'B02':'생성 그림의 뿌리 35mm 치수선과 화면 비례가 일치하지 않는다. 6mm 엽상체와 35mm 뿌리 수치를 모델에 직접 적용한다. 시트에서 겹친 측면 뿌리는 삭제하지 않는다.',
 'B03':'생성 시트의 top/underside에도 비스듬한 음영이 있다. 실제 모델은 단일 무근 타원체이며 정투영 출력이 방향의 기준이다.',
 'B04':'생성 시트 상면의 수중 잎은 설명용 펼침이다. 모델에서는 잎 쌍 아래로 수중 잎을 배치한다. 털은 확대도처럼 전면을 덮지 않도록 단순화한다.',
 'B05':'생성 시트의 겹친 잎 수를 세어 생물 형질로 확정하지 않는다. 4마디·6돌려남·2회 분지를 제작 계약으로 고정한다.',
 'B06':'생성 시트의 일부 underside 라벨은 기부 정면 그림에 붙어 있다. Blender underside는 실제 아래에서 본 뷰로 대체한다. 꽃이삭·잎 수는 계약값을 따른다.',
 'B07':'시트의 가는 꽃차례 세부를 모두 복제하지 않는다. 원뿔 외곽과 분지 구조를 유지하고 작은 이삭을 저면수로 축약한다.',
 'B08':'생성 시점별 잎·꽃 수 차이는 실측 근거가 아니다. 하나의 줄기·5개 잎 모듈·양끝 꽃 무리·5개 아래 가시로 고정하고 모든 뷰를 같은 메시에서 출력한다.',
 'B09':'한 메시의 층과 자갈 6개를 모든 뷰가 공유한다. 생성 시트의 그림자와 갈색 명암은 별도 지오메트리로 복제하지 않는다.',
 'B0A':'생성 시트의 불투명 바탕은 제작 배경이다. 실제 출력은 부착층만 반투명하게 저장한다. 군집 점은 종 식별 구조가 아니다.',
 'B0B':'그림은 종 동정 자료가 아니다. 장식 타원·길쭉한 껍질 모티프를 현미경 개념도로만 채택한다. 생성 이미지의 픽셀 크기를 mm로 변환하지 않는다.'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


def finalize():
    runtime=json.loads((PROD/'runtime_validation.json').read_text(encoding='utf-8'))
    rows=[];originals={};sources={}
    for config in CONFIG:
        folder=config['folder'];name=config['name'];code=config['id'];base=ROOT/folder
        model=json.loads((base/'3D/model_manifest.json').read_text(encoding='utf-8'))
        manifest=json.loads((base/'2D/manifest.json').read_text(encoding='utf-8'))
        validation=json.loads((base/'2D/validation.json').read_text(encoding='utf-8'))
        for path in sorted((base/'document').glob('*.md')):
            if path.name!='production_contract_r01.md':originals[path.relative_to(ROOT).as_posix()]=sha(path)
        generation={'date':'2026-11-17','tool':'image_gen.imagegen','mode':'built-in',
                    'model_identifier':None,'seed':None,'prompt':config['prompt'],
                    'input_spec':f'../document/{name}_model.md','input_spec_sha256':sha(base/f'document/{name}_model.md'),
                    'style_reference':'../../_production/reference/C011_idle.png',
                    'style_reference_sha256':sha(PROD/'reference/C011_idle.png'),
                    'style_input_delivery':'Reference displayed in conversation; new-image call omitted explicit image-path arguments.',
                    'output':f'{name}_sheet_r01.png','output_sha256':sha(base/f'sheet/{name}_sheet_r01.png'),
                    'review':'conditional_reference_with_production_spec_corrections','correction':SHEET_NOTES[code],
                    'selection_reason':'생물 명세의 큰 형태와 프로젝트 카툰 톤 참고. 실제 정투영·기관 수는 제작 계약과 Blender 출력이 우선한다.',
                    'license_note':'내장 생성 도구 산출물. 외부 사진·외부 모델을 복제하거나 새로 배포하지 않았다. 원자료의 법적 권리는 별도 검토하지 않았다.'}
        save(base/'sheet/generation_r01.json',generation)
        manifest['status']['standalone_loader']='verified_separately'
        save(base/'2D/manifest.json',manifest)
        cell=manifest['views']['game']['cell']
        rows.append(f'| [{code}](../{folder}/ASSET_INDEX.md) | {name} | {model["triangles"]:,} | {cell[0]}×{cell[1]} | {config["scale_policy"]} |')
        views='\n'.join(f'| {view} | {v["cell"][0]}×{v["cell"][1]} | {v["bbox"]} | {validation["views"][view]["margin"]} |' for view,v in manifest['views'].items())
        contract=f'''# {code} 정적 배경 제작 계약 r01

2026-11-17 · AssetPipeLine v2.3 적용 · 기존 외형/동작 문서의 제작 보충 계약이다.

## 적용 범위

- `asset_id={name}`, 폴더 `{folder}`, revision `background-r01`. `_`와 기존 철자를 보존한다.
- B 분류의 정적 배경 1 variation만 채택한다. 바람·부유·군락 변화·성장·탁도는 미채택 설계안이며 플레이 이벤트·충돌·발판·먹이 판정은 없다.
- 정적 `static/static`, sample 0, phase mid, 무기한 hold. 시간은 null이며 애니메이션의 0초 클립이 아니다. 리그·Action·NLA·본·모션 HTML은 불필요하다.

## 크기·생물 근거와 각색

{NOTES[code]}

- S. aquaticus 암컷 성체 최대 1.0mm를 비교 기준으로만 쓴다. `0.965396BU`는 C011의 제작용 몸길이 대용값이다. BU를 생물학적 m나 mm로 선언하지 않는다.
- 선택 길이: `{config['selected_length_mm']}`mm; 연출 계수: `{config['presentation_factor']}`; 측정 종류: `{config['measure_kind']}`.
- 기준 길이 `{model['length_bu']:.8f}`BU와 전체 외접 범위 `{model['bounds_bu']}`는 별개다. 폭·높이·뿌리·질량·충돌을 체장비로 자동 추정하지 않는다.
- 축 +X는 잎/모듈 길이, +Z는 위다. 원점은 물선 또는 줄기 기부/기질면이다. 기준점은 [모델 manifest](../3D/model_manifest.json)의 `anchors_bu`에 보존한다.

## 시트와 모델 결정

{SHEET_NOTES[code]}

- [생성 기록](../sheet/generation_r01.json)에 원 프롬프트·생성일·도구·입력/출력 해시를 기록했다. 모델명·seed는 제공되지 않아 null이다.
- 신규 GPT 시트 이후 편집 가능한 메시를 만들었다. 시트를 평면에 붙인 모델이 아니다. 저장 Blend의 숨긴 참조 Empty에는 원본 시트를 패킹했다.
- [Blender 7방향 시트](../sheet/{name}_blender_reference_r01.png)는 모델에서 만든 후속 검수본이다. 표시용 맞춤 축소 시트이며 실측 비례표가 아니다.
- 검사값: {model['triangles']:,}삼각형 / {model['mesh_count']}메시 / 0본. 예산 20,000삼각형, 단일 512² 기본색 텍스처, 최대 셀 변 4096px, 투명 여백 하한 8px.
- 의도한 기관/줄기 접합은 겹치는 메시를 사용한다. 비다양체 용접 모델이나 3D 충돌체로 보증하지 않는다. 숨은 면은 잘못 제거하지 않도록 유지했다.

## 색·UV·출력

- 종별 녹색·갈색·자주색·분홍색 역할은 [모델 palette_roles](../3D/model_manifest.json)에 기록했다. 사진에서 실측한 HEX가 아니다.
- UV 재질별 16타일·내부 여백 4%·의도한 타일 재사용, 약한 고정 무늬, bilinear UV 보간을 사용한다. 프레임별 노이즈·디더·AA·mipmap은 없다.
- [UV 게임 뷰](../2D/review/uv_checker_game.png) / [상면](../2D/review/uv_checker_top.png). 얇은 부품은 무늬보다 실루엣을 우선한다. 실측 텍셀 밀도나 비대칭 무늬용 UV가 아니다.
- C011 camera Euler `(1.195510983467102,0,-0.5700404644012451)`, `1.78/128 BU/px`, game 1×, Nearest, mirror false. 여섯 정투영 검수 방향을 추가했다.
- 4단 명암과 역할별 팔레트, Sprite 전용 `#22313B` 반경 2px 외곽선. B0A/B0B는 부착층 표현상 외곽선을 생략하며 반투명 Alpha를 유지한다.
- 개별 PNG는 폭 W·높이 H×5에 Sprite/Base/Normal/RM/Emissive 순서로 적층한다. Base는 무조명 sRGB, Normal/RM/Emissive는 선형 데이터·A=255이며 Base A로 마스킹한다. 발광 RGB는 0이다.
- 아틀라스 대신 단일 셀 패스 PNG와 적층 PNG를 대응시켰다. `rect=[0,0,W,H]`, 패딩 0. 셀 내부 여백과 별개이며 trim/회전은 하지 않는다.

| 방향 | 셀 px | Sprite bbox | 최소 여백 px |
|---|---|---|---|
{views}

## 검증·보류

- 저장본 재개방, 외부/packed 이미지 해시, UV 유한성·범위, 비퇴화 삼각형, 뿌리 수, 7방향·5패스 정합·여백·Normal 길이를 새로 검사했다. [기록](../2D/validation.json)
- 독립 ZIP 로더와 손상 입력 검사는 [공통 runtime_validation](../../_production/runtime_validation.json)을 따른다. 셀·뷰·피벗·앵커와 해시가 같은 revision이다.
- Blender MCP 연결·CLI MCP가 시간 초과되어 설치된 Blender 5.3.0의 직접 CLI로 제작했다. Computer-Use는 사용하지 않았다.
- 본게임/Pico2D 연결·SDL 업로드·최종 장치 60fps·DEC-06 확정은 보류다. 독립 CPU 합성 검사만으로 게임 사용 완료를 선언하지 않는다.
- 3D 이전본이 없으므로 versions/7z는 만들지 않았다. FBX 인계 요구가 없어 .blend를 원본으로 보존한다.
'''
        (base/'document/production_contract_r01.md').write_text(contract,encoding='utf-8')
        index=f'''# {code} — {name}

2026-11-17 · background-r01 · **정적 에셋 제작·독립 번들 검증 완료 / 본게임 연결 보류**

{NOTES[code]}

- [제작 계약](document/production_contract_r01.md) · [기존 외형 명세](document/{name}_model.md) · [기존 동작 후보](document/{name}_movement.md)
- [편집 가능한 Blender](3D/{name}_r01.blend) · [모델/크기/팔레트](3D/model_manifest.json) · [기본색 텍스처](3D/textures/{name}_basecolor_r01.png)
- [GPT 시트](sheet/{name}_sheet_r01.png) · [프롬프트·입력·해시](sheet/generation_r01.json) · [Blender 정투영 검수 시트](sheet/{name}_blender_reference_r01.png)
- [게임 방향 Sprite](2D/previews/game.png) · [5패스 적층 셀](2D/static/static/game/0.png) · [2D manifest](2D/manifest.json) · [저장본/출력 검사](2D/validation.json)
- [공통 번들·재현·검증](../_production/README.md) · [전체 에셋 목록](../ASSET_INDEX.md)

기관·재질·픽셀 보정의 기준은 제작 계약이다. 기존 생물 자료의 미정 수치를 이번 제작값으로 덮어쓰지 않았다.
'''
        (base/'ASSET_INDEX.md').write_text(index,encoding='utf-8')
        produced={p.relative_to(base).as_posix():sha(p) for p in base.rglob('*') if p.is_file() and p.name!='asset_files.json'}
        save(base/'asset_files.json',{'asset_id':name,'revision':'background-r01','files':produced})
    save(PROD/'source_documents.json',{'original_B_documents':originals,'reference_snapshots':{p.name:sha(p) for p in (PROD/'reference').iterdir() if p.is_file()}})
    save(PROD/'tool_execution.json',{'date':'2026-11-17','image_generation':'11 built-in calls; no seed/model identifier returned',
         'blender_mcp':[{'tool':'get_blendfile_summary_path_info','result':'Cannot connect to Blender at 127.0.0.1:9876'},
                        {'tool':'get_blendfile_summary_path_info','result':'Blender connection timed out at 127.0.0.1:9876'},
                        {'tool':'execute_blender_code','result':'Blender connection timed out at 127.0.0.1:9876'},
                        {'tool':'get_blendfile_summary_path_info_for_cli','result':'Blender CLI timed out after 120s'}],
         'fallback':'Direct installed Blender CLI 5.3.0 --background; clean factory scenes only',
         'computer_use':False,'source_reuse':{'png_codec.py':'C261 3D/tools/png_codec.py; originally C011 codec',
                                            'raster':'C261 export_fish.py rectangular adaptation',
                                            'shared_lighting.py':'C211 r02 shared_lighting.py unchanged'},
         'warnings':'Sandbox denied Blender thumbnail/extensions cache writes; .blend, PNG and packed image checks passed.'})
    table='\n'.join(rows)
    readme=f'''# B 배경 에셋 제작 r01

2026-11-17 · [AssetPipeLine v2.3 원문 스냅샷](reference/AssetPipeLine.md) · [AssetSize v1.1](reference/AssetSize.md)

11종 정적 배경을 제작했다. GPT 시트 11장, 편집 가능한 .blend 11개, Blender 검수 시트 11장, 7방향 × 11종 = 77셀, 셀당 5패스다. 독립 번들 검증은 통과했고 본게임 연결은 보류다.

| ID | 논리 ID | 삼각형 | 게임 방향 셀 px | 크기 정책 |
|---|---|---:|---|---|
{table}

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
- 전 방향 RGBA 원본 {runtime['decoded_rgba_bytes_all_views']:,}byte, ZIP {runtime['bundle_bytes']:,}byte. 로더는 최대 8셀 LRU다. 런타임에 전 방향을 동시에 올리지 않는다.
- 정적 배경 4개·960×560·120프레임 Pillow CPU 합성 p95 {runtime['p95_composite_ms']:.3f}ms, 최대 {runtime['max_composite_ms']:.3f}ms. 셰이딩·SDL 업로드·게임 전체 16.7ms 예산의 측정은 아니다.
- 동일 power 0.82·ambient 0.34·두 월드 광원 위치에서 C011과 B를 합성했다. 반투명 및 색상/회색조 검수판을 보존했다.

## 보류·차이

- Blender MCP/CLI MCP가 연결 실패·시간 초과되어 직접 CLI를 사용했다. [관찰 기록](tool_execution.json). Computer-Use는 사용하지 않았다.
- GPT 다면 시트에는 일부 원근·겹침·치수선 비례가 남는다. 에셋별 보충 계약에서 해당 차이를 수정 규칙으로 고정하고 같은 메시의 Blender 정투영을 후속 기준으로 남겼다. 시트에 존재하지 않는 생물 사실을 만들지 않았다.
- 본게임/Pico2D·StageLevel의 두 Level·충돌 발판·SDL 성능·DEC-06·실기 승인은 미완료다. 이번 결과는 별도 정적 배경 묶음이며 기존 C011 실행 번들을 교체하지 않는다.
- UV는 저대비 반복 기본색용이다. 비대칭 고해상도 페인팅·수치 기반 텍셀 밀도 검수·일반 3D 물리용 용접/관통 검사는 수행하지 않았다.
- 이전 3D 파일이 없어 7z 복원 지도는 해당 없음. FBX·추가 variation·바람/부유 모션·Bloom은 제작하지 않았다.
'''
    (PROD/'README.md').write_text(readme,encoding='utf-8')
    (ROOT/'ASSET_INDEX.md').write_text('# B 배경 에셋 색인\n\n2026-11-17 · background-r01 · 11종 정적 제작·독립 검증 완료. 본게임 연결 보류.\n\n[산출물·미리보기·재현·검증·보류 사항](_production/README.md)\n\n| ID | 논리 ID | 삼각형 | 게임 방향 셀 px | 크기 정책 |\n|---|---|---:|---|---|\n'+table.replace('(../','(')+'\n',encoding='utf-8')
    for c in CONFIG:c.pop('generated_source',None)
    save(PROD/'assets.json',CONFIG)
    files={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='release_files.json'}
    save(PROD/'release_files.json',{'revision':'background-r01','files':files})
    assert len(originals)==33
    print(json.dumps({'assets':len(CONFIG),'original_documents':len(originals),'release_files':len(files)},ensure_ascii=False))


if __name__=='__main__':finalize()
