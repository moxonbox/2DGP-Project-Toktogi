"""Counterexamples from the gameplay-r3 review, through the App event timeline."""
import os
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import json
from collections import Counter
from main import App,ROOT,pg
from game import LEVEL,STEP,FOOD

def verify():
    app=App();g=app.game;a=app.assets;checks={}
    def fresh(i=0,x=150,view='right'):
        g.reset();g.support=LEVEL[i];g.x=x;g.y=g.support.y;g.view=view
        app.timeline.pending.clear();app.physical_keys.clear();app.control_keys.clear()
        app.timeline.accumulator=app.timeline.wall_time=app.timeline.tick_wall=0.;app.focused=True;app.scene='game'
    def key(k,down,**args):
        app.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=k,mod=0,**args),at=app.timeline.wall_time)
        app.update(0.)
    def tap(k):
        key(k,True);key(k,False)
    def ticks(n):
        for _ in range(n):app.update(STEP)
    velocities=[]
    for hold in (0,3,6,12):
        fresh();key(pg.K_RIGHT,True);ticks(20)
        key(pg.K_SPACE,True);ticks(hold);key(pg.K_SPACE,False)
        ticks(12);assert g.launch_count==1
        velocities.append(g.vx)
    assert min(velocities)==max(velocities)==172,velocities
    fresh();key(pg.K_RIGHT,True);ticks(20);key(pg.K_SPACE,True)
    key(pg.K_LSHIFT,True);ticks(12);key(pg.K_SPACE,False);ticks(12)
    assert g.vx==148
    checks['space_hold_preserves_walk_shift_brakes']=velocities

    bonuses=[]
    for side in (pg.K_LEFT,pg.K_RIGHT):
        for aim in (pg.K_UP,pg.K_DOWN):
            pair=[]
            for when in ('before','after'):
                fresh(2,480);g.support=None;g.y=LEVEL[2].y-5;g.vy=180;g.action='Jump';g.clip='air_fall'
                key(side,True);key(aim,True)
                if when=='after':ticks(4)
                tap(pg.K_SPACE)
                for _ in range(45):
                    ticks(1)
                    if g.launch_count:break
                assert g.elastic_count==1
                pair.append((g.view,g.aim,g.vx,g.vy))
            assert pair[0]==pair[1],pair
            bonuses.append(pair[0])
    checks['elastic_pre_post_same_direction_aim']=bonuses

    for command in (pg.K_x,pg.K_SPACE):
        fresh(3,690,'left');tap(pg.K_q);ticks(18)
        previous=g.visual();tap(command)
        assert g.visual()==previous and (g.pending_jump if command==pg.K_SPACE else g.pending_work=='x')
        ticks(65)
        assert g.view=='right'
        assert g.attack_hits==1 if command==pg.K_x else g.launch_count==1 and g.vx>0
    checks['q_attack_and_jump_use_destination']=True
    fresh(3,690,'left');tap(pg.K_q);ticks(18);tap(pg.K_SPACE);key(pg.K_SPACE,True);ticks(80)
    assert not g.launch_count and not g.pending_jump
    checks['pending_jump_can_be_cancelled']=True

    fresh(x=FOOD[0]-29.8375);key(pg.K_f,True);ticks(36);key(pg.K_f,False)
    assert g.action=='Idle' and not g.work
    x=g.x;key(pg.K_RIGHT,True);ticks(2);assert g.x>x and g.action=='Walk'
    ticks(35);assert not g.transition
    checks['feed_release_immediate_move']=True
    fresh();key(pg.K_LEFT,True);key(pg.K_RIGHT,True);ticks(35)
    assert g.action=='Walk' and g.vx==0
    key(pg.K_LEFT,False);ticks(5);assert g.vx>0
    checks['opposed_keys_keep_walk']=True

    launches=[]
    for x in (150,180,198,200):
        fresh(x=x);tap(pg.K_SPACE);origin=g.y;lowest=origin
        for _ in range(200):
            ticks(1);lowest=min(lowest,g.y)
            if g.launch_count and g.support:break
        assert origin-lowest>100 and g.support is LEVEL[1],(x,origin-lowest,g.support)
        launches.append((x,round(origin-lowest,3)))
    fresh(1,330);g.support=None;g.y=403.8;g.vy=400;g.action='Jump';g.clip='air_fall'
    ticks(100);assert g.action=='Jump' and g.clip=='recovery_start'
    checks['first_ledge_headroom_and_jump_end']=launches
    fresh();tap(pg.K_SPACE);ticks(25);app.event(pg.event.Event(pg.WINDOWFOCUSLOST),at=app.timeline.wall_time);app.update(0.)
    assert g.run=='Paused' and g.action=='Idle' and not g.held
    checks['focus_closes_air_action']=True
    fresh();key(pg.K_x,True);ticks(2);tap(pg.K_p);tap(pg.K_p)
    key(pg.K_x,True,repeat=True);assert not g.work
    checks['repeat_after_pause_does_not_attack']=True

    frames=[]
    fresh(x=150);tap(pg.K_SPACE)
    for _ in range(125):
        ticks(1)
        frames.append(g.visual())
    assert any(c[0]=='flight_roll_right' for c in frames)
    low={}
    for hz in (10,15,30,60):
        period=120//hz
        counts={n:[] for n in ('release','apex','rotation')}
        for offset in range(period):
            shown=frames[offset::period]
            counts['release'].append(sum(c[0]=='jump_release' and c[2]==2 for c in shown))
            counts['apex'].append(sum(c[0]=='air_apex' and c[2]==1 for c in shown))
            counts['rotation'].append(sum(c[0]=='flight_roll_right' for c in shown))
        assert all(min(v)>0 for v in counts.values()),(hz,counts)
        low[hz]={k:min(v) for k,v in counts.items()}
    checks['core_poses_every_display_phase']=low
    for view in ('left','right'):
        for cell in a.pose_tracks['flight_roll_'+view].cells:
            a.render(cell,'lit',(0,0),(19,1),ambient=.34)
            assert not a.sample(cell)[1]
    checks['flight_cells_have_no_ground_support']=True
    a.close();pg.quit()
    (ROOT/'gameplay_r4_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
    return checks

if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
