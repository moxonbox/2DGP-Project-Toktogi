"""Replay real key events and exercise every shipped material cell on headless SDL."""
import json
import math
import os
from time import perf_counter


def verify():
    os.environ['SDL_VIDEODRIVER']='dummy'
    os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame as pg
    from main import App, ROOT, STEP, MODES, FIELD, PLAY_CLEAR
    from game import BEACON, COLLECT, FOOD, LEVEL, SHELL, PRE_WINDOW, POST_WINDOW

    app=App()
    g=app.game
    a=app.assets
    keys={'right':pg.K_RIGHT,'left':pg.K_LEFT,'space':pg.K_SPACE,'e':pg.K_e,'f':pg.K_f,'g':pg.K_g,
          'x':pg.K_x,'shift':pg.K_LSHIFT,'q':pg.K_q,'p':pg.K_p,'r':pg.K_r}
    checks={}

    def edge(name,down):
        app.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=keys[name],mod=0))

    def tap(name):
        edge(name,True)
        edge(name,False)

    def step(n):
        for _ in range(n):
            app.update(STEP)

    def until(pred, name, timeout=600):
        for _ in range(timeout):
            if pred():
                return
            step(1)
        raise AssertionError((name,g.x,g.y,g.vx,g.vy,g.run,g.clip))

    def stop():
        edge('right',False)
        edge('shift',True)
        step(24)
        edge('shift',False)

    def place(platform,x,view='right'):
        g.reset()
        app.physical_keys.clear()
        g.support=platform
        g.x=x
        g.y=platform.y
        g.view=view

    app.draw()
    assert not app.buttons and tuple(app.screen.get_at((20,20)))[:3]==PLAY_CLEAR
    # Sample the same albedo pixels on each course platform using the gameplay renderer.
    key=('idle','right',0)
    base=pg.image.tobytes(a.maps(key)['base'],'RGBA')
    body=[i for i in range(0,len(base),4) if base[i+3] and max(base[i:i+3])>125]
    luminance=[]
    for platform in LEVEL[:5]:
        place(platform,(platform.x0+platform.x1)//2)
        app.draw()
        origin=(FIELD.x+round(g.x)-64,FIELD.y+round(g.y)-88)
        sprite=app.screen.subsurface((*origin,128,128))
        data=pg.image.tobytes(sprite,'RGBA')
        values=[.2126*data[i]+.7152*data[i+1]+.0722*data[i+2] for i in body]
        assert sum(v>253 for v in values)==0
        luminance.append(round(sum(values)/len(values),1))
    assert min(luminance)>=170 and max(luminance)-min(luminance)<18,luminance
    checks['play_display']={'ui_buttons':0,'body_luma_by_platform':luminance}
    g.reset()
    app.draw()
    pg.image.save(app.screen,ROOT/'play_preview.png')
    edge('right',True)
    until(lambda:g.x>=127,'first takeoff')
    tap('space')
    until(lambda:g.support is LEVEL[1],'platform 2')
    edge('right',False)
    step(24)
    edge('right',True)
    until(lambda:g.x>=339,'beacon work location')
    stop()
    tap('e')
    step(105)
    assert g.beacon and g.launch_count==1
    tap('space')
    until(lambda:g.support is LEVEL[2],'elastic leaf')
    assert g.checkpoint
    edge('shift',True)
    step(13)
    edge('shift',False)
    before=g.time
    tap('space')
    assert g.prep[3] and 0<before-g.offer[1]<POST_WINDOW
    until(lambda:g.support is LEVEL[3],'elastic jump to platform 4')
    assert g.elastic_count==1 and g.launch_count==3
    stop()
    edge('right',True)
    until(lambda:g.x>=690,'attack range')
    stop()
    tap('x')
    step(48)
    assert not g.shell
    edge('right',True)
    until(lambda:g.x>=746,'goal takeoff')
    stop()
    tap('space')
    until(lambda:g.support is LEVEL[4],'goal support')
    edge('shift',True)
    until(lambda:g.run=='Cleared','stable goal')
    assert g.launch_count==4 and g.elastic_count==1
    checks['input_replay']={'cleared':True,'seconds':round(g.time,3),'launches':4,'elastic_launches':1}
    app.draw()
    assert not app.buttons
    pg.image.save(app.screen,ROOT/'goal_preview.png')
    tap('space')
    assert g.run=='Cleared' and g.launch_count==4
    tap('r')
    assert g.run=='Playing' and g.support is LEVEL[2] and g.clip=='respawn' and g.offer is None

    place(LEVEL[0],86)
    edge('space',False)
    assert g.prep is None
    edge('space',True)
    step(20)
    assert g.launch_count==0 and g.support
    app.event(pg.event.Event(pg.WINDOWFOCUSLOST))
    app.event(pg.event.Event(pg.WINDOWFOCUSGAINED))
    edge('space',False)
    assert g.run=='Paused' and g.prep is None
    t=g.time
    step(60)
    assert g.time==t
    tap('p')
    tap('space')
    assert g.prep
    edge('space',True)
    step(22)
    assert g.launch_count==0 and g.prep is None
    app.switch('viewer')
    app.switch('game')
    edge('space',False)
    assert g.prep is None
    checks['input_epochs']='Space UP, cancellation, focus loss, pause and scene switch'

    place(LEVEL[2],490)
    g.support=None
    g.y=LEVEL[2].y-7
    g.vy=190
    tap('space')
    assert g.prep is None
    until(lambda:g.launch_count==1,'pre-contact elastic release',40)
    assert g.elastic_count==1
    place(LEVEL[1],300)
    g.support=None
    g.y=LEVEL[1].y-7
    g.vy=190
    tap('space')
    until(lambda:g.support is LEVEL[1],'normal air release',40)
    step(20)
    assert g.launch_count==0 and g.elastic_at is None
    place(LEVEL[0],146)
    g.recovery=.25
    tap('space')
    until(lambda:g.launch_count==1,'recovery jump',40)
    assert -390<g.vy<-300
    place(LEVEL[0],200)
    edge('right',True)
    until(lambda:g.support is None,'edge fall')
    assert g.clip=='fall_unlaunched' and g.launch_count==0
    checks['motion_rules']='elastic pre/post windows, one launch, reduced recovery, support-loss fall'

    place(LEVEL[0],FOOD[0]-29.84)
    edge('f',True)
    step(55)
    assert g.bites==1 and g.food==3
    g.view='left'
    edge('g',True)
    assert g.work['key']=='g'
    edge('f',False)
    assert g.work['key']=='g'
    step(220)
    assert g.clip=='groom' and g.visual()[0] in ('obs_antenna_clean','obs_antenna_to_furca','obs_furca_clean')
    edge('g',False)
    assert g.work is None and g.bites==1
    place(LEVEL[2],COLLECT[0]+1.09)
    tap('e')
    step(105)
    assert g.collected
    tap('e')
    assert g.work is None
    place(LEVEL[3],SHELL[0]-7)
    step(1)
    assert g.support is None and g.vy<0 and g.clip=='hit_ground'
    place(LEVEL[0],290)
    g.support=None
    g.y=571
    g.vy=330
    until(lambda:g.run=='Failed','fall boundary',30)
    tap('r')
    assert g.run=='Playing' and g.support is LEVEL[0] and g.launch_count==0
    checks['work_and_progress']='beacon, bite, held input owner, self-groom, collection, hit, fail and respawn'

    app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_F2,mod=0))
    assert app.scene=='viewer'
    v=app.viewer
    assert len(v.names)==82+len(a.sequences)+len(v.game_previews) and len(a.tracks)==len({(key[0],key[1]) for t in a.tracks.values() for key in t.cells})
    for i,name in enumerate(v.names):
        v.select(i)
        for direction in range(len(v.views)):
            v.view=direction
            track=v.track
            assert track.cells[track.index(track.start(len(track.cells)-1))]==track.cells[-1],name
    v.search='더듬이 손질'
    v.filter()
    assert 'obs_antenna_clean' in v.filtered
    v.search=''
    v.filter()
    v.select(v.names.index('obs_antenna_clean'))
    v.time=1.01
    app.draw()
    assert app.buttons
    pg.image.save(app.screen,ROOT/'motion_preview.png')
    v.select(v.names.index('walk'))
    app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_v,mod=0))
    assert v.views[v.view]=='right'
    app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RIGHT,mod=0))
    assert not v.playing and v.track.index(v.time)==1
    for i,_mode in enumerate(MODES):
        app.viewer.mode=i
        app.draw()
    app.viewer.mode=0
    assert len(a.groom.cells)==47 and abs(a.groom.duration-3.96)<1e-8
    assert sum(len(t.cells) for n,t in a.sequences.items() if not n.startswith('runtime_'))==804
    checks['viewer']={'clips':len(a.clips),'sequences':len(a.sequences),'clip_views':len(a.tracks),
                      'base_sequence_frames':804,'runtime_profiles':len(a.pose_tracks),'groom_hold_ms':3960}

    origin=(0,0)
    t0=perf_counter()
    count=0
    for track in a.tracks.values():
        for key in track.cells:
            maps=a.maps(key)
            actual=a.render(key,'lit',origin,(37,32))
            assert actual.get_size()==(128,128) and set(maps)=={'sprite','base','normal','rm','emissive'}
            sa=pg.image.tobytes(maps['sprite'],'RGBA')[3::4]
            assert pg.image.tobytes(actual,'RGBA')[3::4]==sa,key
            count+=1
    assert count==1444 and a.bundle.testzip() is None
    checks['all_material_cells']={'rendered':count,'elapsed_seconds':round(perf_counter()-t0,3),'atlas_cache_cells':36}

    key=('idle','left',0)
    def rgb(light,roughness=None,metallic=None,emission=True):
        return pg.image.tobytes(a.render(key,'lit',origin,light,roughness,metallic,1.,emission),'RGB')
    first=rgb((16,30))
    variants={'direction':rgb((115,25)),'roughness':rgb((16,30),.22),'metallic':rgb((16,30),None,1.),
              'emission':rgb((16,30),emission=False)}
    response={name:sum(first[i:i+3]!=other[i:i+3] for i in range(0,len(first),3)) for name,other in variants.items()}
    assert all(value>0 for value in response.values())
    checks['material_response_changed_pixels']=response

    app.switch('game')
    g.reset()
    samples=[]
    for _ in range(180):
        start=perf_counter()
        app.update(1/60)
        app.draw()
        samples.append((perf_counter()-start)*1000)
    samples.sort()
    checks['dummy_sdl_frame_ms']={name:round(samples[math.ceil(q*len(samples))-1],3) for name,q in (('p50',.5),('p95',.95),('p99',.99))}
    checks['source_bundle_signature']=a.manifest['bundle_contract_signature']
    from verify_requirements import verify as verify_requirements
    checks['requirement_trace']=verify_requirements(app)
    a.close()
    pg.quit()
    from verify_regressions import verify as verify_review
    checks['review_regressions']=verify_review(quiet=True)
    from verify_gameplay_r2 import verify as verify_r2
    checks['gameplay_r2']=verify_r2(quiet=True)
    from verify_gameplay_r3 import verify as verify_r3
    checks['gameplay_r3']=verify_r3()
    from verify_gameplay_r4 import verify as verify_r4
    checks['gameplay_r4']=verify_r4()
    from verify_framework import verify as verify_framework
    checks['framework_r1']=verify_framework()
    (ROOT/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False,indent=2))
