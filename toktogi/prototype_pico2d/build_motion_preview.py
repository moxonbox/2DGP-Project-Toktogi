"""Build the standalone 128px motion catalog from an integrated asset bundle."""
import base64
from collections import defaultdict
import hashlib
from html import escape
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import os

from PIL import Image
from zipfile import ZipFile

from materials import Assets
from motion import MotionSet
from replays import game_replays,world_replays

workspace = Path(__file__).resolve().parents[2]
bundle = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else workspace / 'asset/C/C011_toktogi/2D/integrated-r5'
output = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).with_name('ToktogiMotionPreview.html')
manifest = json.loads((bundle / 'playable_manifest.json').read_text(encoding='utf-8'))

groups = {
    'game': '게임 재생 시간',
    'move': '대기·이동', 'jump': '도약·낙하·회복', 'turn': '회전·조준', 'work': '상호작용·반응',
    'groom': '손질', 'study': '관찰 모션', 'sequence': '전환 시퀀스',
}
names = {
    'idle': '대기', 'walk_start': '보행 시작', 'walk': '보행', 'brake': '제동',
    'aim_up': '위쪽 조준', 'aim_down': '아래쪽 조준', 'aim_return_up': '위쪽 조준 복귀', 'aim_return_down': '아래쪽 조준 복귀',
    'jump_pre': '도약 준비', 'jump_release': '도약 발사', 'air_rise': '공중 상승', 'air_apex': '도약 정점', 'air_fall': '공중 하강',
    'fall_unlaunched': '발사 없는 낙하', 'fall_unlaunched_charged': '준비 중 지지 상실', 'land_soft': '가벼운 착지',
    'land_hard': '강한 착지', 'jump_blocked': '도약 차단', 'recovery_walk': '회복 중 보행', 'recovery_start': '착지 후 회복 시작',
    'recovery_jump_pre': '회복 중 재도약 준비', 'elastic_release': '탄성 도약 발사', 'interact_activate': '대상 활성화',
    'interact_collect': '대상 수집', 'interact_activate_right': '대상 활성화 · 오른쪽', 'interact_collect_right': '대상 수집 · 오른쪽',
    'feed_pre': '섭식 준비', 'feed_cycle': '섭식 반복', 'feed_end': '섭식 종료', 'attack_demo': '공격 예시',
    'hit_ground': '지상 피격', 'hit_air': '공중 피격', 'goal': '목표 도달', 'failed': '실패', 'respawn': '재시작',
    'turn_left_right': '왼쪽에서 오른쪽으로 회전', 'turn_right_left': '오른쪽에서 왼쪽으로 회전', 'turn_full_ccw': '360° 반시계 회전',
    'turn_full_cw': '360° 시계 회전', 'air_turn_ccw': '공중 반시계 회전', 'air_turn_cw': '공중 시계 회전',
    'obs_rest': '정지 관찰', 'obs_walk': '보행 관찰', 'obs_jump': '지면 도약 관찰', 'obs_graze': '먹이 섭식 관찰',
    'obs_antenna_clean': '더듬이 손질', 'obs_furca_clean': '도약기관 손질', 'obs_saliva_clean': '방울을 이용한 손질',
    'obs_bark': '구기의 이물질 제거 시도', 'obs_female_contact': '암컷 간 접촉', 'obs_rebuff': '접근에 대한 거부 반응',
    'obs_juvenile_clasp': '유체의 더듬이 결속', 'obs_wrong_grasp': '뒤쪽 부착 사례', 'obs_male_contact': '수컷 간 접촉',
    'obs_approach': '개체 접근', 'obs_clasp': '더듬이 결속', 'obs_carry': '운반', 'obs_dance': '결속 상태의 방향 전환',
    'obs_pair_jump': '결속 상태의 지면 도약', 'obs_antenna_to_furca': '더듬이에서 도약기관 손질로 연결',
}
sequence_names = dict(zip((
    'playable_preview', 'transition_groom', 'transition_carry_dance', 'transition_flight', 'transition_turn',
    'transition_turn_reverse', 'transition_feed', 'transition_elastic_soft', 'transition_support_loss', 'transition_aim_return',
    'turn_full_ccw', 'turn_full_cw', 'air_turn_ccw_full', 'air_turn_ccw_mid_land', 'air_turn_cw_full', 'air_turn_cw_mid_land',
    'transition_antenna_furca',
), (
    '플레이어 모션 모음', '손질에서 도약으로', '운반에서 방향 전환으로', '도약·비행·착지', '좌에서 우로 회전',
    '우에서 좌로 회전', '섭식 준비·반복·종료', '탄성 도약에서 가벼운 착지로', '지지 상실에서 낙하로', '조준에서 대기로 복귀',
    '보행·제동·360° 반시계 회전', '대기·360° 시계 회전', '공중 반시계 회전 후 착지', '공중 반시계 회전 도중 낙하',
    '공중 시계 회전 후 착지', '공중 시계 회전 도중 낙하', '더듬이 손질에서 도약기관 손질로',
)))


def category(name):
    if name in {'obs_antenna_clean','obs_furca_clean','obs_saliva_clean','obs_antenna_to_furca'}:
        return 'groom'
    if name.startswith('obs_'):
        return 'study'
    if name.startswith(('turn_','air_turn_','aim_')):
        return 'turn'
    if name.startswith(('jump_','air_','fall_','land_','recovery_','elastic_')):
        return 'jump'
    if name.startswith(('idle','walk','brake')):
        return 'move'
    return 'work'


def uri(blob):
    return 'data:image/png;base64,' + base64.b64encode(blob).decode('ascii')


def view_label(view):
    return {'left':'왼쪽','right':'오른쪽 (호환)','sequence':'시퀀스 지정'}.get(view, view.replace('yaw_', '')+'°')


atlases, images = {}, {}
for view, files in manifest['pass_files'].items():
    info = files['sprite']
    source = bundle / info['file']
    blob = source.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == info['sha256'], source
    atlases[view] = uri(blob)
    with Image.open(source) as image:
        assert list(image.size) == info['size']
        images[view] = image.convert('RGBA')


def frame(sample, view):
    x,y,w,h = sample['views'][view]['rect']
    assert (w,h)==(128,128) and 0<=x<=images[view].width-w and 0<=y<=images[view].height-h
    return [view,x,y,sample['duration_s']*1000]


def poster(first):
    view,x,y,_ = first
    data = BytesIO()
    images[view].crop((x,y,x+128,y+128)).save(data,format='PNG',optimize=True)
    return uri(data.getvalue())


cards = defaultdict(list)
motions = {}
checker = Image.new('RGBA',(128,128))
checker.putdata([(222,230,233,255) if (x//8+y//8)%2 else (242,244,245,255) for y in range(128) for x in range(128)])


def register(key, label, group, tracks, preview, detail=''):
    default_track = next(iter(tracks.values()))
    loop = False
    if preview:
        with Image.open(bundle/preview) as original:
            assert original.size==(128,128) and original.n_frames==len(default_track), preview
            loop = original.info.get('loop',1)==0
            for i,(view,x,y,ms) in enumerate(default_track):
                original.seek(i)
                cell = images[view].crop((x,y,x+128,y+128))
                assert original.convert('RGBA').tobytes()==Image.composite(cell,checker,cell.getchannel('A')).tobytes(), (preview,i)
                assert abs(original.info.get('duration',ms)-ms)<.01, (preview,i)
    assert key not in motions
    motions[key] = {'tracks':tracks,'loop':loop}
    thumb = poster(default_track[0])
    count = len(default_track)
    duration = sum(s[3] for s in default_track)/1000
    options = ''.join(f'<option value="{escape(v)}">{escape(view_label(v))}</option>' for v in tracks)
    direction = (f'<label class="view-label">방향<select data-view>{options}</select></label>' if len(tracks)>1
                 else f'<span class="single-view">{escape(view_label(next(iter(tracks))))}</span>')
    searchable = escape(' '.join((label,key,detail,groups[group])).casefold(),quote=True)
    cards[group].append(f'''<article class="card" id="motion-{escape(key)}" data-motion="{escape(key)}" data-search="{searchable}">
      <div class="media"><img src="{thumb}" alt="" width="128" height="128" loading="lazy"><canvas width="128" height="128" role="img" aria-label="{escape(label)} 프리뷰" hidden></canvas></div>
      <div class="card-copy"><h3>{escape(label)}</h3><p class="motion-id">{escape(key)}</p>
      {f'<p class="detail">{escape(detail)}</p>' if detail else ''}
      <p class="meta">{count} 프레임 <span>·</span> {duration:.2f}초 <span>·</span> {'반복' if loop else '1회'}</p></div>
      <div class="controls"><button class="play" type="button" data-play aria-label="{escape(label)} 재생">재생</button>
      <button type="button" data-reset aria-label="{escape(label)} 첫 프레임으로">처음</button>{direction}</div>
      <div class="scrubber"><input type="range" min="1" max="{count}" value="1" aria-label="{escape(label)} 프레임" {'disabled' if count==1 else ''}><span data-frame>1 / {count}</span></div>
    </article>''')
    return thumb


hero = ''
for key, clip in manifest['clips'].items():
    suffix = re.fullmatch(r'(brake|recovery_jump_pre)_(\d+)',key)
    label = names[key] if key in names else f'{names[suffix[1]]} · 위상 {suffix[2]}' if suffix else key
    tracks = {v:[frame(s,v) for s in clip['samples']] for v in clip['supported_views']}
    thumb = register(key,label,category(key),tracks,clip['preview_apng'],clip.get('description',''))
    if key=='idle':
        hero = thumb

for filename, segments in manifest['sequence_previews'].items():
    key = Path(filename).stem
    track = []
    for s in segments:
        start = s.get('start_sample',0)
        samples = manifest['clips'][s['clip']]['samples']
        assert start+s['sample_count']<=len(samples)
        track.extend(frame(p,s['view']) for p in samples[start:start+s['sample_count']])
    register('sequence-'+key,sequence_names.get(key,key),'sequence',{'sequence':track},filename)

overlay=Path(__file__).resolve().with_name('toktogi_runtime_poses.zip')
pose_frames={}
with ZipFile(overlay) as packed:
    runtime=json.loads(packed.read('runtime_poses.json'))
    for name,profile in runtime['profiles'].items():
        atlas_id='runtime:'+name
        frames=profile['cells'];image=Image.new('RGBA',(128*len(frames),128))
        for i,(clip,view,index) in enumerate(frames):
            if clip in manifest['clips']:
                sample=manifest['clips'][clip]['samples'][index]
                x,y,_,_=sample['views'][view]['rect'];cell=images[view].crop((x,y,x+128,y+128))
            else:
                cell=Image.open(BytesIO(packed.read(f'{clip}/{view}/{index}.png'))).crop((0,0,128,128))
            image.paste(cell,(i*128,0))
        images[atlas_id]=image
        blob=BytesIO();image.save(blob,format='PNG');atlases[atlas_id]=uri(blob.getvalue())
        track=[[atlas_id,i*128,0,seconds*1000] for i,seconds in enumerate(profile['durations'])]
        for cell,rect in zip(frames,track):
            pose_frames.setdefault(tuple(cell),rect[:3])
        register('runtime_'+name,name,'sequence',{'sequence':track},None)

assets=Assets(overlay.with_name('toktogi_assets.zip'),overlay)
assert assets.manifest['bundle_contract_signature']==manifest['bundle_contract_signature']
policy=MotionSet(assets)
game_count=0
replay_trace={}
previews=[(name,track,()) for name,track in policy.game_previews()]+list(game_replays(assets,trace=replay_trace))+list(world_replays(assets,trace=replay_trace))
for name,track,events in previews:
    frames=[]
    for (clip,view,index),seconds in zip(track.cells,track.durations):
        if clip in manifest['clips']:
            rect=frame(manifest['clips'][clip]['samples'][index],view)[:3]
        else:
            rect=pose_frames[clip,view,index]
        frames.append([*rect,seconds*1000])
    detail=' · '.join(f'{label} {t:.3f}s' for label,t in events)
    register(name,name,'game',{'sequence':frames},None,detail)
    if name.startswith('replay_'):
        motions[name]['events']=events
        motions[name]['trace']=replay_trace[name]
    game_count+=1
assets.close()
assert len(motions)==len(manifest['clips'])+len(manifest['sequence_previews'])+len(runtime['profiles'])+game_count

nav = ''.join(f'<a href="#{key}">{label}<span>{len(cards[key])}</span></a>' for key,label in groups.items() if cards[key])
options = ''.join(f'<option value="{key}">{label}</option>' for key,label in groups.items() if cards[key])
sections = ''.join(f'''<section class="group" id="{key}" aria-labelledby="{key}-heading">
    <div class="section-head"><h2 id="{key}-heading">{label}</h2><span data-section-count>{len(cards[key])}개</span></div>
    <div class="grid">{''.join(cards[key])}</div></section>''' for key,label in groups.items() if cards[key])

template = r'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light"><title>톡토기 모션 미리보기 · @@REV@@</title>
<style>
:root{--paper:#f7f7f2;--ink:#19251e;--muted:#536158;--line:#d9e0d7;--tint:#e5ebe1;--accent:#315b43;--white:#fff;--gutter:clamp(14px,3vw,40px);font-family:"Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;color:var(--ink);background:var(--paper)}
*,*::before,*::after{box-sizing:border-box}body{margin:0;line-height:1.55}[hidden]{display:none!important}a{color:inherit}button,input,select{font:inherit}button,select{cursor:pointer}button:disabled{cursor:wait}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #34734e;outline-offset:3px}[id]{scroll-margin-top:78px}.wrap{width:min(calc(100% - 2*var(--gutter)),1260px);margin-inline:auto}
.topbar{position:sticky;top:0;z-index:3;background:#f7f7f2f4;border-bottom:1px solid var(--line);backdrop-filter:blur(12px)}.bar{min-height:60px;display:flex;align-items:center;justify-content:space-between;gap:12px}.brand,.top-links a{text-decoration:none;font-weight:750}.brand{letter-spacing:-.03em}.top-links{display:flex;gap:4px}.top-links a{padding:8px 11px;border-radius:8px;color:var(--muted);font-size:.84rem}.top-links a:hover,.category-nav a:hover{background:var(--tint);color:var(--accent)}
.masthead{margin-top:26px;display:grid;grid-template-columns:1.08fr 1fr;min-height:265px;overflow:hidden;border:1px solid var(--line);border-radius:28px;background:var(--tint)}.hero-copy{align-self:center;padding:clamp(23px,4vw,52px)}.revision{margin:0 0 8px;color:var(--accent);font-size:.77rem;font-weight:750;letter-spacing:.08em}h1{margin:0;font-size:clamp(2rem,4.8vw,3.55rem);line-height:1.15;letter-spacing:-.07em}.hero-copy p:last-child{margin:16px 0 0;color:var(--muted);font-size:.93rem;word-break:keep-all}.hero-media{display:grid;place-items:center;margin:0;min-height:220px;background:#293a32}.hero-media img{width:min(90%,256px);height:auto;image-rendering:pixelated}
.quick{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin:16px 0 22px;background:#fff;border:1px solid var(--line);border-radius:17px}.quick div{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px;padding:12px 17px}.quick div+div{border-left:1px solid var(--line)}.quick dt{order:1;color:var(--muted);font-size:.81rem}.quick dd{margin:0;color:var(--accent);font-size:1.36rem;font-weight:800}
.toolbar{display:grid;grid-template-columns:minmax(0,1fr) minmax(135px,205px) auto auto;gap:11px;align-items:end;padding:14px 17px;background:#fff;border:1px solid var(--line);border-radius:16px}.toolbar label{display:grid;gap:4px;font-size:.81rem;font-weight:700;color:var(--muted)}.toolbar input,.toolbar select,.toolbar button{min-height:41px;border:1px solid #b6c2b7;border-radius:8px;color:var(--ink);background:#fff;padding:7px 10px;min-width:0}.toolbar output{padding-block:9px;font-size:.83rem;color:var(--muted);white-space:nowrap}.toolbar button:hover,.controls button:hover{background:var(--tint)}
.layout{display:grid;grid-template-columns:168px minmax(0,1fr);gap:23px;padding-top:26px}.sidebar{align-self:start;position:sticky;top:80px}.sidebar h2{margin:0 0 7px;padding-left:8px;font-size:.84rem;color:var(--muted)}.category-nav{display:grid;gap:2px}.category-nav a{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:7px 9px;border-radius:8px;text-decoration:none;font-size:.84rem;font-weight:700;white-space:nowrap}.category-nav span{font-size:.73rem;color:var(--muted)}.group{margin-bottom:34px}.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px;padding-bottom:10px;margin-bottom:14px;border-bottom:1px solid var(--line)}.section-head h2{margin:0;font-size:1.54rem;letter-spacing:-.05em}.section-head span{color:var(--muted);font-size:.83rem}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:start}
.card{min-width:0;overflow:hidden;border:1px solid var(--line);border-radius:18px;background:#fff}.card.is-active{border-color:var(--accent)}.media{display:grid;place-items:center;min-height:208px;height:clamp(208px,24vw,256px);overflow:hidden;background:#edf0ea repeating-conic-gradient(#e1e7e0 0% 25%,#f1f3ee 0% 50%) 0 0/24px 24px}.media img,.media canvas{width:auto;height:100%;max-width:100%;object-fit:contain;image-rendering:pixelated}.card-copy{padding:13px 16px 9px}.card h3{margin:0;line-height:1.4;font-size:1.04rem;letter-spacing:-.035em;overflow-wrap:anywhere}.motion-id,.detail,.meta{margin:4px 0;color:var(--muted);font-size:.78rem;overflow-wrap:anywhere}.motion-id{font-family:ui-monospace,Consolas,monospace}.detail{font-size:.83rem;word-break:keep-all}.meta span{margin-inline:3px}.controls{display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:8px 14px;border-top:1px solid #edf0eb}.controls button,.controls select{padding:5px 9px;min-height:36px;min-width:0;border:1px solid #b6c2b7;border-radius:8px;background:#fff;color:var(--ink);font-size:.81rem}.controls .play{background:var(--accent);border-color:var(--accent);color:#fff;min-width:80px}.controls .play:hover{background:#234b34}.view-label{display:flex;align-items:center;gap:5px;margin-left:auto;font-size:.74rem;color:var(--muted)}.single-view{margin-left:auto;font-size:.75rem;color:var(--muted)}.scrubber{display:flex;align-items:center;gap:9px;padding:1px 15px 12px;color:var(--muted);font-size:.74rem;font-variant-numeric:tabular-nums}.scrubber input{margin:0;flex:1;min-width:0;accent-color:var(--accent)}.scrubber span{white-space:nowrap}.empty{padding:32px 12px;margin:0 0 28px;text-align:center;color:var(--muted);border:1px dashed #aebcaf;border-radius:14px}.footer{padding:14px 0 25px;border-top:1px solid var(--line);font-size:.8rem;color:var(--muted)}.error{margin:12px 0;color:#9a2925;font-weight:700}
@media(max-width:760px){.layout{display:block;padding-top:18px}.sidebar{position:static;margin-bottom:16px}.category-nav{display:flex;overflow:auto;padding-bottom:6px;gap:5px}.category-nav a{border:1px solid var(--line);background:#fff}.toolbar{grid-template-columns:minmax(0,1fr) auto auto}.toolbar .search{grid-column:1/-1}}
@media(max-width:535px){.masthead{grid-template-columns:1fr;border-radius:20px}.hero-media{min-height:170px}.hero-media img{width:192px}.grid{grid-template-columns:1fr}.quick div{padding-inline:9px;display:grid;gap:0}.quick dd{font-size:1.2rem}.quick dt{font-size:.72rem}.top-links a{padding-inline:5px}.media{height:216px}}
</style>
</head>
<body id="top">
<header class="topbar"><div class="wrap bar"><a class="brand" href="#top">톡토기 모션 목록</a><nav class="top-links" aria-label="페이지 탐색"><a href="#catalog">검색</a><a href="#sequence">전환 시퀀스</a></nav></div></header>
<main class="wrap">
  <header class="masthead"><div class="hero-copy"><p class="revision">@@REV@@</p><h1>톡토기 모션<br>한눈에 보기</h1><p>카드에서 모션을 재생하고, 지원 방향과 128px 원본 프레임을 확인하세요.</p></div><figure class="hero-media"><img src="@@HERO@@" alt="톡토기 대기 자세" width="128" height="128"></figure></header>
  <dl class="quick" aria-label="프리뷰 요약"><div><dt>모션 클립</dt><dd>@@CLIPS@@</dd></div><div><dt>전환 시퀀스</dt><dd>@@SEQUENCES@@</dd></div><div><dt>지원 뷰</dt><dd>@@VIEWS@@</dd></div></dl>
  <section class="toolbar" id="catalog" aria-label="모션 검색 및 필터"><label class="search">모션 검색<input id="query" type="search" placeholder="예: 더듬이, jump, 회전" autocomplete="off"></label><label>카테고리<select id="category"><option value="">전체 카테고리</option>@@OPTIONS@@</select></label><button type="button" id="clear">초기화</button><output id="result" aria-live="polite" for="query category">@@TOTAL@@개</output></section>
  <noscript><p class="error">재생하려면 JavaScript를 켜세요.</p></noscript><p id="error" class="error" role="alert" hidden></p>
  <div class="layout"><aside class="sidebar"><h2>카테고리 바로가기</h2><nav class="category-nav" aria-label="카테고리 바로가기">@@NAV@@</nav></aside><div id="list"><p id="empty" class="empty" hidden>검색 조건에 맞는 모션이 없습니다.</p>@@SECTIONS_HTML@@</div></div>
  <footer class="footer">@@REV@@ · Sprite 패스 · 원본 128×128px · 오프라인 재생</footer>
</main>
<script id="motion-data" type="application/json">@@DATA@@</script>
<script>
"use strict";
const {atlases,motions} = JSON.parse(document.getElementById('motion-data').textContent);
const list = document.getElementById('list');
const groups = [...list.querySelectorAll('.group')];
const query = document.getElementById('query');
const category = document.getElementById('category');
const error = document.getElementById('error');
const images = new Map();
let current;

function atlas(view) {
  if (!images.has(view)) {
    const image = new Image();
    image.src = atlases[view];
    images.set(view, image.decode().then(() => image).catch(reason => {
      images.delete(view);
      throw reason;
    }));
  }
  return images.get(view);
}
function updateButton(state, text) {
  state.button.textContent = text;
  state.button.setAttribute('aria-label', `${state.title} ${text}`);
}
function pause(state) {
  if (!state) return;
  state.playing = false;
  cancelAnimationFrame(state.raf);
  updateButton(state, state.done ? '다시 재생' : '재생');
}
function paint(state, index) {
  if (state.index === index) return;
  const [view,x,y] = state.frames[index];
  state.ctx.clearRect(0,0,128,128);
  state.ctx.drawImage(state.assets[view],x,y,128,128,0,0,128,128);
  state.index = index;
  state.slider.value = index+1;
  state.slider.setAttribute('aria-valuetext', `${index+1} / ${state.frames.length} 프레임`);
  state.label.textContent = `${index+1} / ${state.frames.length}`;
}
async function openCard(card) {
  const motion = motions[card.dataset.motion];
  const track = card.querySelector('[data-view]')?.value ?? Object.keys(motion.tracks)[0];
  if (current?.card===card && current.track===track) return current.ready;
  pause(current);
  current?.card.classList.remove('is-active');
  const frames = motion.tracks[track];
  let sum = 0;
  const ends = frames.map(frame => sum+=frame[3]);
  const canvas = card.querySelector('canvas');
  const state = {card,track,frames,ends,total:sum,loop:motion.loop,position:0,index:-1,playing:false,done:false,
                 canvas,ctx:canvas.getContext('2d'),button:card.querySelector('[data-play]'),title:card.querySelector('h3').textContent,
                 slider:card.querySelector('input[type=range]'),label:card.querySelector('[data-frame]')};
  current = state;
  card.classList.add('is-active');
  state.button.disabled = true;
  updateButton(state,'준비 중');
  error.hidden = true;
  const required = [...new Set(frames.map(frame => frame[0]))];
  for (const view of images.keys()) if (!required.includes(view)) images.delete(view);
  state.ready = Promise.all(required.map(async view => [view,await atlas(view)])).then(entries => {
    if (current!==state) return null;
    state.assets = Object.fromEntries(entries);
    state.ctx.imageSmoothingEnabled = false;
    paint(state,0);
    canvas.hidden = false;
    card.querySelector('.media img').hidden = true;
    updateButton(state,'재생');
    return state;
  }).catch(() => {
    if (current===state) {
      error.textContent = `${state.title} 프리뷰를 읽지 못했습니다.`;
      error.hidden = false;
      updateButton(state,'재시도');
      current = null;
      card.classList.remove('is-active');
    }
    return null;
  }).finally(() => { state.button.disabled = false; });
  return state.ready;
}
function play(state) {
  if (state.done) { state.position=0; state.done=false; }
  state.playing=true;
  state.since=performance.now()-state.position;
  updateButton(state,'일시정지');
  function tick(now) {
    if (state!==current || !state.playing) return;
    const elapsed=Math.max(0,now-state.since);
    if (!state.loop && elapsed>=state.total) {
      state.position=state.total;
      state.done=true;
      paint(state,state.frames.length-1);
      pause(state);
      return;
    }
    state.position=elapsed%state.total;
    paint(state,state.ends.findIndex(end=>end>state.position));
    state.raf=requestAnimationFrame(tick);
  }
  state.raf=requestAnimationFrame(tick);
}
function seek(state, index) {
  pause(state);
  state.done=false;
  state.position=index>0 ? state.ends[index-1] : 0;
  paint(state,index);
  updateButton(state,'재생');
}
list.addEventListener('click',async ({target})=>{
  const button=target.closest('[data-play],[data-reset]');
  if (!button) return;
  const card=button.closest('.card');
  if (button.hasAttribute('data-play') && current?.card===card && current.playing) { pause(current); return; }
  const state=await openCard(card);
  if (!state || current!==state) return;
  if (button.hasAttribute('data-reset')) seek(state,0); else play(state);
});
list.addEventListener('change',async ({target})=>{
  if (target.matches('[data-view]')) await openCard(target.closest('.card'));
});
list.addEventListener('input',async ({target})=>{
  if (!target.matches('input[type=range]')) return;
  const index=Number(target.value)-1;
  const state=await openCard(target.closest('.card'));
  if (state && current===state) seek(state,index);
});
function filter() {
  const terms=query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  let count=0;
  for (const group of groups) {
    let shown=0;
    for (const card of group.querySelectorAll('.card')) {
      card.hidden=!!(category.value && category.value!==group.id) || !terms.every(term=>card.dataset.search.includes(term));
      if (!card.hidden) shown++;
    }
    group.hidden=shown===0;
    group.querySelector('[data-section-count]').textContent=`${shown}개`;
    count+=shown;
  }
  if (current?.card.hidden) pause(current);
  document.getElementById('result').textContent=`${count} / ${Object.keys(motions).length}개`;
  document.getElementById('empty').hidden=count>0;
}
query.addEventListener('input',filter);
category.addEventListener('change',filter);
document.getElementById('clear').addEventListener('click',()=>{ query.value=''; category.value=''; filter(); query.focus(); });
document.querySelectorAll('a[href^="#"]').forEach(link=>link.addEventListener('click',()=>{
  const group=document.getElementById(link.hash.slice(1));
  if (group?.classList.contains('group') && group.hidden) { query.value=''; category.value=''; filter(); }
}));
document.addEventListener('visibilitychange',()=>{ if (document.hidden) pause(current); });
</script>
</body></html>'''

values = {
    'REV':escape(manifest['asset_revision']+' / '+runtime['revision']), 'HERO':hero, 'CLIPS':str(len(manifest['clips'])),
    'SEQUENCES':str(len(manifest['sequence_previews'])+len(runtime['profiles'])+game_count), 'VIEWS':str(len(manifest['pass_files'])), 'OPTIONS':options,
    'TOTAL':str(len(motions)), 'NAV':nav, 'SECTIONS_HTML':sections,
    'DATA':json.dumps({'atlases':atlases,'motions':motions},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),
}
html = re.sub(r'@@([A-Z_]+)@@',lambda match:values[match[1]],template)
output.write_text(html,encoding='utf-8')
print(f'{output.name}: {len(motions)} cards, {len(atlases)} views, {output.stat().st_size:,} bytes')
