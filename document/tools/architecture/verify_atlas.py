"""Verify reference integrity, offline resources, source links, and actual frame data."""
from base64 import b64decode
from collections import Counter
from html import escape
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import ast

from PIL import Image

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
artifact=PROJECT/'document/ToktogiProjectArchitecture.html'
doc=artifact.read_text(encoding='utf8')


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=Counter()
        self.links=[]
        self.resources=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids[attrs['id']]+=1
        if tag=='a' and 'href' in attrs:self.links.append(attrs['href'])
        if 'src' in attrs:self.resources.append(attrs['src'])
        if tag=='link' and 'href' in attrs:self.resources.append(attrs['href'])


parsed=Document();parsed.feed(doc)
assert all(count==1 for count in parsed.ids.values())
assert all(src.startswith('data:image/') for src in parsed.resources)
assert not re.search(r'@@[A-Z_]+@@',doc)

spec = PROJECT/'document/markdown/001_toktogi_game_design_spec.md'
contract = spec.read_text(encoding='utf8').split('<a id="atlas-sources"></a>', 1)[1]
sources = {}
for section, target in re.findall(r'^\| (\w+) \| \[[^\]]+\]\(([^)]+)\) \|', contract, re.M):
    ref = urlsplit(target)
    path = (spec.parent / unquote(ref.path)).resolve() if ref.path else spec
    sources[section] = path, ref.fragment

sections = dict(re.findall(r'<section id="([^"]+)"[^>]*>(.*?)</section>', doc, re.S))
assert sections.keys() == sources.keys()
for section, (path, anchor) in sources.items():
    markup = Document()
    markup.feed(sections[section])
    assert any(
        (artifact.parent / unquote(ref.path)).resolve() == path and ref.fragment == anchor
        for ref in map(urlsplit, markup.links) if ref.path
    ), section

game = sources['files'][0].parent
module_files={p.name for p in game.glob('*.py')}
for link in parsed.links:
    ref=urlsplit(link)
    assert not ref.scheme and not ref.netloc
    if ref.path:
        path = artifact.parent / unquote(ref.path)
        assert path.is_file(),link
        if ref.fragment and path.suffix == '.md':
            assert f'<a id="{ref.fragment}"></a>' in path.read_text(encoding='utf8'), link
    elif ref.fragment.startswith('files/'):
        assert 'files' in parsed.ids and ref.fragment[6:] in module_files,link
    else:assert ref.fragment in parsed.ids,link

specs_markup = sections['specs']
specs_html = Document()
specs_html.feed(specs_markup)
_, *card_links = [
    ((artifact.parent / unquote(ref.path)).resolve(), ref.fragment)
    for ref in map(urlsplit, specs_html.links)
]
map_path, map_anchor = sources['specs']
spec_map = map_path.read_text(encoding='utf8').split(f'<a id="{map_anchor}"></a>', 1)[1].split('\n## ', 2)[1]
assert re.findall(r'<h3>([^<]+)</h3>', specs_markup) == [
    escape(title) for title in re.findall(r'^### (.+)', spec_map, re.M)]
expected = []
for prefix, label, target, suffix in re.findall(r'^- (.*?)\[([^\]]+)\]\(([^)]+)\)(.*)$', spec_map, re.M):
    ref = urlsplit(target)
    expected.append(((spec.parent / unquote(ref.path)).resolve() if ref.path else spec, ref.fragment))
    assert f'<li>{escape(prefix)}<a ' in specs_markup
    assert f'>{escape(label)}</a>{escape(suffix)}</li>' in specs_markup
assert card_links == expected and card_links


def payload(s,id):
    return json.loads(re.search(fr'<script id="{id}" type="application/json">(.*?)</script>',s,re.S)[1])


data=payload(doc,'atlas-data')
original=payload(sources['motion'][0].read_text(encoding='utf8'),'motion-data')
motion_names = original['motions']
for prefix, label in [('game_', '실제 게임 시간표'), ('replay_', '입력 리플레이')]:
    assert f'{label} {sum(name.startswith(prefix) for name in motion_names)}개' in sections['motion']
assert f'총 {len(motion_names)}항목' in sections['motion']

state_text = sources['states'][0].read_text(encoding='utf8')
current_states = state_text.split(f'<a id="{sources["states"][1]}"></a>', 1)[1]
edges = re.search(r'~~~mermaid\nstateDiagram-v2\n(.*?)\n~~~', current_states, re.S)[1]
assert data['initialState'] == re.search(r'\[\*\] --> (\w+)', edges)[1]
for name, (_, _, actual) in data['states'].items():
    expected = [f'{condition} → {dest}' for dest, condition in re.findall(fr'^\s*{name} --> (\w+): (.+)$', edges, re.M)]
    assert actual == expected, name
    summary = re.search(fr'<th scope="row">{name}</th><td>(.*?)</td>', sections['states'])[1]
    assert summary.replace('<kbd>', '[').replace('</kbd>', ']') == escape(' · '.join(expected)), name
assert any(edge.endswith('→ Combat') and '[X]' in edge for edge in data['states']['Interact'][2])

materials = sources['materials'][0].read_text(encoding='utf8')
for name in ('Normal', 'Bloom'):
    status = re.search(fr'^\| {name} \|.*?\| ([^|]+) \|$', materials, re.M)[1]
    assert f'<td>{escape(status)}</td>' in sections['materials']
evidence = json.loads(sources['evidence'][0].read_bytes())
assert f'현행 하위 사례 {len(evidence["requirement_trace"])}건' in sections['evidence']
open_png=lambda uri:Image.open(BytesIO(b64decode(uri.split(',')[1]))).convert('RGBA')
atlas=open_png(data['atlas']);others={};count=0
for clip in data['videos']:
    source=original['motions'][clip['id']]
    frames=next(iter(source['tracks'].values()))
    assert len(clip['frames'])==len(frames) and clip['events']==source.get('events',[])
    for (tile,ms),(name,x,y,duration) in zip(clip['frames'],frames):
        if name not in others:others[name]=open_png(original['atlases'][name])
        i,j=128*(tile%data['columns']),128*(tile//data['columns'])
        assert ms==duration and atlas.crop((i,j,i+128,j+128)).tobytes()==others[name].crop((x,y,x+128,y+128)).tobytes()
        count+=1
assert {m['file'] for m in data['modules']}==module_files
classes=methods=imports=0
definition_types=(ast.FunctionDef,ast.AsyncFunctionDef)
for module in data['modules']:
    tree=ast.parse((game/module['file']).read_text(encoding='utf8'))
    source_classes=[n for n in tree.body if isinstance(n,ast.ClassDef)]
    assert [(c.name,c.lineno) for c in source_classes]==[(c['name'],c['line']) for c in module['classes']]
    assert [(n.name,n.lineno) for n in tree.body if isinstance(n,definition_types)]==[
        (n['name'],n['line']) for n in module['functions']]
    for c,entry in zip(source_classes,module['classes']):
        assert [(n.name,n.lineno) for n in c.body if isinstance(n,definition_types)]==[
            (n['name'],n['line']) for n in entry['methods']]
        methods+=len(entry['methods'])
    classes+=len(source_classes)
    source_imports=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom) and n.module and not n.level:
            source_imports.append((n.module,n.lineno))
        elif isinstance(n,ast.Import):
            source_imports.extend((a.name,n.lineno) for a in n.names)
    expected=Counter((name.split('.')[0]+'.py',line) for name,line in source_imports
                     if name.split('.')[0]+'.py' in module_files)
    assert expected==Counter((i['file'],i['line']) for i in module['imports']),module['file']
    imports+=len(module['imports'])
refs=[s for node in data['nodes'].values() for s in node['refs']]
for r in refs:
    assert r['symbol'] in (artifact.parent/r['path']).read_text(encoding='utf8').splitlines()[r['line']-1]

print(json.dumps({'verified_static_links':len(parsed.links),'verified_source_lines':len(refs),
                  'verified_modules':len(data['modules']),'classes':classes,'methods':methods,'imports':imports,
                  'pixel_and_timing_matches':count,'clips':len(data['videos'])}))
