"""Regression proof through the normal App input timeline."""
import os
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import json
from main import App,ROOT,pg
from game import LEVEL,STEP

def verify():
    app=App();g=app.game;a=app.assets;checks={}
    def fresh(platform=0,x=155,view='right'):
        g.reset();g.support=LEVEL[platform];g.x=x;g.y=g.support.y;g.view=view
        app.timeline.pending.clear();app.physical_keys.clear();app.control_keys.clear()
        app.timeline.accumulator=app.timeline.wall_time=app.timeline.tick_wall=0.;app.focused=True;app.scene='game'
    def key(k,down,at=None):
        app.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=k,mod=0),at=app.timeline.wall_time if at is None else at)
    def ticks(n):
        for _ in range(n):app.update(STEP)
    fresh(3,690,'left');key(pg.K_g,True,.05);ticks(375)
    key(pg.K_RIGHT,True);key(pg.K_g,False);app.update(0.);ticks(32)
    before=g.visual();key(pg.K_x,True);app.update(0.)
    assert g.visual()==before and g.pending_work=='x'
    ticks(45);assert g.attack_hits==1 and not g.shell and g.view=='right'
    checks['groom_turn_attack_direction']=True

    fresh(1,300);g.support=None;g.y=403.8;g.vy=400;g.action='Jump';g.clip='air_fall'
    key(pg.K_LEFT,True);shown=[]
    for _ in range(20):ticks(1);shown.append(g.visual()[0])
    assert shown.count('land_hard')>=18,shown
    checks['opposite_landing_compression_ticks']=shown.count('land_hard')
    fresh(1,300);g.support=None;g.y=403.8;g.vy=400;g.clip='air_fall'
    ticks(4);at=app.timeline.wall_time+STEP
    key(pg.K_LEFT,True,at);key(pg.K_SPACE,True,at);key(pg.K_SPACE,False,at);ticks(1)
    track=g.transition[0];assert track.cells[-1]==('jump_pre','left',1)
    assert g.prep[0]-g.time==track.duration
    ticks(20);assert g.launch_count==1 and g.visual()[1]=='left' and g.vx<0
    checks['opposite_rejump_shared_heading']=True
    fresh();key(pg.K_LEFT,True,.05);key(pg.K_LEFT,False,.15);key(pg.K_RIGHT,True,.15)
    ticks(45);assert g.view=='right' and not g.transition
    checks['reverse_turn_returns_early']=True
    fresh()
    for at,k,down in ((.05,pg.K_LEFT,True),(.15,pg.K_LEFT,False),(.15,pg.K_RIGHT,True),(.18,pg.K_RIGHT,False),(.18,pg.K_LEFT,True),(.22,pg.K_LEFT,False),(.22,pg.K_RIGHT,True)):
        key(k,down,at)
    ticks(90);assert g.view=='right' and g.transition is None
    checks['repeated_turn_reversals']=True

    edges=[]
    for view in ('left','right'):
        for x in (36,200):
            for aim in (pg.K_UP,pg.K_DOWN):
                fresh(x=x,view=view);key(pg.K_LSHIFT,True);ticks(40);key(aim,True);ticks(35)
                markers,legs=a.sample(g.visual())
                assert legs and all(g.support.x0<=g.x+markers['foot_contact_'+leg]['xy'][0]-64<=g.support.x1 for leg in legs)
                previous=g.visual();key(pg.K_x,True);app.update(0.)
                assert not g.work and g.visual()==previous and g.reject_until>g.time
                edges.append((view,x,aim,legs))
    checks['edge_aim_and_attack_admission']=edges
    fresh(4,835);g.beacon=True;key(pg.K_RIGHT,True);ticks(70)
    assert g.run=='Playing'
    key(pg.K_RIGHT,False);key(pg.K_LSHIFT,True);ticks(30)
    assert g.run=='Cleared' and abs(g.vx)<1
    checks['goal_requires_stop']=True
    fresh(x=100.1625);key(pg.K_x,True,.05);ticks(10)
    assert not g.ready_work();key(pg.K_f,True);app.update(0.)
    assert g.work['key']=='x' and g.reject_until>g.time
    checks['work_hint_matches_admission']=True
    fresh();key(pg.K_p,True,.05);key(pg.K_p,True,.05);ticks(12)
    assert g.run=='Paused'
    key(pg.K_p,False);key(pg.K_p,True);app.update(0.)
    assert g.run=='Playing'
    fresh();app.event(pg.event.Event(pg.WINDOWFOCUSLOST),at=.05);key(pg.K_p,True,.06);ticks(60)
    assert not app.focused and g.run=='Paused'
    checks['progress_key_edge_and_focus']=True
    fresh(view='left');key(pg.K_g,True,.05);ticks(150);cell=g.visual()
    key(pg.K_p,True);app.update(0.);ticks(30);assert g.visual()==cell
    key(pg.K_p,False);key(pg.K_p,True);app.update(0.);assert g.visual()==cell
    ticks(42);assert not g.work and g.visual()[0]=='idle'
    checks['pause_resumes_effect_free_pose_return']=True
    count=0;max_error=0.
    for name,clip in a.pose_clips.items():
        if name.startswith(('flight_roll_','ground_spin_')):
            continue
        for sample in clip['samples']:
            assert sample['support']
            marks=next(iter(sample['views'].values()))['markers']
            max_error=max(max_error,max(abs(marks['foot_contact_'+leg]['world'][2]) for leg in sample['support'])/a.manifest['coordinate_contract']['world_units_per_pixel'])
            count+=1
    assert count==780 and max_error<.3
    checks['support_labels']={'cells':count,'max_normal_error_px':max_error}
    a.close();pg.quit()
    (ROOT/'gameplay_r3_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    return checks

if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
