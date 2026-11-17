"""Write handoff records and a hash-locked, independently restorable r01 bundle."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PROJECT=Path(r'C:\Users\user\Desktop\BEng_Work\022_2D_PyGame\2DGP-Project-Toktogi')
configs=json.loads((HERE/'assets.json').read_text(encoding='utf-8'))
validation=json.loads((HERE/'validation.json').read_text(encoding='utf-8'))
saved=json.loads((HERE/'saved_validation.json').read_text(encoding='utf-8'))
assert len(saved)==7 and validation['cell_count']==49
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
notes=[
 '단독 엽상체를 고체 발판 제작 후보로 채택했다. 엽상체 1개에 뿌리 1개와 작은 뿌리골무가 있다. 3개의 희미한 맥은 UV 고정 무늬다. 생성 시트의 FRONT/BACK은 위에서 본 설명 그림이므로 축 기준 도면으로 채택하지 않았다. TOP·LEFT·RIGHT의 납작한 형상과 단일 뿌리를 채택하고, 실제 축별 도면은 Blender 출력으로 교정했다.',
 '연속 수면의 정적 시각 모듈이다. 면의 Normal을 평탄하게 유지하며 약한 무늬는 UV에 고정했다. 두께 0.024×C011 BU는 측면 가독성을 위한 제작값이다. 수심·부력·투명도·표면장력의 실측값이 아니다. 상면 색상 텍스처는 반복 가능하지만 게임 투영 셀의 배치 이음새는 미검증이다. 수면은 자동 충돌면이 아니다.',
 '완만한 경사 모듈과 자갈 4개, 작은 웅덩이 1개를 채택했다. 수면 접합 기준은 낮은 끝의 waterline이다. 시트의 유기적 외곽보다 모듈 경계를 단순하게 제작했다. 경사 IK와 실제 물가 연결 충돌은 미검증이다.',
 '고정된 젖은 가지를 채택했다. 몸체·분지·마디·밝은 절단면이 편집 가능한 메시다. 분지는 몸체에 겹쳐 접합하며 내부 면을 삭제하지 않았다. 이 겹침은 정적 소품의 의도한 접합이다. 부유형과 고정형을 혼합하지 않는다.',
 '넓은 윗면을 가진 고정 돌 1개를 채택했다. 둥근 모서리와 낮은 대비의 UV 무늬, 낮은 부분의 젖음 띠를 사용한다. 시트의 작은 균열은 실루엣과 게임 판정에 필요하지 않아 생략했다. 광물 조성·마찰은 미확정이다.',
 '고정된 낙엽 1개를 채택했다. 두께가 있는 메시·말린 가장자리·작은 찢김·UV 잎맥을 적용했다. 식물 종과 실제 두께는 미확정이다. 먹이 또는 자율 이동 객체로 등록하지 않는다.',
 '표면에 부착된 얇은 패치를 채택했다. 큰 식물·이끼 잎·뿌리를 생성하지 않았다. 생성 시트의 FRONT/BACK을 면 형태 참고, TOP을 얇은 단면 참고로 재해석한다. 세계 +Z 상면 기준 실제 도면은 Blender 출력이다. 소모된 패치 inset은 후속 상태 참고만 하며 이번 출력은 attached_idle 한 상태다.',
]
deferred=[
 'idle_float·water_drift·oviposition_surface는 현행 플레이에서 제외한다. daughter_frond_visual과 어미/딸 variation은 후속 제작으로 보류한다.',
 'contact_ripple은 별도 효과 소유자가 필요하다. level_shift와 수면 상호작용은 보류한다.',
 'wetness_shift·puddle_variation, 실제 경사 충돌·물선 연결·경사 IK는 보류한다.',
 'floating_bob은 현행 부력 제외 범위다. contact_reaction은 환경 이벤트 연결 후 제작한다.',
 'waterline_mask의 동적 변경, 자갈 군집 variation과 충돌 판정은 보류한다.',
 'drift_leaf·wetness_change와 부유형 variation은 보류한다.',
 'feed_visual·regrowth_visual 및 실제 먹이 소모는 게임 자원 권한과 이벤트 연결 전까지 보류한다.',
]
names=['나도좀개구리밥','잔잔한 수면','물가 경사','젖은 가지','젖은 돌','젖은 낙엽','조류 패치']
table=[]
for i,c in enumerate(configs):
    folder=ROOT/c['folder']; obj=c['asset_id']; index=c['folder'].split('_')[0]
    model=json.loads((folder/'3D/model_validation.json').read_text(encoding='utf-8'))
    manifest=json.loads((folder/'2D/environment-r01/manifest.json').read_text(encoding='utf-8'))
    bound=next(x for x in manifest['cells'] if x['view']=='game_left')['bbox']['sprite']
    width,height=bound[2]-bound[0],bound[3]-bound[1]
    production=f'''# {index} {names[i]} — environment-r01 제작 기록

2026-11-17. 정적 제작 후보를 구현·파일 검증했다. 게임 연결·물리 검증과 DEC-06 양산 승인은 완료하지 않았다.

## 채택 범위와 출처

{notes[i]}

- 원본 [외형 명세]({obj}_model.md)·[동작 명세]({obj}_movement.md)·[생태 자료]({obj}.md)는 수정하지 않았다.
- 공통 기준은 [AssetPipeLine v2.3](../../../../document/markdown/AssetPipeLine.md), [AssetSize](../../../../document/markdown/AssetSize.md), [StageLevel](../../../../document/markdown/StageLevel.md), [Rebuild](../../../../document/markdown/Rebuild.md)다.
- [기계 판독 계약](production_contract_r01.json)에 폴더 ID·논리 ID·선택 크기·예산·카메라·재질을 분리했다. 미정인 8자리 번호를 발명하지 않고 `clip/view/000.png`와 manifest 키를 사용한다.

## 크기·색·표시 계약

- 선택 길이 {c['length_ratio']}×C011, 목표 X 길이 {c['length_bu']:.6f} BU. 이는 상대 연출값이다. C011 몸 대용값 0.965396 BU와 카메라 환산 0.01390625 BU/px를 사용한다.
- {'엽상체 길이 3.5 mm와 폭 2.3 mm는 기존 범위 안에서 선택한 제작 기준이며 특정 개체 실측이 아니다. 뿌리 1.3×C011 길이·두께·색은 게임 각색이다.' if i==0 else '생물 길이 mm는 null이다. 모듈 크기를 생물 실측 또는 mm→BU 물리 단위 변환으로 해석하지 않는다.'}
- 출력 {c['cell_size']}×{c['cell_size']}px, 1× Nearest. game_left Sprite 실측 {width}×{height}px. 피벗과 3D 앵커의 투영 좌표는 뷰별 manifest에 있다. 모든 뷰의 Sprite/Base 투명 여백은 최소 8px다.
- 기준색 `{c['color']}`, 거칠기 {c['roughness']}, 금속성 0, 발광 0은 제작 선택값이다. 젖음은 지오메트리를 바꾸지 않는 고정 색/거칠기 마스크다. 실측 PBR로 주장하지 않는다.
- Sprite에는 C011의 네 단계 선형 명암과 자산별 색상 팔레트를 사용한다. 실제 palette_rgb는 뷰별 기록이다. Base는 조명·AO를 굽지 않는다. 디더·AA·mipmap·임의 trim·회전·미러는 사용하지 않는다.
- 외곽선은 {'사용하지 않는다. 수면 모듈 이음새 또는 부착 패치에 검은 테두리를 만들지 않기 위한 예외다.' if i in (1,6) else 'C011과 같은 #22313B, dx²+dy²≤5 확장이다.'}
- 5패스 순서는 Sprite / Base / Normal / RM / Emissive다. Normal·RM·Emissive A=255, coverage는 Base A로 읽는다. AO 별도 베이크는 이번 범위에서 제외하며 소비자 기본값 1을 사용한다. RM B는 예약 0이다.
- Blender 미리보기에는 원본 C011의 AgX·조명 3개·World 설정을 복제했다. CPU Sprite 출력과 게임 연속 재조명은 별도 경로다. [공유 광원 비교판](../2D/environment-r01/shared_light_compare.png)은 기존 게임 lighting.py의 power .82·ambient .34를 사용한다.

## 저장·검증

- 삼각형 {model['triangle_count']}, 본 0. 정적 환경에 불필요한 리그·Action·NLA를 만들지 않았다. 메시는 닫힌 편집용 형상을 유지한다.
- UV는 잎/패치의 XY, 경계면의 평면 투영, 돌의 분리된 섬을 사용한다. 밑면·측면의 반복은 의도적이다. UV 유한값과 저장 후 존재를 검사했다. 체크 타일로 늘어짐을 판정하는 별도 시각 검수는 미실행이다.
- .blend 재개방, 프레임 1/30/12/60/1의 평가 정점 해시 일치, packed 이미지와 외부 PNG 바이트 일치를 확인했다. 상대 이미지 경로를 사용한다.
- 7시점·7셀의 크기·경로·파일 해시·데이터 Alpha·Normal 길이·외접 범위·투명 RGB를 검사했다. 생물 사실 검증과 런타임 플레이 검증을 대신하지 않는다.
- [검수 결과](../../_pipeline_r01/validation.json), [저장본 결과](../../_pipeline_r01/saved_validation.json), [출처 해시](../../_pipeline_r01/source_evidence.json)를 참조한다.

## 보류

{deferred[i]}

현행 C011 로더는 128px 전용이므로 기존 실행 묶음을 교체하지 않았다. 신규 셀 크기 지원·상태/충돌 바인딩·실기 성능을 별도 검증해야 한다. 이 제작본의 `production_export_allowed`는 false다.
'''
    (folder/'document/production_r01.md').write_text(production,encoding='utf-8')
    (folder/'ASSET_INDEX.md').write_text(f'''# {index} {names[i]} — 에셋 색인

2026-11-17 · environment-r01 · **정적 제작 후보 / 게임 미연결**

- [제작 범위·규격·보류](document/production_r01.md)
- [편집용 Blender](3D/{obj}_r01.blend) · [메시 검사](3D/model_validation.json)
- [GPT Image 시트](sheet/{obj}_sheet_r01.png) · [실제 Blender 시점](sheet/{obj}_blender_views_r01.png) · [생성 프롬프트](sheet/prompt.txt)
- [5패스 manifest](2D/environment-r01/manifest.json) · [게임 시점 Sprite](2D/environment-r01/{c['clip']}/game_left/sprite.png)
- [C011 1×·회색조 비교](2D/environment-r01/style_compare.png) · [공유 광원 비교](2D/environment-r01/shared_light_compare.png)
- [A 전체 색인](../ASSET_INDEX.md)

범위: {c['clip']} 정적 1표본 × 7시점. {model['triangle_count']}삼각형·0본. 기존 문서와 파일명·밑줄을 보존했다.
''',encoding='utf-8')
    table.append(f"| [{index} {names[i]}]({c['folder']}/ASSET_INDEX.md) | {c['length_ratio']} | {c['cell_size']}² | {width}×{height} | {model['triangle_count']} |")
perf=validation['performance']
(ROOT/'ASSET_INDEX.md').write_text('''# A 환경 에셋 제작본

2026-11-17 · environment-r01 · AssetPipeLine v2.3 적용. **A01–A07 정적 제작 후보 7개를 생성하고 저장·픽셀 검증했다. 게임 연결 완료본은 아니다.**

| 에셋 | C011 길이 기준 배율 | 셀 px | game_left Sprite px | 삼각형 |
| --- | ---: | ---: | ---: | ---: |
'''+ '\n'.join(table)+f'''

[전체 1× 비교판](_pipeline_r01/overview_1x.png) · [회색조](_pipeline_r01/overview_grayscale.png) · [검증](_pipeline_r01/validation.json) · [저장본 재개방](_pipeline_r01/saved_validation.json) · [ZIP](_pipeline_r01/asset_A_environment_r01.zip)

## 완료와 한계

- GPT Image 원본 시트·프롬프트 7세트, 편집 가능한 Blend 7개, 고정 UV 텍스처, 49개 5패스 적층 PNG와 Sprite 미리보기, 뷰별 피벗·앵커·해시 manifest를 저장했다.
- 폴더·논리 ID·클립·뷰·샘플을 별도로 기록했다. 8자리 번호 미정과 DEC-06은 계속 보류다. 3D와 셀 크기를 C011의 128px로 강제하지 않았다.
- 정적 지형에 본·자발 이동을 추가하지 않았다. 물리·먹이·산란 이벤트는 실행하지 않는다. 원본 생태·동작 명세는 보존하며 채택/제외/보류는 각 production_r01.md에 명시했다.
- 셀 원시 RGBA 합계 {validation['raw_rgba_bytes']:,}byte (약 {validation['raw_rgba_bytes']/1024**2:.1f}MiB). 모든 뷰 전량 적재 비용이며 디코딩·재조명 캐시·업로드 여유는 별도다.
- SDL dummy에서 7개 정적 Sprite 합성 p95 {perf['seven_static_blit_p95_ms']:.2f}ms. 기존 게임 BRDF로 320px 돌 1개를 이동 광원 재조명한 p95는 {perf['single_stone_320px_relight_p95_ms']:.2f}ms로 16.7ms 목표를 초과했다. 실기 화면/GPU·실제 게임 코스 검증은 하지 않았다.
- 기존 `toktogi/prototype/`는 128px C011 전용이다. 원본 코드·ZIP을 바꾸지 않았다. 이번 독립 검수기는 새로운 셀 크기의 읽기·해시·패스를 검증하는 인계 도구다.

## 실행 및 출처

[재현 절차](_pipeline_r01/README.md) · [파일 잠금](_pipeline_r01/files.sha256.json) · [원본 근거](_pipeline_r01/source_evidence.json)

ImageGen 내장 도구를 사용했다. 모델 식별자·seed는 반환되지 않아 추정하지 않았다. Blender MCP의 원본 읽기는 성공했으나 제작 호출은 120초 제한으로 실패하여 **Blender 5.3 CLI**로 동일 스크립트를 실행했다. Computer-Use는 사용하지 않았다.
''',encoding='utf-8')
(HERE/'README.md').write_text(r'''# environment-r01 재현·검수

Blender 5.3, Python 3.13, NumPy, Pillow, Pygame을 사용했다. 추가 패키지는 설치하지 않았다. 생성 도구는 ImageGen 내장 도구이며 각 sheet/prompt.txt가 최종 프롬프트다. 파일 해시는 files.sha256.json, 원본 근거는 source_evidence.json이다.

## 경로와 실행

`build_assets.py`는 이 폴더의 상위 A 폴더를 기준으로 7개 에셋을 찾는다. 검토된 입력 시트·assets.json·reference/와 SPRITE_PNG.py가 필요하다. 새 revision은 작업 사본에서 만든다. 다음 명령은 A 폴더에서 실행한다.

```powershell
& 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python .\_pipeline_r01\build_assets.py
& 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python .\_pipeline_r01\check_saved.py
python .\_pipeline_r01\verify_assets.py
```

검수기는 창을 열지 않는다. SDL dummy는 실제 디스플레이 성능 시험이 아니다. lighting.py는 프로젝트의 기존 BRDF 그대로다. 128px 좌표 격자만 검수 호출에서 현재 셀 크기로 교체한다. 게임에 새 로더나 물리 시스템을 설치하지 않는다.

## 묶음·복원

ZIP은 A 폴더를 루트로 하며 상대 경로를 보존한다. files.sha256.json의 파일을 포함한다. 별도 폴더에 압축을 풀고 각 SHA256을 검사한 뒤 사용한다. bundle.source.json은 ZIP 해시와 manifest 서명을 가진다. 기존 제작 모델이 없었으므로 versions/에 소급 버전을 만들지 않았다.

## 관문

- 문서·원본 해시, 정적 메시·UV 존재, 7개 저장본 재개방, packed/external 일치, 임의 seek, 49셀 데이터 계약: PASS.
- 시트는 스타일·주요 형상 참고다. A01/A07의 방향 표기 충돌은 제작 기록에서 채택 패널과 축으로 정리했다. Blender 정투영 판이 최종 축 기준이다.
- 체크 타일 UV 늘어짐 시각 판정, 모션·접촉·취소·효과 1회 실행, 플레이어 착지·수면 이음새, 게임 캐시/업로드/실기 60fps: NOT_RUN 또는 DEFERRED.
- 이동 광원 CPU 재조명 16.7ms 예산: FAIL. 동적 광원 양산 전 캐시·출력 크기·비용을 조정해야 한다.
- DEC-06 양산, 새 8자리 ID, 실제 충돌 크기는 미확정이다. 부력·수영·산란은 현행 제외 범위다.
- OS 썸네일과 Blender 확장 캐시 쓰기는 샌드박스에서 거부됐지만 전달 파일 저장에는 영향이 없었다.
''',encoding='utf-8')
evidence=json.loads((HERE/'source_evidence.json').read_text(encoding='utf-8'))
source=PROJECT/'asset/C/C011_toktogi/3D/toktogi_unified.blend'
evidence=[e for e in evidence if e['path']!=source.relative_to(PROJECT).as_posix()]
evidence.append({'path':source.relative_to(PROJECT).as_posix(),'sha256':sha(source),'use':'read-only camera/preview lighting reference'})
(HERE/'source_evidence.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf-8')
(HERE/'execution.json').write_text(json.dumps({'date':'2026-11-17','computer_use':False,
    'imagegen':'built-in image_gen; seven subject calls; C011 idle style reference',
    'blender_mcp_reference_read':'PASS','blender_mcp_build':'120s timeout',
    'blender_build':'5.3.0 CLI --background --factory-startup --disable-autoexec --threads 2',
    'source_game_modified':False,'deployment_root':'asset/A'},indent=2),encoding='utf-8')
# Only deliver the requested assets, their shared tools, and the root index.
files=[ROOT/'ASSET_INDEX.md']
for c in configs:files.extend(p for p in (ROOT/c['folder']).rglob('*') if p.is_file())
files.extend(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in
    ('asset_A_environment_r01.zip','bundle.source.json','files.sha256.json','deployment.json','deploy.py'))
files=sorted(set(files))
lock={p.relative_to(ROOT).as_posix():sha(p) for p in files}
(HERE/'files.sha256.json').write_text(json.dumps(lock,indent=2,ensure_ascii=False),encoding='utf-8')
bundle=HERE/'asset_A_environment_r01.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in files:archive.write(p,p.relative_to(ROOT).as_posix())
    archive.write(HERE/'files.sha256.json','_pipeline_r01/files.sha256.json')
with zipfile.ZipFile(bundle) as archive:
    assert archive.testzip() is None
    for rel,digest in lock.items():assert hashlib.sha256(archive.read(rel)).hexdigest()==digest,rel
signature=hashlib.sha256(json.dumps(lock,sort_keys=True).encode()).hexdigest()
(HERE/'bundle.source.json').write_text(json.dumps({'schema':1,'revision':'environment-r01','bundle_sha256':sha(bundle),
    'manifest_signature':signature,'files':len(lock),'zip_bytes':bundle.stat().st_size,'zip_readback':'PASS'},indent=2),encoding='utf-8')
print(json.dumps({'files':len(lock),'zip_bytes':bundle.stat().st_size,'zip_hash':sha(bundle)},indent=2))
