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
        for key,target in (('w',90),('s',270)):
            g=reset();keys(g,key,True);ticks(g,60);keys(g,key,False)
            assert abs((g.yaw_angle-target+180)%360-180)<1e-7
            headings[key]=round(g.yaw_angle%360,3)
        camera=assets.manifest['coordinate_contract']['camera_location']
        def facing(angle):
            markers,_=assets.sample(g.motion.yaw_cell(angle))
            mouth,tail=markers['mouth_marker']['world'],markers['furca_marker']['world']
            return sum((mouth[i]-tail[i])*camera[i] for i in (0,1))
        initial=facing(0.)
        facing_scores={};rotations={}
        for key,sign in (('a',-1),('d',1)):
            g=reset();g.walk_speed=24.;keys(g,key,True);trace=[]
            step=360/1.55*STEP
            for i in range(400):
                g.step();trace.append(g.yaw_angle)
                assert g.support and g.transition is None and g.yaw_turning
                assert abs(g.yaw_angle-sign*(i+1)*step)<1e-6
                assert g.visual()[0] in ('idle','ground_spin_left')
                if i==12:facing_scores[key]=facing(g.yaw_angle)
            assert abs(trace[-1])>720
            keys(g,key,False);saved=g.yaw_angle;ticks(g,60)
            assert g.yaw_angle==saved
            rotations[key]=round(trace[-1],3)
        assert facing_scores['a']<initial<facing_scores['d']
        for key in ('a','d'):
            traces=[]
            for aim in ('','w','s','ws'):
                g=reset();g.walk_speed=24.;keys(g,key+aim,True)
                sequence=[]
                for _ in range(40):g.step();sequence.append(g.yaw_angle)
                traces.append(sequence)
                expected=1 if aim=='w' else -1 if aim=='s' else 0
                assert g.aim==expected
                if expected:
                    assert g.visual()[0]==('aim_up' if expected>0 else 'aim_down')
                    g.edge('space',True);g.edge('space',False)
                    assert g.prep and g.prep[-2]==expected
            assert all(sequence==traces[0] for sequence in traces)
        g=reset();keys(g,'w',True);ticks(g,13);keys(g,'w',False)
        angle,pose=g.yaw_angle,g.visual()
        assert 0<angle<90 and pose[0].startswith('ground_spin_')
        ticks(g,120);assert g.yaw_angle==angle and g.visual()==pose
        keys(g,'wsad',True);ticks(g,10);keys(g,'wsad',False)
        assert g.yaw_angle==angle
        g.pause();ticks(g,120);assert g.yaw_angle==angle and g.visual()==pose
        g.pause();ticks(g,1);assert g.visual()==pose
        keys(g,'s',True);g.step();keys(g,'s',False);assert g.yaw_angle<angle
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
                'continuous_rotation_degrees':rotations,'screen_facing_scores':facing_scores,'pause_and_opposites_hold':True,
                'reverse_input':True,'aim_does_not_redirect_rotation':True,'jump_and_attack':True,'ledge_support_gate':True,
                'z_spin_cells':len(track.cells),'z_spin_seconds':round(track.duration,3),
                'legacy_fixture_preserved':True,'computer_use':False}
    finally:assets.close()


if __name__=='__main__':
    report=verify()
    (ROOT/'directional_yaw_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
