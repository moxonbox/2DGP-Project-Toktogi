"""Record the additive B r02 release without rewriting r01 production history."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PROD=ROOT/'_production/r02'
CONFIG=json.loads((PROD/'assets.json').read_text(encoding='utf-8'))
CHANGES={
 'B01':'비대칭 볼륨 잎·표면에 붙인 3개 잎맥·곡선 단일 뿌리·뿌리 싸개를 보완했다.',
 'B02':'7개 표면 잎맥·7개 곡선 뿌리와 끝마개·자주색 아랫면을 보완했다. 35mm 뿌리의 길이비를 유지했다.',
 'B03':'무근 타원체를 더 도톰하게 만들고 윗면을 살짝 평평하게 조정했다. 두께 0.44×길이는 각색이다. 뿌리·털·맥은 없다.',
 'B04':'한 쌍의 오목한 잎·주맥/측맥·잎당 8무리×3가닥 곡선 털·입체 분지 수중 잎을 보완했다. 털 수와 수중 잎 크기는 각색이며 수중 잎은 뿌리가 아니다.',
 'B05':'곡선 줄기·둥근 마디 접합·2회 갈라지는 잎을 보완했다. 5BU 절편·4마디·마디당 6잎은 제작값이다.',
 'B06':'꽃이삭 끝을 둥글게 하고, 도톰한 곡선 띠잎·잎집·세로 무늬를 보완했다.',
 'B07':'타원 알갱이 꽃차례를 가는 가지와 깃털형 작은 이삭으로 바꾸고 마디·잎집을 보완했다.',
 'B08':'연속된 화살형 잎·마디집·아래 가시·굽은 꽃자루·입체 꽃잎/꽃받침을 보완했다.',
 'B09':'분리된 평판 층을 하나의 요철 퇴적층 메시로 바꾸고 불규칙 자갈·굽은 잔가지·작은 입자를 보완했다.',
 'B0A':'얇은 요철 막·낮은 군집·고정 얼룩과 가변 투명도를 보완했다. Alpha 상한은 178/255이며 외곽선은 없다.',
 'B0B':'8개 장식 껍질의 외곽 테두리·줄무늬·형태 차이를 보완했다. 종 동정용이 아닌 현미경 전용 개념도다. Alpha 상한 216/255, 무외곽선.'}
SCALE={
 'B01':'엽상체 2.5×1.6mm, 연출 계수 1. 뿌리 0.90BU는 제작값이다.',
 'B02':'엽상체 6×5mm·뿌리 35mm, 연출 계수 1. 긴 뿌리를 셀에 맞춰 줄이지 않는다.',
 'B03':'엽상체 1.0×0.7mm, 연출 계수 1.',
 'B04':'한 부유 잎 10×6mm, 연출 계수 1. 잎 쌍 전체 길이와 구분한다.',
 'B05':'확정 생물 길이는 null. 제작 절편 명목 길이 5BU.',
 'B06':'높이 1200mm × 연출 계수 0.006 → 6.9508512BU. 원거리 배경이며 같은 지지면의 실측 비례 비교 대상은 아니다.',
 'B07':'높이 2000mm × 연출 계수 0.0045 → 8.688564BU. 원거리 배경이다.',
 'B08':'원문 1000mm는 뻗는 줄기 길이. 계수 0.008 → 7.723168BU 모듈 폭 대용값이며 실측 직선 폭이 아니다.',
 'B09':'입경·퇴적 두께 미선정. 명목 폭 6BU는 설계값이며 발판/충돌체가 아니다.',
 'B0A':'면적·두께·종조성 실측은 null. 명목 폭 3BU는 제작값이다.',
 'B0B':'종·세포 치수·실세계 배율 미확정. 명목 폭 3BU를 세포 길이비로 해석하지 않는다.'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


def finalize():
    runtime=json.loads((PROD/'runtime_validation.json').read_text(encoding='utf-8'))
    direction=json.loads((PROD/'direction_validation.json').read_text(encoding='utf-8'))
    assert runtime['cells']==165 and direction['status']=='PASS'
    rows=[];originals={}
    for c in CONFIG:
        d=ROOT/c['folder'];name=c['name'];code=c['id']
        model=json.loads((d/'3D/model_manifest_r02.json').read_text(encoding='utf-8'))
        m=json.loads((d/'2D/background-r02/manifest.json').read_text(encoding='utf-8'))
        v=json.loads((d/'2D/background-r02/validation.json').read_text(encoding='utf-8'))
        assert len(m['views'])==15 and model['triangles']<=20000
        m['status']['standalone_loader']='verified_separately';save(d/'2D/background-r02/manifest.json',m)
        views='\n'.join(f'| {key} | {cell["cell"]} | {cell["bbox"]} | {v["views"][key]["margin"]} |' for key,cell in m['views'].items())
        text=f'''# {code} 정적 배경 제작 계약 r02

2026-11-17 · AssetPipeLine v2.3 · `background-r02` · 모델·디테일·다시점 보완.

{CHANGES[code]}

{SCALE[code]}

- [r01 제작 계약](production_contract_r01.md)의 생물 근거·시트 검토·미정 값은 유지한다. 위 r02 변경이 충돌하는 제작값보다 우선한다. 원본 생물 문서 3개는 수정하지 않았다.
- [r01 GPT 시트](../sheet/{name}_sheet_r01.png)를 참조한 편집 가능 메시를 수정했다. 이번에는 GPT 시트를 새로 생성하지 않았다. [r02 15시점 검수판](../sheet/{name}_blender_reference_r02.png)은 같은 저장 모델에서 만든 후속 출력이다.
- `{name}` / `{c['folder']}`의 `_`와 기존 철자를 보존한다. 정적 `static/static`, sample 0, hold, duration null. 본·리그·애니메이션·이벤트·충돌·먹이·부력은 없다.
- 기준 개체는 S. aquaticus 암컷 성체 최대 1mm. C011 몸 대용값 0.965396BU × 길이비 × 연출 계수. BU를 생물학적 m/mm로 선언하지 않는다. 크기·기관 수 미측정 값을 제작값으로 확정하지 않는다.
- 목표 기준 길이 {model['length_bu']:.8f}BU. 전체 외접 범위·앵커는 [모델 manifest](../3D/model_manifest_r02.json), `measure_kind={c['measure_kind']}`. 고정 밀도 128/1.78 px/BU, 게임 1×. 모든 셀을 128²로 줄이지 않는다.
- 톡토기와 같은 고정 카메라 Euler 및 월드 +Z yaw를 사용한다. `left=0`, 순환 yaw 45° 간격 8방향, 별도 호환 `right=2.00151174696589rad`. right와 yaw_180은 다르다. `ortho_*` 6개는 정투영 검수 전용이다. r01의 정투영 `left/right`와 r02 게임 방향의 의미를 혼용하지 않는다.
- 메시·Normal·모든 앵커를 함께 회전해 재출력한다. mirror false. 픽셀 피벗은 크롭에 따라 달라지지만 같은 모델 원점을 가리킨다. [독립 투영 검증](../../_production/r02/direction_validation.json)
- {model['triangles']:,}삼각형 / {model['mesh_count']}메시 / 0본. 예산 20,000삼각형·512² 기본색·셀 한 변 최대 4096px·최소 여백 8px. 둥근 기관의 접합에는 의도한 메시 겹침이 있다. 용접된 3D 충돌체 보증은 없다.
- 종별 팔레트는 모델 manifest `palette_roles`에 저장한다. 16개 UV 역할 타일·4% 내부 여백·의도한 역할 재사용·고정 얼룩·선형 bilinear UV 표본을 사용한다. 얇은 선은 픽셀 해상도에 따라 일부 간헐적으로 보일 수 있다.
- Sprite는 C011 4단 광원 배율 뒤 역할당 13색으로 양자화한다. r01의 역할당 4색보다 약한 표면 무늬가 남는다. 고유 식물색 유지, 디더·AA·mipmap 없음, 확대 Nearest. Sprite에만 #22313B 반경 2px 외곽선. B0A/B0B는 무외곽선·반투명이다.
- W×(H×5) PNG의 순서는 Sprite/Base/Normal/RM/Emissive. Base는 무조명 sRGB, 데이터 패스 A=255, Base A로 마스크한다. Normal은 카메라 R 오른쪽·G 위·B 카메라 방향. 발광 RGB=0. 모든 패스가 같은 셀·피벗·포즈·크롭이다.

| 방향 | 셀 W,H px | Sprite bbox | 최소 여백 px |
|---|---|---|---|
{views}

- [저장본·UV·출력 검사](../2D/background-r02/validation.json) · [2D manifest](../2D/background-r02/manifest.json) · [UV left](../2D/background-r02/review/uv_checker_left.png) · [UV top](../2D/background-r02/review/uv_checker_ortho_top.png)
- 저장 Blend 재개방·packed/외부 이미지 해시·유한 UV·비퇴화 삼각형·기관 수·15시점 5패스·여백·Normal 길이 검사 통과. 독립 번들 165셀/9종 오류 거부 검사 통과.
- Blender MCP 연결 실패로 설치된 Blender 5.3.0 CLI를 사용했다. Computer-Use는 사용하지 않았다. 본게임/Pico2D 연결·SDL 업로드·최종 장치 성능·DEC-06은 보류다.
- r01 모델/출력/ZIP은 원래 경로에 그대로 보존한다. 삭제·이동이 없어 7z 중복 정리를 하지 않았다. 이전 색인은 ASSET_INDEX_r01.md로 보존하고 최신 색인만 바꾼다.
'''
        (d/'document/production_contract_r02.md').write_text(text,encoding='utf-8')
        (d/'ASSET_INDEX.md').write_text(f'''# {code} — {name}

2026-11-17 · **background-r02: 모델·디테일 보완 / 톡토기 9방향 + 정투영 6방향**

{CHANGES[code]}

- [제작 계약](document/production_contract_r02.md) · [Blender 원본](3D/{name}_r02.blend) · [모델/크기/팔레트](3D/model_manifest_r02.json)
- [15시점 검수판](sheet/{name}_blender_reference_r02.png) · [left Sprite](2D/background-r02/previews/left.png) · [2D manifest](2D/background-r02/manifest.json) · [검증](2D/background-r02/validation.json)
- [r02 공통 번들·검증·재현](../_production/r02/README.md) · [이전 r01 색인](ASSET_INDEX_r01.md) · [전체 B 목록](../ASSET_INDEX.md)

정적 제작·독립 번들 검증 완료. 본게임/Pico2D·실기 성능은 미검증이다.
''',encoding='utf-8')
        rows.append(f'| [{code}]({c["folder"]}/ASSET_INDEX.md) | {name} | {model["triangles"]:,} | {m["views"]["left"]["cell"]} | 15 |')
        for p in (d/'document').glob('*.md'):
            if not p.name.startswith('production_contract_'):originals[p.relative_to(ROOT).as_posix()]=sha(p)
        own=[p for p in d.rglob('*') if p.is_file() and (p.name.endswith('_r02.blend') or '_r02.' in p.name or 'background-r02' in p.parts or p.name=='ASSET_INDEX.md') and p.name!='asset_files_r02.json']
        save(d/'asset_files_r02.json',{'revision':'background-r02','files':{p.relative_to(d).as_posix():sha(p) for p in own}})
    assert len(originals)==33
    (ROOT/'ASSET_INDEX.md').write_text('''# B 배경 에셋 — r02

2026-11-17 · 11종 모델·디테일 보완, 165 정적 셀(각 5패스).

[전체 미리보기](_production/r02/overview.png) · [r01/r02 비교](_production/r02/before_after.png) · [톡토기 9방향 1× 비교](_production/r02/c011_directions_1x.png)

[공통 계약·번들·검증·재현](_production/r02/README.md) · [이전 r01 색인](ASSET_INDEX_r01.md)

| 에셋 | 이름 | 삼각형 | left 셀 px | 시점 |
|---|---|---:|---|---:|
'''+ '\n'.join(rows)+'\n\n정적 제작·독립 번들 검증 완료. 본게임/Pico2D 연결·실기 성능·DEC-06은 보류. r01 모델·출력·원본 문서는 보존했다.\n',encoding='utf-8')
    changes='\n'.join(f'- {code}: {note}' for code,note in CHANGES.items())
    (PROD/'README.md').write_text(f'''# B 정적 배경 r02 인계

2026-11-17 · AssetPipeLine v2.3 / AssetSize 기준 · 11종 모델·디테일·시점 보완.

{changes}

- 편집 가능한 Blend 11개, 종당 15뷰/5패스, 총 165셀. 8개 순환 yaw + 별도 right가 톡토기 카메라와 일치한다. 6개 `ortho_*`는 검수 전용이다. [원본 방향 계약](reference/c011_view_contract.json)의 DEC-06 보류 상태는 해제하지 않았다.
- [전체 색인](../../ASSET_INDEX.md) · [미리보기](overview.png) · [전후 비교](before_after.png) · [톡토기 9방향 1×](c011_directions_1x.png) · [고정 장면 1×](comparison_1x.png) · [회색조](comparison_grayscale_1x.png) · [이동 광원 A](comparison_light_260.png) / [B](comparison_light_680.png)
- [ZIP](backgrounds_r02.zip) / [잠금](backgrounds_r02.source.json). 독립 [로더](tools/background_bundle.py)는 직사각형 셀·straight Alpha·8셀 LRU·피벗을 지원한다. `maps(asset_id, view='left')`, `draw(canvas, asset_id, world_position, camera=(0,0), view='left')`. B0B는 월드 draw를 거부하고 별도 현미경 maps만 허용한다.
- [런타임 검사](runtime_validation.json): 165셀 5패스 일치, 9종 잘못된 입력 거부. 120프레임/4개 배경 CPU 합성 p95 {runtime['p95_composite_ms']:.3f}ms, 최대 {runtime['max_composite_ms']:.3f}ms. [방향 검사](direction_validation.json): 앵커 {direction['anchors_checked']}개, 최대 오차 {direction['maximum_anchor_error_px']:.8f}px < 0.002px.
- 전체 방향을 모두 RGBA로 디코딩하면 {runtime['decoded_rgba_bytes_all_views']:,}bytes ({runtime['decoded_rgba_bytes_all_views']/1048576:.1f}MiB). ZIP은 {runtime['bundle_bytes']:,}bytes. 긴 B02 뿌리·B04 잎 쌍의 높은 해상도가 주요 비용이다. 전체 선로딩을 권장하지 않으며 8셀 캐시도 실기 메모리 예산 합격을 뜻하지 않는다.
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
''',encoding='utf-8')
    save(PROD/'source_documents.json',{'original_B_documents':originals,'reference_snapshots':{p.name:sha(p) for p in (PROD/'reference').iterdir() if p.is_file()}})
    save(PROD/'tool_execution.json',{'date':'2026-11-17','revision':'background-r02','blender':'5.3.0','mcp':'Cannot connect to Blender at 127.0.0.1:9876','fallback':'installed Blender background CLI','computer_use':False,'image_generation':'existing r01 sheets reused; no new generation','visual_review':['overview.png','before_after.png','c011_directions_1x.png','per-asset 15-view boards'],'status':'production_and_standalone_verified; main game deferred'})
    files={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.blend1') and p!=PROD/'release_files.json'}
    save(PROD/'release_files.json',{'revision':'background-r02','files':files})
    print(json.dumps({'assets':len(CONFIG),'release_files':len(files),'original_documents':len(originals)}))


if __name__=='__main__':finalize()
