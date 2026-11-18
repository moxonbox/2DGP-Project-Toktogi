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
        for names,target in (('d',0),('dw',45),('w',90),('wa',135),('a',180),('as',225),('s',270),('sd',315)):
            g=reset();keys(g,names,True)
            shown=[]
            for _ in range(100):
                g.step();shown.append(g.visual()[0])
                if abs((g.yaw_angle-target+180)%360-180)<1e-7:break
            keys(g,names,False)
            assert abs((g.yaw_angle-target+180)%360-180)<1e-7,(names,g.yaw_angle)
            assert not any(name.startswith('turn_') for name in shown)
            assert g.transition is None and g.support
            headings[names]=round(g.yaw_angle%360,3)
        g=reset();keys(g,'dw',True);ticks(g,40)
        gait=[]
        for _ in range(36):g.step();gait.append(g.visual())
        assert len(set(gait))>1 and all(cell[0]=='walk' and cell[1]=='yaw_090' for cell in gait)
        g=reset();keys(g,'w',True);ticks(g,13);keys(g,'w',False)
        angle,pose=g.yaw_angle,g.visual()
        assert 0<angle<90 and pose[0].startswith('ground_spin_')
        ticks(g,120);assert g.yaw_angle==angle and g.visual()==pose
        keys(g,'wsad',True);ticks(g,10);keys(g,'wsad',False)
        assert g.yaw_angle==angle
        g.pause();ticks(g,120);assert g.yaw_angle==angle and g.visual()==pose
        g.pause();ticks(g,1);assert g.visual()==pose
        keys(g,'s',True);g.step();keys(g,'s',False);assert g.yaw_angle<angle
        g=reset();trace=[]
        for key,target in (('w',90),('a',180),('s',270),('d',360)):
            keys(g,key,True)
            for _ in range(90):
                g.step();trace.append(g.yaw_angle)
                if abs(g.yaw_angle-target)<1e-7:break
            keys(g,key,False)
            assert abs(g.yaw_angle-target)<1e-7,(key,g.yaw_angle)
        assert all(b>=a for a,b in zip(trace,trace[1:])) and trace[-1]==360.
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
                'full_rotation_degrees':trace[-1],'pause_and_opposites_hold':True,
                'reverse_input':True,'diagonal_walk_animated':True,'jump_and_attack':True,'ledge_support_gate':True,
                'z_spin_cells':len(track.cells),'z_spin_seconds':round(track.duration,3),
                'legacy_fixture_preserved':True,'computer_use':False}
    finally:assets.close()


if __name__=='__main__':
    report=verify()
    (ROOT/'directional_yaw_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
