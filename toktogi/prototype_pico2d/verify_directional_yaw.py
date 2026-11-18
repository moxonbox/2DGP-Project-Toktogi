"""Focused WASD yaw, release, action and original Z-spin checks; no window."""
import json
from pathlib import Path
from app import GAME_KEYS,App
from legacy_test_app import App as LegacyApp
from materials import Assets
from game import Game
from stage_world import habitat_world
from physics import STEP

ROOT=Path(__file__).resolve().parent


def verify():
    assets=Assets(ROOT/'toktogi_assets.zip')
    def reset():
        g=Game(assets,world=habitat_world(),walk_speed=72.,directional_yaw=True)
        g.x=190.
        return g
    def keys(g,names,down):
        for key in names:g.edge(GAME_KEYS[key],down)
    def ticks(g,count):
        for _ in range(count):g.step()
    try:
        assert App.directional_yaw and not LegacyApp.directional_yaw
        headings={}
        for key,target in (('w',270),('s',90)):
            g=reset();keys(g,key,True);ticks(g,60);keys(g,key,False)
            assert abs((g.yaw_angle-target+180)%360-180)<1e-7
            headings[key]=round(g.yaw_angle%360,3)
        camera=assets.manifest['coordinate_contract']['camera_location']
        def facing(angle):
            markers,_=assets.sample(g.motion.yaw_cell(angle))
            mouth,tail=markers['mouth_marker']['world'],markers['furca_marker']['world']
            return sum((mouth[i]-tail[i])*camera[i] for i in (0,1))
        initial=facing(0.)
        capped={}
        for key,view,start,target in (('a','right',0.,-180.),('d','left',180.,360.)):
            g=reset();g.walk_speed=12.;g.view=view;g.yaw_angle=start;keys(g,key,True)
            ticks(g,450)
            assert g.yaw_angle==target and not g.yaw_turning and g.support
            keys(g,key,False);keys(g,key,True);ticks(g,30)
            assert g.yaw_angle==target
            capped[key]=abs(target-start)
            g.edge('shift',True);ticks(g,130)
            assert abs(g.yaw_angle-target)>180 and g.vx==0
            before=g.yaw_angle;g.edge('shift',False);ticks(g,130)
            expected=180 if key=='a' else 0
            assert abs((g.yaw_angle-expected+180)%360-180)<1e-7
            assert abs(g.yaw_angle-before)<=180 and not g.yaw_turning
        facing_scores={};rotations={};detents={}
        for key,sign in (('a',-1),('d',1)):
            g=reset();g.walk_speed=24.;g.edge('shift',True);keys(g,key,True);trace=[]
            step=360/1.55*STEP
            for i in range(450):
                g.step();trace.append(g.yaw_angle)
                assert g.support and g.transition is None and g.yaw_turning
                previous=trace[-2] if i else 0.
                delta=sign*(g.yaw_angle-previous)
                assert -1e-7<=delta<=step+1e-7
                if delta<1e-7:assert abs(g.yaw_angle/180-round(g.yaw_angle/180))<1e-7
                assert g.visual()[0] in ('idle','ground_spin_left')
                if i==12:facing_scores[key]=facing(g.yaw_angle)
            assert abs(trace[-1])>720
            for boundary in (180,360,540,720):
                held=[i for i,angle in enumerate(trace) if abs(angle-sign*boundary)<1e-7]
                assert len(held)==12 and held==list(range(held[0],held[-1]+1)),(key,boundary,held)
            detents[key]=len(held)*STEP*1000
            keys(g,key,False);saved=g.yaw_angle;ticks(g,60)
            assert g.yaw_angle==saved
            rotations[key]=round(trace[-1],3)
        assert facing_scores['a']<initial<facing_scores['d']
        g=reset();g.walk_speed=24.;g.edge('shift',True);keys(g,'d',True)
        for _ in range(100):
            g.step()
            if g.yaw_angle==180:break
        assert g.yaw_angle==180
        keys(g,'d',False);ticks(g,3);assert g.yaw_angle==180
        keys(g,'a',True);g.step();assert g.yaw_angle<180
        for key in ('a','d'):
            traces=[]
            for aim in ('','w','s','ws'):
                g=reset();g.walk_speed=24.;keys(g,key+aim,True)
                sequence=[]
                for _ in range(110):g.step();sequence.append(g.yaw_angle)
                traces.append(sequence)
                expected=-1 if aim=='w' else 1 if aim=='s' else 0
                assert g.aim==expected
                if expected:
                    assert g.visual()[0]==('aim_up' if expected>0 else 'aim_down')
                    g.edge('space',True);g.edge('space',False)
                    assert g.prep and g.prep[-2]==expected
            assert all(sequence==traces[0] for sequence in traces)
        g=reset();keys(g,'w',True);ticks(g,13);keys(g,'w',False)
        angle,pose=g.yaw_angle,g.visual()
        assert -90<angle<0 and pose[0].startswith('ground_spin_')
        ticks(g,120);assert g.yaw_angle==angle and g.visual()==pose
        keys(g,'wsad',True);ticks(g,10);keys(g,'wsad',False)
        assert g.yaw_angle==angle
        g.pause();ticks(g,120);assert g.yaw_angle==angle and g.visual()==pose
        g.pause();ticks(g,1);assert g.visual()==pose
        keys(g,'s',True);g.step();keys(g,'s',False);assert g.yaw_angle>angle
        g=reset();keys(g,'w',True);ticks(g,13);keys(g,'w',False)
        keys(g,'x',True);keys(g,'x',False)
        assert g.work and g.visual()[0]=='attack_demo'
        ticks(g,130);assert not g.work and g.yaw_pose is None
        g=reset();keys(g,'w',True);ticks(g,13);keys(g,'w',False)
        g.edge('space',True);g.edge('space',False);ticks(g,36)
        assert g.launch_count==1 and not g.support and g.yaw_pose is None
        g=reset();keys(g,'z',True);keys(g,'z',False)
        assert g.full_turn and g.transition and len(g.transition[0].cells)==62
        track=g.transition[0];ticks(g,190)
        assert not g.transition and g.view=='right'
        g=reset();g.x=g.support.x0+4;keys(g,'w',True);ticks(g,5)
        assert g.yaw_angle==0 and g.yaw_pose is None
        legacy=Game(assets);legacy.edge('left',True);legacy.step()
        assert legacy.transition and legacy.transition[0].cells[0][0].startswith('turn_')
        return {'passed':True,'headings_degrees':headings,'release_hold_degrees':round(angle,3),
                'plain_AD_max_turn_degrees':capped,'Ctrl_AD_rotation_degrees':rotations,'Ctrl_mode_switch':True,'WS_inverted':True,'half_turn_detent_ms':detents,'reverse_cancels_detent':True,'screen_facing_scores':facing_scores,'pause_and_opposites_hold':True,
                'reverse_input':True,'aim_does_not_redirect_rotation':True,'jump_and_attack':True,'ledge_support_gate':True,
                'z_spin_cells':len(track.cells),'z_spin_seconds':round(track.duration,3),
                'legacy_fixture_preserved':True,'computer_use':False}
    finally:assets.close()


if __name__=='__main__':
    report=verify()
    (ROOT/'directional_yaw_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
