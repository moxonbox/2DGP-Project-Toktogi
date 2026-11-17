"""Write measured handoff records and a hash-checked r02 asset bundle."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

configs = read(HERE/'assets.json')
validation = read(HERE/'validation.json')
saved = read(HERE/'saved_validation.json')
atlas = read(HERE/'atlas_preview_validation.json')
assert validation['cell_count'] == 105 and len(saved) == len(atlas) == 7
assert all(a['pixel_validation'] == 'PASS' for a in validation['assets'])
assert sum(a['atlas_rect_roundtrips'] for a in atlas) == 315
assert sum(a['turntable_frames_verified'] for a in atlas) == 56
perf = validation['performance']
details = [
    '엽상체를 비대칭 곡면으로 다듬고 단일 뿌리·뿌리골무·부착부를 보완했다. 희미한 세 맥은 UV에 고정했다. 1×에서 점선처럼 보이던 가는 돌출 맥은 제거했다.',
    '수면에 낮은 주기 곡면과 고정 잔물결 무늬를 넣었다. 상면과 경계·밑면을 분리해 판 가장자리의 잘못된 스무딩을 줄였다. 물 흐름이나 부력 애니메이션은 아니다.',
    '경사면 높이를 불규칙하게 조형하고 얕은 홈·둥근 자갈 7개·낮은 쪽의 작은 물웅덩이를 추가했다. 수변의 색·거칠기 전이를 부드럽게 했다.',
    '가지를 휘고 가늘어지는 비정형 단면으로 바꿨다. 옆가지·양쪽 절단면의 나이테·얕은 나무껍질 능선·옹이를 추가했다. 가는 능선의 1px 끊김을 줄이도록 폭과 매립 깊이를 조정했다.',
    '각진 상자형 돌을 비대칭의 둥근 강돌로 바꿨다. 넓은 상면과 얕은 표면 변형·광물 얼룩·작은 UV 균열을 넣었다. 상면 지지 마커는 최종 메시에서 측정했다.',
    '잎 가장자리를 비대칭으로 말고 끝·찢김·짧은 잎자루를 조형했다. 중맥은 얕은 메시, 측맥은 고정 UV로 분리해 1×에서 과도한 검은 점선을 줄였다.',
    '얇은 부착막의 가장자리를 여러 엽상 돌출로 바꾸고 옅은 황토색 조각 3개와 고정 얼룩을 추가했다. 이끼 줄기·잎 같은 다른 생물 구조는 추가하지 않았다.',
]
names = ['나도좀개구리밥', '정수면', '수변 경사면', '젖은 나뭇가지', '젖은 돌', '젖은 낙엽', '조류 부착막']
rows = []
visual = []
for i, c in enumerate(configs):
    folder = ROOT/c['folder']
    model = read(folder/'3D/model_validation_r02.json')
    manifest = read(folder/'2D/environment-r02/manifest.json')
    checked = next(s for s in saved if s['asset_id'] == c['asset_id'])
    assert sha(folder/manifest['source_blend']) == model['blend_sha256'] == checked['source_blend_sha256']
    assert manifest['generator_sha256'] == sha(HERE/'build_assets.py')
    assert manifest['preview_generator_sha256'] == sha(HERE/'make_previews.py')
    assert checked['saved_reopen'] == 'PASS' and len(manifest['game_atlas']['rects']) == 9
    bbox = next(x for x in manifest['cells'] if x['view'] == 'left')['bbox']['sprite']
    extent = ' × '.join(f'{v:.4f}' for v in model['extent_bu'])
    biological = ('엽상체 길이 3.5mm·폭 2.3mm는 기존 범위 안의 제작 선택값이며 특정 개체 실측이 아니다. 뿌리 크기·굽힘은 각색이다.'
                  if i == 0 else '생물 실측 mm는 null이다. 모듈 길이·폭·높이·무늬는 게임 연출 선택값이다.')
    uv_note = ('돌의 측면은 평면 투영에 따른 늘어짐이 남는다. 약한 비방향성 얼룩에는 허용했으며, 큰 방향성 문양을 넣을 때 측면 UV를 별도 전개해야 한다.'
               if i == 4 else '작은 뿌리·자갈·능선·맥·색 조각은 별도 UV 섬으로 체크 밀도가 더 높다. 부위별 밀도 차이와 반복 밑면은 의도적이다.')
    (folder/'document/production_r02.md').write_text(f'''# {c['folder']} — environment-r02

2026-11-17. 모델·디테일·C011 방향별 정적 Sprite 보완. 게임 연결 상태는 보류다.

## 변경과 크기

{details[i]}

- [원본 외형]({c['asset_id']}_model.md)·[동작]({c['asset_id']}_movement.md)·[r01 채택 범위](production_r01.md)는 보존한다. 기존 미채택 동작을 이번 정적 출력의 구현으로 간주하지 않는다.
- [r02 계약](production_contract_r02.json): 길이 기준 {c['length_ratio']}×C011, 목표 X 길이 {c['length_bu']:.6f}BU. 부속부 포함 최종 외접은 {extent}BU다. 목표 길이와 전체 외접은 서로 다른 측정값이다.
- {biological} C011 몸 대용값 0.965396BU를 사용하며 SI 실측 스케일로 주장하지 않는다.
- {c['cell_size']}px 정사각 셀, 0.01390625BU/px, 1× Nearest. left Sprite 외접 {bbox[2]-bbox[0]}×{bbox[3]-bbox[1]}px. 모든 방향의 Sprite/Base 투명 여백 ≥8px.
- 삼각형 {model['triangle_count']:,}/{c['triangle_budget']:,}, 본 0. [실측](../3D/model_validation_r02.json). 편집 가능한 닫힌 메시를 유지하고 검증되지 않은 숨은 면 삭제는 하지 않았다.

## 방향·피벗·표시

- C011 integrated-r5와 같은 9키: left, yaw_045/090/135/180/225/270/315, right. right는 2.00151174696589rad(약 114.68°)이며 yaw_180과 별개다.
- 모든 게임 방향은 같은 카메라·같은 피벗 {manifest['game_pivot']}에서 메시의 실제 Z 회전으로 출력했다. 이미지 미러·임의 trim·2D 회전은 없다. 6개 ortho_*는 모델 검수 전용으로 분리했다.
- [manifest](../2D/environment-r02/manifest.json)에 방향·yaw·카메라 행렬·피벗·앵커·외접·시간·파일 해시·아틀라스 rect가 있다. Blend 내장 SELECT_ENVIRONMENT_VIEW.py의 select_view(name)으로 같은 15시점을 재현한다.
- 5패스는 Sprite/Base/Normal/RM/Emissive 순서다. 데이터 패스 A=255, coverage는 Base A. Base에 조명·AO를 굽지 않으며 AO 소비자 기본값은 1이다. RM G/B=0, 발광=0.
- 기본색 {c['color']}, 거칠기 {c['roughness']}, 젖음 전이 폭 0.08BU는 연출값이다. 고정 UV 무늬·선형 bilinear 보간·C011 4단 명암 뒤 재질별 팔레트 양자화를 쓴다. 실제 팔레트는 각 cell의 palette_rgb다.
- 외곽색 #22313B, 반경 {c['outline_radius_px']}px. 수면·부착막은 검은 테두리가 판처럼 보이지 않도록 외곽선 0px 예외다. 디더·화면 AA·mipmap은 없다.
- Blender 미리보기는 기존 C011 AgX·3광원·World, CPU Sprite는 고정 toon4, 연속 재조명 비교판은 기존 게임 BRDF power .82/ambient .34다. 이 세 경로를 구분한다.

## 검수와 자료

- [전후 비교](../2D/environment-r02/before_after.png)·[9방향/C011](../2D/environment-r02/game_views_C011.png)·[회색조](../2D/environment-r02/game_views_grayscale.png)·[공유 광원](../2D/environment-r02/shared_light_compare.png).
- [8방향 APNG](../2D/environment-r02/turntable.png)는 350ms마다 방향을 보여주는 검수 회전이다. 동작 애니메이션이 아니다. 호환 right는 9방향 판에서 별도 확인한다.
- [UV 체크](../2D/environment-r02/uv_checker_compare.png)의 left·ortho_top을 시각 확인했다. {uv_note} 밑면은 반복을 허용하며 완전한 고유 UV 베이크 아틀라스로 쓰지 않는다.
- [기존 GPT 시트](../sheet/{c['asset_id']}_sheet_r01.png)·[원본 프롬프트](../sheet/prompt.txt)를 재사용했다. 새 ImageGen 호출은 없다. [새 6면 시트](../sheet/{c['asset_id']}_blender_views_r02.png)는 최종 메시에서 출력했다.
- 재개방·packed/external 일치·15방향 정순/역순·unknown 거부·임의 프레임 seek·원상 복귀 PASS. 셀 15개·아틀라스 영역 45개·APNG 8프레임의 원본 픽셀 일치 PASS.
- [파일 검사](../../_pipeline_r02/validation.json)·[저장본 검사](../../_pipeline_r02/saved_validation.json)·[아틀라스 검사](../../_pipeline_r02/atlas_preview_validation.json)·[출처](../../_pipeline_r02/source_evidence.json).

## 미검증·보류

128px 전용 게임 로더 연결·충돌/접지 바인딩·실제 코스·실기 성능은 미실행이다. 물리·부력·먹이·산란 이벤트는 구현하지 않았다. DEC-06과 번호 확정은 보류이며 production_export_allowed=false를 유지한다. 게임 애니메이션이나 양산 승인으로 해석하지 않는다.
''', encoding='utf-8')
    (folder/'ASSET_INDEX.md').write_text(f'''# {c['folder']} — {names[i]}

현재 제작본 **environment-r02** · 2026-11-17. {details[i]}

- [모델](3D/{c['asset_id']}_r02.blend) · [제작 기록](document/production_r02.md) · [계약](document/production_contract_r02.json)
- [C011와 9방향 비교](2D/environment-r02/game_views_C011.png) · [회전 APNG](2D/environment-r02/turntable.png) · [전후 비교](2D/environment-r02/before_after.png)
- [6면 시트](sheet/{c['asset_id']}_blender_views_r02.png) · [UV 체크](2D/environment-r02/uv_checker_compare.png)
- [manifest/5패스 아틀라스 좌표](2D/environment-r02/manifest.json) · [Sprite 아틀라스](2D/environment-r02/game_atlas_sprite.png)
- [r01 제작 기록](document/production_r01.md) · [원본 GPT 시트](sheet/{c['asset_id']}_sheet_r01.png) · [전체 A 색인](../ASSET_INDEX.md)

게임 9시점 + 검수 6시점 = 15셀. 셀 {c['cell_size']}px, 5패스, 삼각형 {model['triangle_count']:,}, 본 0. r01 파일은 원래 위치에 보존했다. 게임 연결·실기 검증·DEC-06은 보류다.
''', encoding='utf-8')
    rows.append(f"| [{c['folder']}]({c['folder']}/ASSET_INDEX.md) | {c['length_ratio']}× | {c['cell_size']} | {model['triangle_count']:,} | 9 + 6 |")
    visual.append({'asset_id':c['asset_id'], 'reviewed':'overview_1x, left and ortho_top UV checker',
                   'uv_limit':uv_note, 'mesh_details':details[i]})

(ROOT/'ASSET_INDEX.md').write_text(f'''# A 환경·소품 — environment-r02

2026-11-17. A01–A07의 모델·표면 디테일을 보완하고 C011 토토기와 같은 9방향 Sprite를 추가했다. 기존 r01은 보존했다.

[전체 1× 비교판](_pipeline_r02/overview_1x.png) · [회색조](_pipeline_r02/overview_grayscale.png) · [ZIP](_pipeline_r02/asset_A_environment_r02.zip)

| 에셋 | C011 길이 기준 | 셀 px | 삼각형 | 게임 + 검수 시점 |
| --- | ---: | ---: | ---: | ---: |
'''+'\n'.join(rows)+f'''

## 출력·보존

- 편집 가능한 Blend 7개, 고정 UV 텍스처, 105개 5패스 적층 셀(게임 63·검수 42), 패스별 게임 아틀라스 35장, 9방향 비교판·회전 APNG·전후 비교·UV 체크·6면 시트를 제공한다.
- 각 자산의 9방향은 같은 피벗·카메라를 쓴다. 8개 순환 yaw와 호환 right(약 114.68°)를 구분하며 실제 메시 회전으로 출력했다. 0.01390625BU/px와 상대 길이 기준을 유지한다.
- 8개 색인만 최신본으로 전환하며 이전 색인은 [보존 위치](_pipeline_r02/before/ASSET_INDEX.md)에 있다. r01 모델·텍스처·출력·ZIP·원본 문서는 그대로다. [보존/복원 지도](_pipeline_r02/restore_map.json).
- GPT 시트 7개와 프롬프트는 r01을 재사용했다. 이번 6면 시트는 보완한 메시에서 출력했다. Blender MCP 연결 불가로 Blender 5.3 CLI를 사용했으며 Computer-Use는 사용하지 않았다.

## 검증과 실행 상태

- [저장본 7개 재개방](_pipeline_r02/saved_validation.json), [105셀 검사](_pipeline_r02/validation.json), [아틀라스 315영역·APNG 56프레임](_pipeline_r02/atlas_preview_validation.json) PASS. 모델 예산·뷰 선택·UV/텍스처·해시·피벗·패스·Alpha·Normal·여백을 확인했다.
- [시각 검수 기록](_pipeline_r02/visual_review.json). 작은 부위의 UV 밀도 차이·밑면 반복·돌 측면의 평면 투영 늘어짐은 기록한 제한이다.
- 전 셀 5패스 원시 RGBA는 {validation['raw_rgba_bytes']:,}byte(약 {validation['raw_rgba_bytes']/1024**2:.1f}MiB), 아틀라스·캐시 중복은 별도다. 전체 동시 적재를 권장하는 값이 아니다.
- SDL dummy 120프레임: 7개 정적 Sprite 합성 p95 {perf['seven_static_blit_p95_ms']:.2f}ms, 320px 돌 1개 CPU 재조명 p95 {perf['single_stone_320px_relight_p95_ms']:.2f}ms. 재조명은 16.7ms 목표 초과다.
- 기존 게임 로더는 128px 전용이다. 새 로더·게임 물리·실제 코스·실기 화면/GPU는 미검증이며 기존 게임 코드는 변경하지 않았다. DEC-06·양산은 보류, production_export_allowed=false다.

[재현 절차](_pipeline_r02/README.md) · [파일 잠금](_pipeline_r02/files.sha256.json) · [원본 근거](_pipeline_r02/source_evidence.json)
''', encoding='utf-8')

(HERE/'README.md').write_text(r'''# environment-r02 재현·검수

Blender 5.3, Python 3.13, NumPy, Pillow, Pygame. 추가 의존성 설치 없이 기존 환경을 사용했다. 스크립트는 자신의 상위 A 폴더에서 입력·출력을 찾는다. 원본 프로젝트에 바로 재생성하지 말고 ZIP을 별도 작업 폴더에 복원한 뒤 실행한다.

```powershell
& 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python .\_pipeline_r02\build_assets.py
& 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python .\_pipeline_r02\check_saved.py
python .\_pipeline_r02\verify_assets.py
python .\_pipeline_r02\make_previews.py
python .\_pipeline_r02\finalize.py
```

각 명령 성공 후 다음 명령을 실행한다. build_assets는 셀과 manifest를 다시 쓰므로 반드시 make_previews까지 실행해 5패스 아틀라스·좌표·해시를 갱신한다. finalize는 검증 결과·Blend·생성기 해시 일치를 요구하고 문서·ZIP을 작성한다. OS 썸네일/확장 캐시 경고는 전달 파일 저장과 무관했다.

## 소비 규칙

- 2D/environment-r02/manifest.json의 cells에서 view를 선택하고 cell_size·pass_order·pivot·anchors를 읽는다. 000.png는 5패스 적층 원본, sprite.png는 표시용이다.
- game_atlas는 3×3 배치·2px 패딩과 각 rect를 명시한다. 게임 9뷰만 포함하며 6개 ortho_*는 개별 셀로 남는다. 데이터 패스 coverage는 Base Alpha다.
- turntable.png는 8방향 APNG 검수 미리보기이며 게임 클립이 아니다. 시간 350ms/방향. 호환 right는 순환 순서에 끼워 넣지 않는다.
- Blender 내장 SELECT_ENVIRONMENT_VIEW.py를 실행한 뒤 select_view('yaw_090')처럼 호출한다. ENVIRONMENT_VIEWS.json에 고정 카메라/피벗·yaw가 들어 있다. 자동실행은 필요 없다.
- lighting.py는 기존 게임 BRDF 사본이다. 검수기에서 좌표 격자 크기만 해당 셀로 바꾼다. 실기 성능 검증이나 새 런타임 로더를 대체하지 않는다.

## 복원·이전 자료

files.sha256.json은 ZIP 내부의 상대 경로와 SHA256을 잠근다. bundle.source.json은 ZIP 해시와 파일 목록 서명을 가진다. 별도 폴더에 안전하게 풀고 해시를 확인한 후 사용한다. r02 ZIP은 r02 모델·출력과 필요한 입력을 포함하며 전체 프로젝트/게임 실행 묶음이 아니다. 이전 r01 결과는 원래 프로젝트 위치와 r01 ZIP에 보존하며 restore_map.json에 연결했다.

before/의 Markdown은 이전 색인의 원문 보존본이다. 그 안의 상대 링크는 이전 A 위치를 기준으로 하므로 탐색에는 현재 ASSET_INDEX.md를 사용한다. reference/는 제작 당시 문서/이미지 스냅샷이다. 원본 생태·모션·라이선스 근거는 기존 document 및 r01 제작 기록을 유지하며 새 생물 사실을 추가하지 않았다.

## 남은 관문

큰 셀 로더·상태/충돌/접지 연결·실기 60fps·실제 코스·물리/효과는 미검증이다. CPU 동적 재조명은 측정 예산을 넘는다. 수영·부력·산란은 현행 제외 범위를 유지한다. 정적 모델 개선을 모션 구현으로 간주하지 않는다. 돌 측면 UV와 작은 부위의 밀도 차이는 고유 방향성 텍스처를 확대 적용하기 전에 재전개한다. 번호 확정·DEC-06 양산은 보류다.
''', encoding='utf-8')

write(HERE/'visual_review.json', {'date':'2026-11-17','reviewer':'assistant visual inspection',
    'additional_samples':['A04 and A06 game_views_C011', 'A05 shared_light_compare'],
    'assets':visual,'actual_game_and_hardware':'NOT_RUN'})
write(HERE/'execution.json', {'date':'2026-11-17','computer_use':False,'new_imagegen_calls':0,
    'image_source':'r01 seven GPT sheets and prompts retained', 'blender_mcp':'connection unavailable at 127.0.0.1:9876',
    'blender_build':'Blender 5.3 CLI, background factory-startup disable-autoexec threads=2',
    'source_game_modified':False,'scope':'seven static A assets, model/detail/15 views'})
baseline_path = HERE/'baseline_r01.sha256.json'
baseline = read(baseline_path if baseline_path.exists() else ROOT/'baseline.json')
write(HERE/'baseline_r01.sha256.json', baseline)
indexes = ['ASSET_INDEX.md'] + [c['folder']+'/ASSET_INDEX.md' for c in configs]
restore = []
for rel in indexes:
    archived = HERE/'before'/rel
    assert sha(archived) == baseline[rel]
    restore.append({'current':rel,'previous':archived.relative_to(ROOT).as_posix(),
                    'previous_sha256':baseline[rel],'current_sha256':sha(ROOT/rel)})
write(HERE/'restore_map.json', {'revision':'environment-r02','index_restore':restore,
    'r01_unchanged_files':{r:h for r,h in baseline.items() if r not in indexes},
    'previous_bundle':'_pipeline_r01/asset_A_environment_r01.zip',
    'policy':'No deletes; r01 remains in original paths. Restore only eight indexes to roll back navigation.'})

files = [ROOT/'ASSET_INDEX.md']
for c in configs:
    files.extend(p for p in (ROOT/c['folder']).rglob('*') if p.is_file())
excluded = {'files.sha256.json','bundle.source.json','asset_A_environment_r02.zip','deployment.json'}
files.extend(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded)
files = sorted(set(files))
lock = {p.relative_to(ROOT).as_posix():sha(p) for p in files}
write(HERE/'files.sha256.json', lock)
bundle = HERE/'asset_A_environment_r02.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in files:
        archive.write(p,p.relative_to(ROOT).as_posix())
    archive.write(HERE/'files.sha256.json','_pipeline_r02/files.sha256.json')
with zipfile.ZipFile(bundle) as archive:
    assert archive.testzip() is None
    for rel,digest in lock.items():
        assert hashlib.sha256(archive.read(rel)).hexdigest() == digest, rel
write(HERE/'bundle.source.json', {'revision':'environment-r02','bundle_sha256':sha(bundle),
    'manifest_signature':hashlib.sha256(json.dumps(lock,sort_keys=True).encode()).hexdigest(),
    'files':len(lock),'zip_bytes':bundle.stat().st_size,'zip_readback':'PASS'})
print(json.dumps({'files':len(lock),'zip_bytes':bundle.stat().st_size,'zip_readback':'PASS'}))
