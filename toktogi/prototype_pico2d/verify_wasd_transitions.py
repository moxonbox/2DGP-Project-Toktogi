"""Focused rapid-key pose continuity; authored cells only, no native window."""
import json
from math import atan2,degrees
from pathlib import Path
from app import GAME_KEYS
from game import Game
from materials import Assets
from physics import STEP
from stage_world import habitat_world

ROOT=Path(__file__).resolve().parent


def verify():
    assets=Assets(ROOT/'toktogi_assets.zip')
    def reset():
        g=Game(assets,world=habitat_world(),walk_speed=12.,directional_yaw=True)
        g.x=190.
        return g
    def hold(g,wanted):
        wanted=set(wanted)
        for key in 'wasd':
            if GAME_KEYS[key] in g.held and key not in wanted:g.edge(GAME_KEYS[key],False)
        for key in 'wasd':
            if key in wanted and GAME_KEYS[key] not in g.held:g.edge(GAME_KEYS[key],True)
    def ticks(g,count):
        for _ in range(count):g.step()
    try:
        g=reset();previous=None;jumps=[];rendered=[]
        schedule=('a','aw','as','d','dw','ds','a','w','d','s','a','d')*2
        for wanted in schedule:
            hold(g,wanted)
            for _ in range(12):
                angle=g.yaw_angle;g.step()
                assert abs(g.yaw_angle-angle)<=360/1.55*STEP+1e-6
                markers,_=assets.sample(g.visual())
                front,back=markers['mouth_marker']['world'],markers['furca_marker']['world']
                heading=degrees(atan2(front[1]-back[1],front[0]-back[0]))
                if previous is not None:jumps.append(abs((heading-previous+180)%360-180))
                previous=heading;rendered.append(heading)
        assert max(jumps)<15,max(jumps)
        sampled=rendered[::2]
        frame_jumps=[abs((b-a+180)%360-180) for a,b in zip(sampled,sampled[1:])]
        assert max(frame_jumps)<20,max(frame_jumps)
        g=reset();hold(g,'ds');ticks(g,24)
        assert g.aim==1 and g.aim_display==1 and g.visual()[0]=='aim_up'
        hold(g,'dw');g.step()
        assert g.aim==-1 and 0<g.aim_display<1 and g.visual()[0]=='aim_up'
        ticks(g,40);assert g.aim_display==-1 and g.visual()[0]=='aim_down'
        angle=g.yaw_angle;hold(g,'aw');g.step()
        assert g.yaw_angle==angle and -1<g.aim_display<0
        ticks(g,24);assert g.aim_display==0 and g.yaw_angle!=angle
        g=reset();hold(g,'ds');ticks(g,24)
        pose,display=g.visual(),g.aim_display
        g.pause();ticks(g,120);assert g.visual()==pose and g.aim_display==display
        g.pause();g.step();assert 0<g.aim_display<display
        ticks(g,24);assert g.aim_display==0
        g=reset();hold(g,'ds');ticks(g,24)
        g.edge('x',True);assert g.work and g.work['key']=='x' and g.visual()[0] not in ('aim_up','aim_down','ground_spin_left')
        g.step();assert g.aim_display==0
        g=reset();hold(g,'ds');ticks(g,24)
        g.edge('space',True);g.edge('space',False);assert g.prep and g.prep[-2]==1
        ticks(g,36);assert g.launch_count==1 and not g.support and g.aim_display==0
        return {'passed':True,'rapid_key_changes':len(schedule),'simulation_samples':len(rendered),
                'max_visual_heading_step_degrees':round(max(jumps),3),
                'max_60hz_visual_heading_step_degrees':round(max(frame_jumps),3),
                'aim_values_immediate':True,'aim_switch_through_neutral':True,
                'rotation_waits_for_neutral':True,'pause_pose_preserved':True,
                'jump_and_attack_priority':True,'computer_use':False,
                'scope':'Source marker directions and authored pose continuity; physical keyboard/display not certified.'}
    finally:assets.close()


if __name__=='__main__':
    report=verify()
    (ROOT/'wasd_transitions_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
