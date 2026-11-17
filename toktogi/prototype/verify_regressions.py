"""Regression gates for the game review, independent of render frame rate."""
import os
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import ctypes
import json
from pathlib import Path
import statistics
import shutil
import tempfile
from time import perf_counter

import pygame as pg
from materials import Assets
from main import App,ROOT
from game import LEVEL,STEP,FOOD_TOUCH,BEACON_TOUCH,COLLECT_TOUCH,SHELL,segment_box
from input_clock import SDLEvent


def verify(*,quiet=False):
    app=App();g=app.game;a=app.assets
    checks={}

    def fresh(platform=LEVEL[0],x=150,view='right'):
        g.reset();g.support=platform;g.x=x;g.y=platform.y;g.view=view
        app.timeline.accumulator=app.timeline.wall_time=app.timeline.tick_wall=0.
        app.timeline.pending.clear();app.physical_keys.clear();app.scene='game'

    records=[]
    for release in (.15,.18):
        runs=[]
        for hz in (5,10,30,60,120):
            fresh(LEVEL[2],480)
            g.support=None;g.y=330.8;g.vy=300;g.clip='air_fall'
            for down,at in ((True,release-.01),(False,release)):
                app.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=pg.K_SPACE,mod=0),at=at)
            for _ in range(hz):app.update(1/hz)
            runs.append((hz,g.launch_count,g.elastic_count,round(g.x,7),round(g.y,7)))
        assert len({r[1:] for r in runs})==1,runs
        assert runs[0][2]==(1 if release==.15 else 0),runs
        records.append(runs)
    checks['timestamped_inputs_5_120fps']=records

    fresh()
    app.update(3.)
    assert app.timeline.overload and abs(g.time-2)<1e-8
    app.update(0.)
    assert not app.timeline.overload and abs(g.time-3)<1e-8
    checks['catch_up_debt_preserved']=True

    # A cancel quantized to the preparation boundary must beat the pending launch.
    fresh()
    for down,at in ((True,0.),(False,0.),(True,.08)):
        app.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=pg.K_SPACE,mod=0),at=at)
    app.update(.2)
    assert g.launch_count==0 and g.prep is None
    checks['preparation_boundary_cancel']=True

    # Inject into SDL's own queue, without sending input to an OS window.
    pg.event.clear()
    native=SDLEvent();native.words[0]=pg.KEYDOWN;native.words[1]=12345
    native.words[3]=1;native.words[4]=44;native.words[5]=pg.K_SPACE
    sdl=app.input_clock.sdl
    assert sdl.SDL_PeepEvents(ctypes.byref(native),1,0,pg.KEYDOWN,pg.KEYUP)==1
    keys=[e for e in app.input_clock.events() if e.type==pg.KEYDOWN]
    assert len(keys)==1 and keys[0].key==pg.K_SPACE and keys[0].timestamp==12345,keys
    checks['native_sdl_timestamp_preserved']=True

    bites=[]
    for hz in (5,10,30,60,120):
        fresh(LEVEL[0],FOOD_TOUCH[0]-29.84)
        for down,at in ((True,0.),(False,.86)):
            app.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=pg.K_f,mod=0),at=at)
        for _ in range(hz):app.update(1/hz)
        bites.append((hz,g.bites,g.food))
    assert len({r[1:] for r in bites})==1 and bites[0][1]==2,bites
    checks['feed_count_5_120fps']=bites

    fresh(LEVEL[0],FOOD_TOUCH[0]-29.84);g.edge('f',True)
    while not g.bites:g.step()
    bite_boundary=g.time
    fresh(LEVEL[0],FOOD_TOUCH[0]-29.84)
    app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_f,mod=0),at=0.)
    app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_p,mod=0),at=bite_boundary)
    for down in (True,False):
        app.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=pg.K_SPACE,mod=0),at=bite_boundary)
    app.update(.8)
    assert g.run=='Paused' and g.bites==1 and g.launch_count==0
    paused_time=g.time;app.update(.5)
    assert g.time==paused_time
    checks['pause_commit_boundary_and_closed_input']=True

    # Logical Idle in flight does not erase velocity or install a second launch.
    fresh();g.support=None;g.y=350;g.vy=-100;g.action='Jump'
    g.edge('space',True)
    assert g.action=='Idle' and g.vy==-100
    g.step();assert g.action=='Idle' and g.launch_count==0
    g.edge('space',False);assert g.action=='Jump' and g.prep is None
    checks['air_action_separate_from_motion']=True

    # Held movement stays physically available while the impact pose is shown.
    fresh(LEVEL[1],300);g.support=None;g.y=403.8;g.vy=300;g.vx=20;g.held={'right'};g.action='Jump'
    g.step();assert g.clip=='land_soft'
    landed=g.x
    for _ in range(8):g.step()
    assert g.clip=='land_soft' and g.x>landed
    checks['moving_landing_visible']=True

    slip=[]
    for view in ('left','right'):
        fresh(LEVEL[0],150,view);g.edge(view,True)
        history={};spans=[]
        for _ in range(120):
            g.step()
            if g.clip!='walk':continue
            markers,legs=a.sample(g.visual())
            for leg in ('LF','LM','LH','RF','RM','RH'):
                if leg not in legs and leg in history:
                    values=history.pop(leg);spans.append(max(values)-min(values))
            for leg in legs:history.setdefault(leg,[]).append(g.x+markers['foot_contact_'+leg]['xy'][0]-64)
        spans.extend(max(v)-min(v) for v in history.values())
        slip.append({'view':view,'max_stance_span_px':max(spans),'stride_px':g.stride})
    assert max(v['max_stance_span_px'] for v in slip)<3.,slip
    checks['walk_stance_slip']=slip

    # Admission and commit both use the selected work location, in both supported views.
    contacts=[]
    for view in ('left','right'):
        for key,p,target,clip,t in (
            ('f',LEVEL[0],FOOD_TOUCH,'feed_cycle',.22),
            ('e',LEVEL[1],BEACON_TOUCH,'interact_activate'+('_right' if view=='right' else ''),.20),
            ('e',LEVEL[2],COLLECT_TOUCH,'interact_collect'+('_right' if view=='right' else ''),.20)):
            fresh(p,150,view)
            marker='mouth_marker' if key=='f' else 'interaction_work_socket_RF' if view=='right' else 'interaction_work_socket'
            offset=g.socket(clip,t,marker)[0]-g.x
            g.x=target[0]-offset
            g.edge(key,True)
            assert g.work,(key,view,g.x)
            for _ in range(70):g.step()
            assert g.bites if key=='f' else g.beacon if p is LEVEL[1] else g.collected,(key,view)
            contacts.append((key,view,round(g.x,4)))
    for key,p,x in (('f',LEVEL[0],56),('e',LEVEL[1],373),('e',LEVEL[2],511)):
        fresh(p,x);g.edge(key,True)
        for _ in range(70):g.step()
        assert not(g.bites or g.beacon or g.collected),(key,x)
    checks['work_contact_admission_commit']=contacts

    for x,hit in ((671,False),(690,True)):
        fresh(LEVEL[3],x);g.edge('x',True);g.edge('x',False)
        for _ in range(70):g.step()
        assert (not g.shell)==hit and g.attack_hits==int(hit),(x,g.shell,g.attack_hits)
    fresh(LEVEL[3],690);g.edge('x',True)
    for _ in range(8):g.step()
    g.edge('space',True)
    for _ in range(50):g.step()
    assert g.shell and g.attack_hits==0
    checks['attack_hit_miss_cancel']=True
    assert segment_box((0,0),(1,1),(1,1,2,2))
    assert not segment_box((0,0),(1,1),(1,1,2,2),include_end=False)
    assert segment_box((1,1),(2,2),(1,1,2,2),include_end=False)
    checks['attack_active_end_excluded']=True

    for key in ('q','g'):
        fresh(LEVEL[0],150,'left');g.vx=-24;g.gait=.2;g.set_clip('walk',.2);g.was_walking=True;g.action='Walk'
        before=g.visual();g.edge(key,True);after=g.visual()
        assert (g.transition if key=='q' else g.work['next'])
        if key=='q':assert g.transition[0].cells[0][0]=='brake_05'
        else:assert g.clip=='brake_05'
        assert pg.image.tobytes(a.maps(before)['sprite'],'RGBA')==pg.image.tobytes(a.maps(after)['sprite'],'RGBA')
    fresh(LEVEL[0],150,'left');g.edge('g',True)
    for _ in range(150):g.step()
    before=g.visual();g.edge('g',False)
    assert g.work is None and g.visual()==before
    for _ in range(42):g.step()
    assert g.visual()[0]=='idle'
    checks['phase_brake_and_groom_return']=True

    fresh(LEVEL[0],200)
    for _ in range(300):g.step()
    markers,legs=a.sample(g.visual())
    assert g.action=='Idle' and all(g.support.x0<=g.x+markers['foot_contact_'+leg]['xy'][0]-64<=g.support.x1 for leg in legs)
    checks['edge_idle_balanced_x']=round(g.x,3)

    # Ceiling collision keeps the visible body outside the upper platform.
    fresh(LEVEL[3],840);g.shell=False;g.edge('space',True);g.edge('space',False)
    for _ in range(100):
        prev=g.vy;g.step()
        if prev<0 and g.vy==0 and g.support is None:break
    else:raise AssertionError('Ceiling contact did not occur')
    base=a.maps(g.visual())['base'];ox,oy=round(g.x)-64,round(g.y)-88;p=LEVEL[4]
    overlap=sum(bool(base.get_at((x,y)).a) and p.x0<=ox+x<p.x1 and p.y<=oy+y<p.bottom for y in range(128) for x in range(128))
    assert overlap==0,overlap
    checks['ceiling_surface_overlap_px']=overlap

    # Contact ink survives relighting and retains a genuine response to changed lights.
    ink=[]
    for i in (11,17):
        key=('obs_antenna_clean','left',i)
        images=[a.render(key,'lit',(0,0),light,power=.82,ambient=.34) for light in ((19,1),(119,31))]
        assert max(images[0].get_at((70,75))[:3])<100
        assert pg.image.tobytes(images[0],'RGB')!=pg.image.tobytes(images[1],'RGB')
        ink.append([i,list(images[0].get_at((70,75)))[:3]])
    checks['relit_contact_ink']=ink

    cells=a.tracks['obs_female_contact','left'].cells
    for c in cells:a.render(c,'lit',(0,0),(19,1))
    times=[]
    for _ in range(6):
        for c in cells:
            t=perf_counter();a.render(c,'lit',(0,0),(19,1));times.append((perf_counter()-t)*1000)
    checks['warm_large_scene_render_ms']={'median':round(statistics.median(times),4),'max':round(max(times),4)}
    assert max(times)<16.67
    c=cells[0]
    assert a.render(c,'lit',(0,0),(19,1)) is a.render(c,'lit',(10,20),(29,21))
    assert a.render(c,'lit',(0,0),(19,1)) is not a.render(c,'lit',(0,0),(20,1))
    checks['relative_light_cache_invalidation']=True

    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        directory=Path(tmp).resolve()
        assert directory.is_relative_to(ROOT.resolve())
        damaged=directory/'damaged.zip'
        shutil.copyfile(ROOT/'toktogi_assets.zip',damaged)
        shutil.copyfile(ROOT/'toktogi_assets.source.json',damaged.with_suffix('.source.json'))
        with damaged.open('r+b') as f:
            f.seek(1024);value=f.read(1);f.seek(1024);f.write(bytes((value[0]^1,)))
        try:Assets(damaged)
        except ValueError as e:assert 'checksum' in str(e)
        else:raise AssertionError('Damaged asset bundle was accepted')
    checks['asset_bundle_source_lock']=True

    a.close();pg.quit()
    (ROOT/'regression_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    if not quiet:print(json.dumps(checks,ensure_ascii=False,indent=2))
    return checks


if __name__=='__main__':verify()
