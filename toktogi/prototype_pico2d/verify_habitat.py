"""Focused habitat checks: physical gaps, action contacts, restart, and material rendering."""
from pathlib import Path
import argparse
import json
from statistics import median
from time import perf_counter
from unittest.mock import patch
from PIL import Image, ImageChops
from app import App
from game import Game
from input_clock import Event
from stage_world import habitat_world, ZONES
from pond import Pond
from physics import STEP
from lighting import fields, shade
from sprite_renderer import SRGB


def verify(output):
    app=App(profile='habitat')
    try:
        # Each adjacent gap is crossed by the original physics and Space action.
        gaps=[]
        for i in range(9):
            g=Game(app.assets,world=habitat_world())
            source,target=g.course.platforms[i:i+2]
            # Isolate jump geometry; contextual combat is checked below.
            g.world.set_value('shell',False)
            g.support=source;g.x=source.x1-85;g.y=source.y
            g.world.level_id=g.world.platform_ids[id(source)][1]
            g.edge('right',True)
            for _ in range(240):
                g.step()
                if g.x>=source.x1-32:break
            g.edge('space',True);g.edge('space',False)
            for _ in range(240):
                g.step()
                if g.support is target or g.run!='Playing':break
            assert g.support is target,(i,g.x,g.y,g.run)
            assert g.launch_count==1
            gaps.append(i)
        assert app.game.pond.water_y==400.
        for kind in ('peek','jump'):
            for dodge in (False,True):
                trial=Game(app.assets,world=habitat_world());surface=trial.course.platforms[3]
                trial.x=1140;trial.y=surface.y;trial.support=surface
                trial.pond=Pond(trial.world,active_span=(1030,2110),water_y=400.)
                trial.pond.cycle=int(kind=='jump')
                for _ in range(430):
                    trial.step()
                    if trial.pond.phase=='warn':break
                assert trial.pond.phase=='warn'
                if dodge:trial.edge('space',True);trial.edge('space',False)
                for _ in range(155):trial.step()
                assert trial.pond.hits==(0 if dodge else 1),(kind,dodge,trial.pond.hits)
        # Use actual context E and authored contact markers for every interaction.
        g=app.game
        g.x=285;g.view='left'
        assert app.command('e')=='g'
        app.event(Event('key_down',key='e'))
        for _ in range(30):app.update(STEP)
        assert g.work and g.work['stage']=='groom'
        app.event(Event('key_up',key='e'))
        g.reset();g.x=285
        app.event(Event('key_down',key='z'));app.event(Event('key_up',key='z'))
        assert g.full_turn
        g.reset()
        interactions=[]
        for e in g.world.entities:
            if e.kind=='shell':continue
            support=next(p for p in g.course.platforms if p.x0<=e.point[0]<=p.x1 and p.y==e.point[1])
            found=False
            for facing in ('right','left'):
                for x in range(round(e.point[0]-48),round(e.point[0]+49)):
                    g.support=support;g.x=x;g.y=support.y;g.view=facing;g.vx=g.vy=0
                    _,key,_=g.work_candidate('f' if e.kind=='food' else 'e')
                    if key==e.key:found=True;break
                if found:break
            assert found,('Unreachable action',e.key)
            g.pond.next_attack=g.time+100
            old=g.world.states[e.key]
            app.event(Event('key_down',key='e'))
            for _ in range(180):app.update(STEP)
            app.event(Event('key_up',key='e'))
            for _ in range(180):app.update(STEP)
            assert g.world.states[e.key]!=old,(e.key,g.notice,g.work)
            interactions.append(e.kind)
        assert g.world.goal_ready()
        assert g.checkpoint and g.world.checkpoint_id=='pond_rest'
        enemy=g.world.entity('shell');p=g.course.platforms[7]
        g.support=p;g.x=enemy.point[0]-29;g.y=p.y;g.vx=g.vy=0;g.view='right'
        g.pond.next_attack=g.time+100
        app.event(Event('key_down',key='e'));app.event(Event('key_up',key='e'))
        for _ in range(180):app.update(STEP)
        assert not g.world.states[enemy.key] and g.attack_hits==1
        assert ImageChops.difference(app.play_view.art.platform_frames[1][0][0],
                                    app.play_view.art.platform_frames[1][-1][0]).convert('RGB').getbbox()
        goal=g.course.platforms[-1];g.support=goal;g.x=2950;g.y=goal.y;g.vx=g.vy=0
        g.world.level_id='reeds'
        for _ in range(36):app.update(STEP)
        assert g.run=='Cleared'
        checkpoint=g.world.checkpoints[-1]
        assert g.world.landed(checkpoint.platform)
        g.reset(True);assert g.world.level_id=='pond' and g.x==checkpoint.point[0]
        assert all(g.world.states[k] for k in checkpoint.required_beacons)
        g.pond.step(g,STEP)
        g.x=200
        for _ in range(1200):g.pond.step(g,STEP)
        assert g.pond.phase=='idle' and g.pond.hits==0
        # Landscape drawing must not mutate game state or read files mid-frame.
        output.mkdir(parents=True,exist_ok=True)
        for i,zone in zip((0,4,8),ZONES):
            p=g.course.platforms[i];g.x=(p.x0+p.x1)/2;g.y=p.y;g.support=p;g.world.level_id=zone[0]
            app.play_view.camera.epoch=None;app.play_view.step(g,0)
            before=(g.x,g.y,g.time,dict(g.world.states))
            with patch.object(Path,'open',side_effect=AssertionError('Frame reads a file')):
                app.draw()
            assert before==(g.x,g.y,g.time,dict(g.world.states))
            app.screen.save(output/(zone[0]+'.png'))
        # A non-square material responds to normals and preserves sprite alpha.
        maps={k:Image.new('RGBA',(32,19),v) for k,v in {
            'sprite':(90,110,90,255),'base':(90,110,90,255),'normal':(220,128,210,255),
            'rm':(60,0,0,255),'emissive':(0,0,0,255)}.items()}
        a=shade(fields(maps,(),SRGB),-30,40,None,None,1.,True,.2,1.)
        b=shade(fields(maps,(),SRGB),65,40,None,None,1.,True,.2,1.)
        assert a.size==(32,19) and ImageChops.difference(a,b).convert('RGB').getbbox()
        assert a.getchannel('A').getextrema()==(255,255)
        a.close();b.close()
        for image in maps.values():image.close()
        samples=[]
        for _ in range(45):
            app.update(1/60);start=perf_counter();app.draw();samples.append((perf_counter()-start)*1000)
        report={'passed':True,'physical_gaps':len(gaps),'context_E_interactions':interactions,
                'checkpoint_restore':True,'goal_clear':True,'groom_and_turn':True,'context_E_attack':True,'animated_material':True,'shore_safe':True,'habitat_fish_dodge_cases':4,'frame_file_io':0,
                'non_square_material_light_response':True,'draw_median_ms':median(samples),
                'draw_p95_ms':sorted(samples)[int(len(samples)*.95)],'computer_use':False}
        (output/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return report
    finally:app.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('habitat_artifacts'))
    print(json.dumps(verify(parser.parse_args().output),ensure_ascii=False,indent=2))
