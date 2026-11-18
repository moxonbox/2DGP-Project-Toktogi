"""Focused Windows render budget, unchanged pixels and control-response checks."""
import argparse,json,statistics,hashlib
from pathlib import Path
from time import perf_counter

ROOT=Path(__file__).resolve().parent
from app import App
from PIL import Image,ImageChops
from input_clock import Event
from physics import STEP
from game import Game
from lighting import shade

def focused_checks(app):
    assert Game(app.assets).walk_speed==24
    for value in (0,-1,float('nan'),float('inf')):
        try:Game(app.assets,walk_speed=value)
        except ValueError:pass
        else:raise AssertionError('Invalid walk speed accepted.')
    g=app.game;app.switch('game');g.reset()
    app.event(Event('key_down',key='d'))
    acceleration=0
    for _ in range(24):
        app.update(STEP);acceleration+=STEP
        if g.vx>=72:break
    assert g.vx==72 and acceleration<=.101
    app.event(Event('key_up',key='d'))
    stopping=0
    for _ in range(24):
        app.update(STEP);stopping+=STEP
        if g.vx==0:break
    assert g.vx==0 and stopping<=.067
    app.event(Event('key_down',key='d'))
    for _ in range(12):app.update(STEP)
    app.event(Event('key_up',key='d'));app.event(Event('key_down',key='a'))
    reversing=0
    for _ in range(24):
        app.update(STEP);reversing+=STEP
        if g.vx<0:break
    assert g.vx<0 and reversing<=.051
    app.close_context()
    for state in ('Paused','Playing','Failed','Cleared'):
        g.run=state
        expected=Image.new('RGBA',app.screen.size,(63,45,29,255));actual=expected.copy()
        app.play_view._paint_overlay(expected,g);app.play_view.overlay(actual,g)
        assert ImageChops.difference(expected,actual).getbbox(alpha_only=False) is None
        expected.close();actual.close()
    key=app.assets.tracks['idle','right'].cells[0]
    for scale in (1,2,3):
        source=Image.new('RGBA',(200,150),(30,45,60,191))
        args=(key,(-20,-15),scale)
        expected=app.assets.renderer.composite_bloom(source,*args,clip=(8,4,190,140))
        actual=source.copy()
        result=app.assets.renderer.composite_bloom(actual,*args,clip=(8,4,190,140),in_place=True)
        assert result is actual and expected.tobytes()==actual.tobytes()
        assert source.getextrema()==((30,30),(45,45),(60,60),(191,191))
        source.close();expected.close();actual.close()
    return {'max_speed_px_s':72,'accelerate_ms':round(acceleration*1000,2),
            'stop_ms':round(stopping*1000,2),'reverse_direction_ms':round(reversing*1000,2),
            'hud_states':4,'bloom_scales':3,'scope':'120 Hz simulation response; excludes device/poll latency.'}


def run(output):
    output.mkdir(parents=True,exist_ok=True)
    app=App(native=True,profile='habitat');app.backend.shown=True
    try:
        g=app.game
        results={}
        for phase in ('habitat_motion','viewer_light_bloom'):
            times=[];app.switch('game' if phase=='habitat_motion' else 'viewer')
            app.viewer.mode=0;app.viewer.light_mode=2;app.viewer.bloom=True;app.viewer.playing=True
            for i in range(180):
                if phase=='habitat_motion':
                    # Authored motion frames + variable world-space light, including cold cache entries.
                    g.x=150+(i%120);g.y=380;g.clip='walk';g.visual_time=(i/60)%.48
                    g.gait=g.visual_time;g.time=i/60;g.view='right'
                    app.play_view.step(g,1/60)
                else:app.viewer.step(1/60);app.viewer.light_time=i/60
                start=perf_counter();app.draw();times.append((perf_counter()-start)*1000)
                if i in (0,17,61,119):app.screen.save(output/(phase+'_'+str(i)+'.png'))
            ordered=sorted(times)
            results[phase]={'frames':len(times),'median_ms':statistics.median(times),
                            'p95_ms':ordered[170],'max_ms':ordered[-1]}
        keys=[app.assets.tracks[name,view].cells[0] for name in ('idle','walk','jump_pre','attack_demo') for view in ('left','right')]
        hashes={}
        for i,key in enumerate(keys):
            for flat in (False,True):
                image=app.assets.render(key,'lit',(17,29),(i*41-80,45),roughness=.27 if i%2 else None,
                                        metallic=.35 if i%3==0 else None,flat_normal=flat)
                name=f'material_{i}_{int(flat)}.png'
                image.save(output/name)
                raw=shade(app.assets.surface_fields(key,flat),i*41-97,29-45,
                          .27 if i%2 else None,.35 if i%3==0 else None,
                          1.,True,.115,app.assets.renderer.emission_scale)
                hashes[name]=hashlib.sha256(raw.tobytes()).hexdigest()
                raw.close()
        before=json.loads((ROOT/'optimization_before.json').read_text(encoding='utf-8'))
        # Display palette and stage art can change intentionally; retain the raw material golden.
        expected={name:digest for name,digest in before['pixels_sha256'].items() if name.startswith('material_')}
        assert hashes==expected,'Original BRDF material pixels changed.'
        results['raw_material_pixel_references']=len(hashes)
        results['raw_material_pixel_changed_channels']=0
        results['controls']=focused_checks(app)
        results['driver']=app.backend.driver;results['renderer']=app.backend.renderer_name
        results['scope']='Hidden Windows renderer; render+upload+present; no profiling, sleep, screenshots in timing.'
        results['p95_budget_ms']=1000/60
        results['p95_target_met']={name:results[name]['p95_ms']<=1000/60 for name in ('habitat_motion','viewer_light_bloom')}
        (output/'results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(results,indent=2))
    finally:app.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'optimization_artifacts')
    run(parser.parse_args().output)
