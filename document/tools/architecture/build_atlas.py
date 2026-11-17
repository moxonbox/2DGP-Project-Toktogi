"""Build the self-contained architecture guide from the project directory."""
from pathlib import Path
from zipfile import ZipFile
from html import escape
from io import BytesIO
from os.path import relpath
import ast
import base64
import json
import re
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
DOCUMENT = PROJECT / 'document'
DEST = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DOCUMENT / 'ToktogiProjectArchitecture.html'
SPEC = DOCUMENT / 'markdown/001_toktogi_game_design_spec.md'


def read_section(path, anchor):
    marker = f'<a id="{anchor}"></a>'
    _, separator, rest = path.read_text(encoding='utf8').partition(marker)
    if not separator:
        raise ValueError(f'Missing section {marker} in {path}')
    heading, _, body = rest.lstrip().partition('\n')
    if not heading.startswith('## '):
        raise ValueError(f'Expected a level 2 heading after {marker} in {path}')
    return re.split(r'^#{1,2} |^<a id="[^"]+"></a>$', body, maxsplit=1, flags=re.M)[0]


def resolve_link(target):
    relative_path, _, anchor = target.partition('#')
    path = (SPEC.parent / relative_path).resolve() if relative_path else SPEC
    if not path.is_relative_to(PROJECT) or not path.is_file():
        raise ValueError(f'Invalid specification link: {target}')
    if anchor:
        read_section(path, anchor)
    return path, anchor


def href(path, anchor=''):
    relative = Path(relpath(path, DOCUMENT)).as_posix()
    return relative + (f'#{anchor}' if anchor else '')


def tables(markdown):
    for block in re.findall(r'^\|.*\|(?:\n\|.*\|)+', markdown, re.M):
        header, separator, *rows = [
            [cell.strip() for cell in line.strip('|').split('|')] for line in block.splitlines()
        ]
        if not rows or len(separator) != len(header) or any(len(row) != len(header) for row in rows):
            raise ValueError(f'Invalid table with header {header}')
        yield header, rows


def keys_html(value):
    return re.sub(r'\[([^\]]+)\]', r'<kbd>\1</kbd>', escape(value))


def html_table(header, rows, *, render=escape):
    columns = ''.join(f'<th scope="col">{escape(text)}</th>' for text in header)
    body = []
    for first, *cells in rows:
        values = ''.join(f'<td>{render(text)}</td>' for text in cells)
        body.append(f'<tr><th scope="row">{render(first)}</th>{values}</tr>')
    return f'<table class="thin"><thead><tr>{columns}</tr></thead><tbody>{"".join(body)}</tbody></table>'


contract = read_section(SPEC, 'atlas-sources')
_, source_rows = next(tables(contract))
sources = {}
for section, link, _ in source_rows:
    match = re.fullmatch(r'\[[^\]]+\]\(([^)]+)\)', link)
    if not match or section in sources:
        raise ValueError(f'Invalid source for HTML section {section}: {link}')
    sources[section] = resolve_link(match[1])
expected_sections = {'architecture', 'framework', 'files', 'controls', 'states', 'motion', 'materials', 'specs', 'evidence'}
if sources.keys() != expected_sections:
    raise ValueError(f'Unexpected or missing HTML sections: {sources.keys() ^ expected_sections}')
GAME = sources['files'][0].parent

def extract_json(path, anchor):
    raw = path.read_text(encoding='utf8')
    return json.loads(re.search(fr'<script id="{anchor}" type="application/json">(.*?)</script>', raw, flags=re.S)[1])


def png_uri(img):
    file = BytesIO()
    img.save(file, format='PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(file.getvalue()).decode('ascii')


motions = extract_json(sources['motion'][0], 'motion-data')
with ZipFile(GAME / 'toktogi_assets.zip') as z:
    base = json.loads(z.read('playable_manifest.json'))
    original_cells = sum(name.endswith('.png') for name in z.namelist())
with ZipFile(GAME / 'toktogi_runtime_poses.zip') as z:
    supplemental = json.loads(z.read('runtime_poses.json'))
    supplement_cells = sum(name.endswith('.png') for name in z.namelist())
checks = json.loads(sources['evidence'][0].read_bytes())
spin = json.loads((PROJECT / 'asset/C/C01_toktogi/3D/framework-r4/spin_interkey_validation.json').read_bytes())
regression = sum(len(checks[key]) for key in ('review_regressions','gameplay_r2','gameplay_r3','gameplay_r4','framework_r1'))
groups = {
    'main': ('실행', '명령행에서 플레이 또는 회귀 검증을 시작한다.'),
    'app': ('실행', 'Pygame 창, 장면 전환, 단축키와 입력 수명을 관리한다.'),
    'input_clock': ('입력', 'Windows SDL2 큐의 타임스탬프를 보존한다.'),
    'timeline': ('입력', '입력 순번과 120Hz 고정 틱, 캐치업을 처리한다.'),
    'game': ('규칙', '행동·진행 상태, 발사·착지·효과·전환 수명을 관리한다.'),
    'physics': ('규칙', '평면 코스의 Capsule 스윕과 선분·박스 교차를 계산한다.'),
    'course': ('규칙', '발판·먹이·등불·가시·체크포인트·목표 배치를 선언한다.'),
    'motion': ('모션', 'Track 표본 시간, 진입·복귀 경로와 실제 게임 자세를 선택한다.'),
    'replays': ('모션', '대표 입력 네 가지를 Game에 넣어 셀과 사건 시간을 얻는다.'),
    'materials': ('에셋', 'ZIP 잠금, PNG 헤더·마커·참조와 캐시를 관리한다.'),
    'sprite_renderer': ('표시', '5패스 제공자를 받고 재질 모드와 셰이딩 캐시를 제공한다.'),
    'lighting': ('표시', '카메라 Normal·RM·발광을 Pillow CPU 셰이딩으로 계산한다.'),
    'play_view': ('표시', '코스·플레이어·추적광과 접지 그림자를 그린다.'),
    'motion_viewer': ('표시', 'F2 모션 검색과 프레임·재질·광원·마커 조작을 그린다.'),
    'pack_assets': ('제작', '원본 아틀라스에서 128px 5패스 셀 ZIP을 생성한다.'),
    'build_motion_preview': ('제작', '원본·보조·게임 시간·리플레이를 독립 HTML에 묶는다.'),
    'verify_prototype': ('검증', '입력 재생·완주와 전 셀 재질 검증을 실행한다.'),
    'verify_requirements': ('검증', 'v2.1 요구 ID에서 현행 프로필에 적용되는 하위 사례를 검사한다.'),
    'verify_regressions': ('검증', '입력 시각·효과·지지·셰이더의 기존 반례를 재실행한다.'),
    'verify_gameplay_r2': ('검증', '손질·착지·보조 셀과 조명 기준을 확인한다.'),
    'verify_gameplay_r3': ('검증', '반전·모서리·목표·입력 포커스 회귀를 확인한다.'),
    'verify_gameplay_r4': ('검증', '탄성 타이밍·조준·도약 전개의 가독성을 확인한다.'),
    'verify_framework': ('검증', 'Q·Z·섭식 전환·코스 재사용·리플레이를 확인한다.'),
}
modules = []
module_symbols = {}
definitions = (ast.FunctionDef, ast.AsyncFunctionDef)
for file in sorted(GAME.glob('*.py')):
    text = file.read_text(encoding='utf8')
    group, role = groups.get(file.stem, ('기타', '프로젝트 Python 모듈'))
    tree = ast.parse(text)
    functions = [dict(name=n.name,line=n.lineno) for n in tree.body if isinstance(n, definitions)]
    classes = []
    for n in tree.body:
        if not isinstance(n, ast.ClassDef):
            continue
        methods = [dict(name=m.name,line=m.lineno) for m in n.body if isinstance(m, definitions)]
        fields = [dict(name=m.target.id,line=m.lineno) for m in n.body
                  if isinstance(m, ast.AnnAssign) and isinstance(m.target, ast.Name)]
        classes.append(dict(name=n.name,line=n.lineno,bases=[ast.unparse(b) for b in n.bases],
                            methods=methods,fields=fields))
    local_imports = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and not n.level:
            local_imports.append((n.module, ', '.join(a.name for a in n.names), n.lineno))
        elif isinstance(n, ast.Import):
            local_imports.extend((a.name, a.name, n.lineno) for a in n.names)
    imports = [dict(file=f'{name.split(".")[0]}.py', names=names, line=line)
               for name,names,line in sorted(local_imports,key=lambda item:item[2])
               if (GAME / f'{name.split(".")[0]}.py').is_file()]
    symbols = {item['name']:item['line'] for item in functions+classes}
    for c in classes:
        symbols.update((f"{c['name']}.{member['name']}",member['line']) for member in c['methods']+c['fields'])
    module_symbols[file.name] = symbols
    modules.append(dict(file=file.name,group=group,role=role,lines=len(text.splitlines()),
                        symbols=' '.join(symbols),classes=classes,functions=functions,imports=imports))


def source(file, symbol):
    path = PROJECT / file
    lines = path.read_text(encoding='utf8').splitlines()
    line = next(i for i, text in enumerate(lines,1) if symbol in text)
    return {'path':href(path),'line':line,'symbol':symbol}


def src(name, symbol):
    return source((GAME / f'{name}.py').relative_to(PROJECT).as_posix(), symbol)


def node(title, role, reads, writes, refs):
    return dict(title=title,role=role,reads=reads,writes=writes,refs=refs)


nodes = {
    'entry':node('실행과 장면', '프로그램을 시작하고 플레이와 F2 검수의 입력 대상을 정한다.', '키·마우스·포커스, 실행 인수', 'Game / Viewer 선택, 창과 화면 갱신', [src('main',"if __name__=='__main__'"),src('app','def switch('),src('app','GAME_KEYS=')]),
    'clock':node('입력과 시간', 'SDL2 큐의 입력 시간과 이벤트 순서를 보존해 고정 틱에 전달한다.', 'SDL 타임스탬프, 프레임 경과 시간', '120Hz 논리 틱과 처리할 입력', [src('input_clock','class EventClock'),src('timeline','def advance(')]),
    'rules':node('게임 규칙', '위치·속도와 행동·진행 상태를 갱신하고 bite·hit·launch 같은 효과를 확정한다.', '논리 입력, Course, 접촉 마커', '현재 자세와 게임 사건, 지지면', [src('game','def step('),src('game','def work_tick('),src('game','def launch(')]),
    'motion':node('모션 선택', 'Game이 유지하는 행동·속도·회전에 맞춰 Track의 셀 하나를 고른다.', '현재 상태, 방향, 보행 위상, 제작 시간표', 'clip · view · sample, 보간 없는 픽셀 셀', [src('motion','class Track'),src('motion','class MotionSet'),src('motion','def cell(')]),
    'render':node('화면과 조명', 'PlayView와 Viewer가 같은 재질 렌더러로 128px 셀을 그린다.', '스프라이트 키, 5패스, 카메라 기준 광원', 'Pygame Surface와 최종 화면', [src('play_view','class PlayView'),src('sprite_renderer','class SpriteRenderer'),src('lighting','def shade(')]),
    'course':node('코스와 충돌', '정적 발판의 순수 충돌 계산을 제공한다. 시작과 체크포인트의 지지 자세 및 Capsule 여유를 검사한다.', '발판 박스와 Capsule 위치·속도', '수평 정지점, 바닥·천장 후보, 코스 대상', [src('course','class Course'),src('physics','def capsule_overlaps('),src('physics','def sweep_y(')]),
    'assets':node('에셋 저장소', '기반 ZIP과 보조 ZIP을 열고 SHA256, 서명, 프레임·마커·PNG 헤더를 검사한다.', 'integrated-r5 원본 및 r4 보조 ZIP, source lock', '5패스 셀과 Track, 접지·작업 마커', [src('materials','class Assets'),src('materials','def validate_tracks('),src('motion','def validate_playable(')]),
    'replay':node('검수와 리플레이', '같은 Game의 입력을 120Hz로 재생해 셀 순서와 사건 시간을 수집한다.', '대표 상황과 시각이 붙은 입력, 런타임 모션', 'F2의 재질 검수와 HTML의 Sprite 재생', [src('replays','def game_replays('),src('motion_viewer','class Viewer'),src('build_motion_preview','previews=')]),
    'author':node('Blender 제작', '왼쪽·오른쪽 Z의 지지발 목표를 월드 좌표에서 유지하고 5ms마다 본 키를 굽는다.', '원본 리그·카메라·UV·웨이트', '128px 5패스와 앵커, 지오메트리 해시', [source('asset/C/C01_toktogi/3D/framework-r4/build_spin_r4.py','def plan_contacts('),source('asset/C/C01_toktogi/3D/framework-r4/check_saved.py','geometry_hash')]),
}

framework = []
objects = ''
for title, entries in re.findall(r'^### ([^\n]+)\n(.*?)(?=^### |\Z)', read_section(*sources['framework']), re.M | re.S):
    header, rows = next(tables(entries))
    if header == ['파일', '심볼', '동작']:
        items = []
        for file, symbol, detail in rows:
            symbols = module_symbols[file]
            line = f' <small>L{symbols[symbol]}</small>' if symbol else ''
            name = escape(symbol or file)
            items.append(f'<li><a href="#files/{escape(file)}"><code>{name}</code></a>{line}<p>{escape(detail)}</p></li>')
        framework.append(f'<article class="panel"><h3>{escape(title)}</h3><ol class="call-flow">{"".join(items)}</ol></article>')
    elif header == ['파일', '객체', '연결되는 객체', '관계'] and not objects:
        items = []
        for file, symbol, related, detail in rows:
            if symbol not in module_symbols[file]:
                raise ValueError(f'Unknown object {symbol} in {file}')
            items.append(
                f'<tr><th scope="row"><a href="#files/{escape(file)}"><code>{escape(symbol)}</code></a></th>'
                f'<td><code>{escape(related)}</code></td><td>{escape(detail)}</td></tr>'
            )
        objects = ''.join(items)
    else:
        raise ValueError(f'Unexpected framework table: {title}')
if not (framework and objects):
    raise ValueError('Framework requires call order and object relationships')

play_controls, viewer_controls = tables(read_section(*sources['controls']))
state_document = read_section(*sources['states'])
(_, state_rows), (_, progress) = tables(state_document)
states = {name: (title, description, []) for name, title, _, description in state_rows}
diagram = re.search(r'^~~~mermaid\nstateDiagram-v2\n(.*?)^~~~', state_document, re.M | re.S)
if not diagram:
    raise ValueError('Missing current Mermaid state diagram')
initial = None
for statement in diagram[1].strip().splitlines():
    match = re.fullmatch(r'\s*(\[\*\]|\w+) --> (\w+)(?:: (.+))?', statement)
    if not match:
        raise ValueError(f'Invalid state transition: {statement}')
    origin, destination, condition = match.groups()
    if destination not in states:
        raise ValueError(f'Unknown destination state: {destination}')
    if origin == '[*]' and initial is None and condition is None:
        initial = destination
    elif origin in states and condition:
        states[origin][2].append(f'{condition} → {destination}')
    else:
        raise ValueError(f'Invalid state transition: {statement}')
if not initial or any(not state[2] for state in states.values()):
    raise ValueError('State diagram requires one initial state and outgoing transitions for every state')
state_buttons = ''.join(
    f'<button class="state-card" type="button" data-state="{escape(name)}" aria-pressed="{str(name == initial).lower()}">'
    f'<b>{escape(name)}</b><small>{escape(label)}</small></button>' for name, _, label, _ in state_rows
)
state_summary = ''.join(
    f'<tr><th scope="row">{escape(name)}</th><td>{" · ".join(map(keys_html, entry[2]))}</td></tr>'
    for name, entry in states.items()
)
state_notes = re.search(r'^> (.+)$', state_document, re.M)
if not state_notes:
    raise ValueError('Missing current state notes')
initial_title, initial_description, initial_edges = states[initial]

frames = {}
videos = []
replays = [
    ('replay_feed_attack','섭식 복귀 → 공격','F 유지 · F UP · X', '재현용으로 시작 발판에 가시 껍질을 배치한 시나리오다.'),
    ('replay_walk_z','보행 → Z → 보행','→ 유지 · Z · → 해제','보행 위상별 제동 후 한 바퀴 돌고 걷기를 이어 간다.'),
    ('replay_q_reverse','Q 재반전','Q · → · ←','현재 회전 중간 포즈를 기준으로 방향을 다시 평가한다.'),
    ('replay_jump_land','도약 → 공중제비 → 착지','Space DOWN · Space UP','기본 코스 시작 발판 x=165에서 다음 발판에 착지한다.'),
    ('game_ground_spin_left','지상 Z · 왼쪽 시작','Z','왼쪽 중립 자세에서 시작해 같은 방향으로 돌아온다.'),
    ('game_ground_spin_right','지상 Z · 오른쪽 시작','Z','오른쪽 중립 자세에서 시작해 같은 방향으로 돌아온다.'),
    ('game_turn_left_right_left','Q · 왼쪽에서 오른쪽','Q','중립 반전 480ms. 서로 다른 지지 자세를 100ms씩 표시한다.'),
    ('game_turn_right_left_right','Q · 오른쪽에서 왼쪽','Q','중립 반전 480ms. 서로 다른 지지 자세를 100ms씩 표시한다.'),
]
tiles = []
for key,title,keys,detail in replays:
    report = motions['motions'][key]
    sequence = next(iter(report['tracks'].values()))
    sequence_out = []
    for atlas,x,y,ms in sequence:
        if atlas not in frames:
            frames[atlas] = Image.open(BytesIO(base64.b64decode(motions['atlases'][atlas].split(',')[1]))).convert('RGBA')
        image = frames[atlas].crop((x,y,x+128,y+128))
        sequence_out.append([len(tiles), ms])
        tiles.append(image)
    videos.append(dict(id=key,title=title,keys=keys,detail=detail,frames=sequence_out,events=report.get('events',[])))
columns=12
atlas = Image.new('RGBA',(128*columns,128*((len(tiles)+columns-1)//columns)))
for i,tile in enumerate(tiles):
    atlas.paste(tile,(128*(i%columns),128*(i//columns)))
hero_track=motions['motions']['idle']['tracks']['right']
name,x,y,_=hero_track[0]
hero_src=Image.open(BytesIO(base64.b64decode(motions['atlases'][name].split(',')[1])))
hero=png_uri(hero_src.crop((x,y,x+128,y+128)))

values = {
    'atlas': png_uri(atlas), 'columns':columns, 'videos':videos, 'nodes':nodes, 'modules':modules,
    'states': states, 'initialState': initial, 'moduleBase': href(GAME) + '/',
}
template=(HERE/'atlas.template.html').read_text(encoding='utf8')
spec_map = read_section(*sources['specs'])
spec_cards = []
for heading, entries in re.findall(r'^### ([^\n]+)\n(.*?)(?=^### |\Z)', spec_map, re.M | re.S):
    rows = []
    for entry in entries.splitlines():
        if not entry.strip():
            continue
        match = re.fullmatch(r'- (.*?)\[([^\]]+)\]\(([^)]+)\)(.*)', entry)
        if not match:
            raise ValueError(f'Invalid specification map entry: {entry}')
        before, label, target, after = match.groups()
        link = escape(href(*resolve_link(target)), quote=True)
        rows.append(f'<li>{escape(before)}<a href="{link}">{escape(label)}</a>{escape(after)}</li>')
    if not rows:
        raise ValueError(f'Empty specification section: {heading}')
    spec_cards.append(f'<article class="panel"><h3>{escape(heading)}</h3><ul class="compact">{"".join(rows)}</ul></article>')
if not spec_cards:
    raise ValueError('Empty specification map')
body={
    'STYLE':(HERE/'atlas.css').read_text(encoding='utf8'),
    'DATA':json.dumps(values,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),
    'HERO':hero,
    'MOTIONS':str(len(motions['motions'])), 'CLIPS':str(len(base['clips'])),
    'SEQUENCES':str(len(base['sequence_previews'])),'PROFILES':str(len(supplemental['profiles'])),
    'CELLS':f'{original_cells+supplement_cells:,}', 'ORIGINAL':f'{original_cells:,}', 'SUPPLEMENTAL':str(supplement_cells),
    'MODULES':str(len(modules)),'REGRESSION':str(regression),
    'REQUIREMENTS':str(len(checks['requirement_trace'])),
    'FRAMEWORK':''.join(framework),
    **{f'SOURCE_{section.upper()}':escape(href(*ref), quote=True) for section, ref in sources.items()},
    'OBJECTS':objects,
    'PLAY_CONTROLS':html_table(*play_controls, render=keys_html),
    'VIEWER_CONTROLS':html_table(*viewer_controls, render=keys_html),
    'STATES':state_buttons,
    'STATE_NAME':escape(f'{initial} · {initial_title}'),
    'STATE_DETAIL':keys_html(initial_description),
    'STATE_EDGES':''.join(f'<li>{keys_html(edge)}</li>' for edge in initial_edges),
    'STATE_SUMMARY':state_summary,
    'ACTION_COUNT':str(len(states)),
    'PROGRESS_COUNT':str(len(progress)),
    'PROGRESS_STATES':''.join(f'<div><b>{escape(name)}</b><p>{keys_html(description)}</p></div>' for name, description in progress),
    'STATE_NOTES':keys_html(state_notes[1]),
    'MATERIAL_STATUS':html_table(*next(tables(read_section(*sources['materials']))),
                                 render=lambda value: re.sub(r'`([^`]+)`', r'<kbd>\1</kbd>', escape(value))),
    'GAME_TIMELINES':str(sum(key.startswith('game_') for key in motions['motions'])),
    'REPLAYS':str(sum(key.startswith('replay_') for key in motions['motions'])),
    'LAUNCHES':str(checks['input_replay']['launches']),
    'ELASTIC_LAUNCHES':str(checks['input_replay']['elastic_launches']),
    'SPEC_CARDS':''.join(spec_cards),
    'FILE_OPTIONS':''.join(f'<option value="{m["file"]}">{m["file"]}</option>' for m in modules),
    'DURATION':str(checks['input_replay']['seconds']),
    'NATIVE':f"{sum(v['sampled_poses_2p5ms'] for v in spin.values()):,}",
    'OPTIONS':''.join(f'<option value="{escape(t[0])}">{escape(t[1])}</option>' for t in replays),
}
document=re.sub(r'@@([A-Z_]+)@@',lambda m:body[m[1]],template)
assert not re.search(r'@@[A-Z_]+@@',document)
DEST.write_text(document,encoding='utf8')
print(f'{DEST} | {DEST.stat().st_size:,} bytes | {len(modules)} modules | {len(tiles)} embedded animation cells')
