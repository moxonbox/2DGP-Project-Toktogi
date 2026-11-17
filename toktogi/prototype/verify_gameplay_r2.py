"""App-boundary regressions for the twelve gameplay-r1 review findings."""
import os
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import json,math,statistics
from zipfile import ZipFile
from time import perf_counter
import pygame as pg
from main import App,ROOT
from game import LEVEL,STEP,BEACON_TOUCH,FOOD_TOUCH


def verify(*,quiet=False):
    app=App();g=app.game;a=app.assets;checks={}
    def fresh(p=LEVEL[0],x=150,view='right'):
        g.reset();g.support=p;g.x=x;g.y=p.y;g.view=view
        app.timeline.accumulator=app.timeline.wall_time=app.timeline.tick_wall=0.
        app.timeline.pending.clear();app.physical_keys.clear();app.scene='game';app.focused=True
    def key(k,down,at):
        app.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=k,mod=0),at=at)
    def ticks(n):
        for _ in range(n):app.update(STEP)
    def delta(c,d):
        return sum(x!=y for x,y in zip(*(pg.image.tobytes(a.maps(k)['sprite'],'RGBA')[3::4] for k in (c,d))))
    noise=[]
    for kind in (None,pg.MOUSEMOTION,pg.WINDOWEXPOSED,pg.KEYUP):
        fresh();key(pg.K_SPACE,True,0.);key(pg.K_SPACE,False,0.)
        if kind==pg.KEYUP:key(pg.K_a,False,.08)
        elif kind:app.event(pg.event.Event(kind),at=.08)
        key(pg.K_SPACE,True,.08);app.update(.2)
        noise.append(g.launch_count)
    assert noise==[0]*4,noise
    fresh(x=100.1625);key(pg.K_f,True,0.)
    while not g.bites:app.update(STEP)
    boundary=g.time;counts=[]
    for noisy in (False,True):
        fresh(x=100.1625);key(pg.K_f,True,0.)
        if noisy:app.event(pg.event.Event(pg.MOUSEMOTION),at=boundary)
        key(pg.K_f,False,boundary);app.update(.6);counts.append(g.bites)
    assert counts==[0,0],counts
    checks['irrelevant_events_preserve_cancel']={'launches':noise,'bites':counts}

    fresh(LEVEL[3],690);key(pg.K_x,True,.05)
    accepted=None;first=None
    for _ in range(30):
        app.update(STEP)
        if g.work:
            accepted=g.work['started_at']
            assert abs(g.work['age']-(g.time-accepted))<1e-8
            assert abs(g.work['age']-g.visual_time)<1e-8
        if g.attack_hits:first=g.time;break
    assert first is not None and first-accepted>=.078-1e-9,(accepted,first)
    fresh(LEVEL[1],336.9);key(pg.K_e,True,.05)
    commit=None
    for _ in range(60):
        app.update(STEP)
        if g.beacon:
            distance=math.dist(g.socket(g.clip,g.visual_time,'interaction_work_socket_RF'),BEACON_TOUCH)
            assert distance<=3.5,distance
            commit={'elapsed':g.time-g.work['started_at'],'distance_px':distance};break
    assert commit is not None
    checks['shared_work_clock']={'first_attack_elapsed':first-accepted,'activation':commit}

    fresh(x=200);moving=[]
    for _ in range(300):
        app.update(STEP)
        if abs(g.vx)>.1:moving.append((g.action,g.visual()[0]))
    assert moving and all(action=='Walk' for action,_ in moving),moving[:10]
    assert g.action=='Idle' and g.x<200
    checks['automatic_balance_app']={'end_x':g.x,'moving_actions':sorted(set(action for action,_ in moving))}

    exits=[]
    for phase in range(len(a.clips['walk']['samples'])):
        for command in (pg.K_q,pg.K_g,pg.K_x):
            fresh(view='left');g.vx=-24;g.gait=a.tracks['walk','left'].start(phase)
            g.set_clip('walk',g.gait);g.was_walking=True;g.action='Walk';g.held={'left'}
            key(command,True,0.);key(pg.K_LEFT,False,0.);started=False
            for _ in range(700):
                app.update(STEP)
                if g.work or g.transition:started=True
                elif started:break
            assert started and not g.work and g.clip=='idle' and not g.was_walking,(phase,command,g.clip)
            ticks(3);assert not g.clip.startswith('brake'),g.clip
            exits.append((phase,command))
    checks['all_gait_work_natural_exits']=len(exits)

    jumps=[]
    for clip in ('land_soft','land_hard'):
        for view in ('left','right'):
            for i in range(len(a.clips[clip]['samples'])):
                fresh(LEVEL[1],300,view);g.gait=.2;g.recovery=.27;g.set_clip(clip,a.tracks[clip,view].start(i))
                previous=g.visual();key(pg.K_SPACE,True,0.);key(pg.K_SPACE,False,0.);app.update(0.)
                assert g.visual()==previous,(previous,g.visual())
                ticks(10);assert g.launch_count==1
                jumps.append((clip,view,i))
    checks['recovery_jump_uses_visible_landing']=len(jumps)

    returns=[]
    for hz in (10,15,30,60):
        fresh(view='left');key(pg.K_g,True,0.);ticks(375)
        before=g.visual();key(pg.K_RIGHT,True,app.timeline.wall_time);key(pg.K_g,False,app.timeline.wall_time);app.update(0.)
        assert g.visual()==before
        samples=[];previous=before
        for _ in range(math.ceil(.4*hz)):
            app.update(1/hz);current=g.visual();samples.append(delta(previous,current));previous=current
        assert g.view=='right' and g.transition is None
        # The last frame is already the target heading; no delayed whole-body flip.
        assert samples[-1]<500,samples
        returns.append({'hz':hz,'max_alpha_delta_px':max(samples),'final_delta_px':samples[-1]})
    checks['direct_groom_return_10_60fps']=returns

    fresh(LEVEL[3],740);g.shell=False;key(pg.K_RIGHT,True,0.);ticks(45)
    before=g.visual();key(pg.K_RIGHT,False,app.timeline.wall_time);key(pg.K_LEFT,True,app.timeline.wall_time);app.update(0.);ticks(1)
    assert g.vx>0 and g.view=='right' and g.transition is not None
    assert delta(before,g.visual())<500
    ticks(75);assert g.view=='left' and g.vx<0
    checks['arrow_reverse_has_visible_turn']=True

    fresh(LEVEL[3],654.0533333333334);g.vx=300;g.edge('x',True);ticks(10)
    assert g.attack_hits==0
    checks['moving_root_active_sweep_miss']=True
    fresh(view='left');key(pg.K_g,True,0.);ticks(150)
    before=g.visual();time=g.time;key(pg.K_p,True,app.timeline.wall_time);app.update(0.);app.update(.5)
    assert g.run=='Paused' and g.visual()==before and g.time==time
    checks['pause_freezes_visible_pose']=True

    edges=[]
    for view in ('left','right'):
        for x in (36,200):
            fresh(x=x,view=view);key(pg.K_LSHIFT,True,0.);ticks(100)
            markers,legs=a.sample(g.visual())
            assert legs and all(g.support.x0<=g.x+markers['foot_contact_'+leg]['xy'][0]-64<=g.support.x1 for leg in legs),(view,x,legs)
            profile=a.poses['profiles'][g.edge_pose]
            assert min(profile['lift_height_px'].values())>.7,profile
            assert abs(g.x-x)<1e-8
            edges.append({'view':view,'x':x,'support':legs,'lifted':profile['lifted'],'min_lift_px':min(profile['lift_height_px'].values())})
    checks['manual_edge_stance']=edges

    fresh();app.draw();before=pg.image.tobytes(app.screen,'RGBA');g.edge('g',True);app.draw()
    after=pg.image.tobytes(app.screen,'RGBA')
    assert before!=after and not app.buttons and g.work is None
    fresh(x=100.1625);assert 'food' in g.ready_work()
    fresh(LEVEL[1],340.2251);assert 'beacon' in g.ready_work()
    checks['world_feedback_without_hud']=True

    count=0
    for name,clip in a.pose_clips.items():
        for view in clip['supported_views']:
            for i in range(len(clip['samples'])):
                k=(name,view,i);maps=a.maps(k);img=a.render(k,'lit',(0,0),(19,1),power=.82,ambient=.34)
                assert pg.image.tobytes(img,'RGBA')[3::4]==pg.image.tobytes(maps['sprite'],'RGBA')[3::4]
                count+=1
    assert count==930 and a.pose_bundle.testzip() is None
    checks['supplemental_pose_cells']=count

    with ZipFile(ROOT/'lighting_reference.zip') as golden:
        cases=json.loads(golden.read('cases.json'));maximum=0;changed=0
        for i,case in enumerate(cases):
            image=a.render(tuple(case['key']),'lit',(0,0),case['light'],case['roughness'],case['metallic'],case['power'],case['emission'],ambient=case['ambient'])
            errors=[abs(x-y) for x,y in zip(pg.image.tobytes(image,'RGBA'),golden.read(str(i)+'.rgba'))]
            maximum=max(maximum,max(errors));changed+=sum(e>0 for e in errors)
        assert maximum<=1 and changed<=4,(maximum,changed)
    checks['reference_shader_equivalence']={'cases':len(cases),'max_channel_error':maximum,'changed_channels':changed}

    app.scene='viewer';v=app.viewer;v.select(v.names.index('obs_female_contact'));app.viewer.light_mode=2
    for c in v.track.cells:a.surface_fields(c)
    samples=[]
    for i in range(150):
        start=perf_counter();app.update(1/60);app.draw();cost=(perf_counter()-start)*1000
        if i>=30:samples.append(cost)
    ordered=sorted(samples);p95=ordered[math.ceil(.95*len(ordered))-1]
    checks['moving_light_viewer_frame_ms']={'median':statistics.median(samples),'p95':p95,'max':max(samples),'samples':len(samples),'scope':'SDL dummy update+draw, excludes OS presentation and event polling'}
    checks['moving_light_viewer_frame_ms']['p95_within_60hz_budget']=p95<=1000/60
    a.close();pg.quit()
    (ROOT/'gameplay_r2_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    if not quiet:print(json.dumps(checks,ensure_ascii=False,indent=2))
    return checks


if __name__=='__main__':verify()
