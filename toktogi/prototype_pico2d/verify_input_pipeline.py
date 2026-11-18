"""Focused event pipeline, chords and latency checks; no visible window."""
import argparse
import ctypes
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import app as app_module
from app import App
from game import Game
from input_clock import CTRL,Event,EventClock
from physics import STEP
from stage_world import habitat_world
from timeline import FixedStepTimeline

ROOT=Path(__file__).resolve().parent


def verify(asset_root=None):
    app=App(profile='legacy',asset_root=asset_root)
    def fresh():
        app.scene='game';app.focused=True;app.running=True;app.game.reset();app.game.walk_speed=72.
        app.timeline=FixedStepTimeline(STEP);app.physical_keys.clear();app.control_keys.clear();app.viewer_keys.clear()
        app.epoch=0;app.context_cutoff=float('-inf');app.dispatch_time=0.
        app.viewer.searching=False;app.viewer.search='';app.viewer.composition='';app.viewer.filter()
    def key(name,down=True,*,at=None,scan=None,repeat=False,mod=0):
        event=Event('key_down' if down else 'key_up',name,timestamp=at,scancode=scan,repeat=repeat,mod=mod)
        app.event(event,at=at)
    checks={};taps={};latencies={}
    try:
        fresh();app.switch('viewer')
        for _ in range(5):
            key('f',mod=CTRL);assert app.viewer.searching
            key('f',False);key('return');key('return',False)
            assert not app.viewer.searching and 'f' not in app.viewer_keys
        checks['Ctrl_F_search_reopened_five_times']=True
        fresh();key('d',scan=7);key('unknown',False,scan=7)
        assert not app.game.held and not app.physical_keys
        app.update(.05);assert not app.game.input_presses
        checks['physical_release_survives_changed_symbol']=True
        fresh();key('d',scan=0);key('s',scan=0)
        assert {'right','up'}<=app.game.held and len(app.physical_keys)==2
        key('d',False,scan=0);key('s',False,scan=0)
        assert not app.physical_keys and not app.game.held
        checks['unknown_scancode_keys_remain_independent']=True
        fresh();key('f');attack=app.game.work;assert attack
        key('x');assert app.game.work is attack and app.game.notice_priority
        key('x',False);app.update(1.);assert app.game.work is None
        key('x');attack=app.game.work;assert attack and attack['key']=='x' and not app.game.notice_priority
        key('x',repeat=True);assert app.game.work is attack
        key('f',False);assert 'x' in app.game.held
        key('x',False);assert 'x' not in app.game.held
        fresh();key('f');app.update(1.)
        target=app.game.world.targets('shell')[0]
        platform=next(p for p in app.game.course.platforms if p.x0<=target.point[0]<=p.x1 and p.y==target.point[1])
        app.game.support=platform;app.game.x=target.point[0]-29;app.game.y=platform.y
        key('e');assert app.game.work and app.game.work['key']=='x'
        checks['fresh_F_X_E_alias_attacks_and_release_count']=True
        for fps in (10,15,30,60,120,240):
            fresh();x=app.game.x;key('d',at=.001);key('d',False,at=.004)
            while app.timeline.wall_time<.1-1e-9:app.update(1/fps)
            taps[str(fps)]=app.game.x-x
            assert taps[str(fps)]>0 and not app.game.held and not app.game.input_presses and not app.physical_keys
        assert max(taps.values())-min(taps.values())<1e-9
        checks['3ms_tap_retained_once_across_frame_rates']=True
        fresh();key('lctrl',at=.001);app.update(.02)
        key('d',at=.021);key('lctrl',False,at=.023);key('d',False,at=.024)
        x=app.game.x;app.update(.04)
        assert app.game.yaw_angle>0 and app.game.x==x and not app.game.held
        checks['released_modifier_chord_retained_for_one_tick']=True
        fresh();key('a',at=.001);key('d',at=.001);app.update(.02)
        assert app.game.vx==0
        key('a',False);app.update(.04);assert app.game.vx>0
        before=app.game.vx;key('a');key('d',False);app.update(STEP)
        assert abs(app.game.vx-(before-1700*STEP))<1e-7
        checks['opposites_neutral_and_rollover_release_immediate']=True
        fresh()
        for name in ('d','s','lctrl','rctrl','lshift'):key(name,at=.001)
        key('space',at=.002);key('space',False,at=.004);app.update(.14)
        assert app.game.launch_count==1 and app.game.aim==1
        assert {'right','up','shift','run'}<=app.game.held
        key('lctrl',False);assert 'shift' in app.game.held
        for name in ('d','s','rctrl','lshift'):key(name,False)
        app.update(.05);assert not app.game.held and not app.game.input_presses
        checks['six_key_chord_jump_and_dual_Ctrl_release']=True
        fresh();key('d',at=.001);key('space',at=.002);key('p',at=.003);key('space',False,at=.004)
        app.update(.02);assert app.game.run=='Paused' and not app.game.input_presses and not app.physical_keys
        key('p',False);key('p');key('p',False);app.update(.05)
        assert app.game.run=='Playing' and app.game.launch_count==0 and not app.game.held
        key('d');app.event(Event('focus_lost'));assert not app.game.held and not app.game.input_presses
        checks['pause_focus_context_clear_without_ghost_jump']=True
        for fps in (10,15,30,60,120,240):
            fresh();g=app.game;x=g.x;accepted=[];moved=[];observed=[]
            dispatch,step_scene=app._event,app.step_scene
            def record(event):
                dispatch(event)
                if event.type=='key_down' and event.key=='d':accepted.append(g.time)
            def tick(dt,apply):
                step_scene(dt,apply)
                if not moved and g.x!=x:moved.append(g.time)
            key('d',at=.001)
            with patch.object(app,'_event',record),patch.object(app,'step_scene',tick):
                while app.timeline.wall_time<.1-1e-9:
                    app.update(1/fps)
                    if moved and not observed:observed.append(app.timeline.wall_time)
            assert accepted and moved
            accept_ms=(accepted[0]-.001)*1000;move_ms=(moved[0]-.001)*1000
            assert accept_ms<=STEP*1000+1e-7 and move_ms<=2*STEP*1000+1e-7
            latencies[str(fps)]={'event_to_tick_accept_ms':round(accept_ms,3),
                                 'event_to_simulation_move_ms':round(move_ms,3),
                                 'frame_observing_move_ms':round((observed[0]-.001)*1000,3)}
        for fps in (10,15,30,60,120,240):
            accepted_delays=[];move_delays=[];frame_delays=[]
            for phase in range(16):
                fresh();g=app.game;x=g.x;at=(phase+.5)/16/fps
                accepted=[];moved=[];observed=[];dispatch,step_scene=app._event,app.step_scene
                def record(event):
                    dispatch(event)
                    if event.type=='key_down':accepted.append(g.time)
                def tick(dt,apply):
                    step_scene(dt,apply)
                    if not moved and g.x!=x:moved.append(g.time)
                key('d',at=at)
                with patch.object(app,'_event',record),patch.object(app,'step_scene',tick):
                    for _ in range(max(6,fps//2)):
                        app.update(1/fps)
                        if moved:
                            observed.append(app.timeline.wall_time)
                            break
                assert accepted and moved and observed,(fps,phase)
                accepted_delays.append((accepted[0]-at)*1000)
                move_delays.append((moved[0]-at)*1000)
                frame_delays.append((observed[0]-at)*1000)
            assert max(accepted_delays)<=STEP*1000+1e-7
            assert max(move_delays)<=2*STEP*1000+1e-7
            latencies[str(fps)]['phase_sweep']={'samples':16,
                'max_tick_accept_ms':round(max(accepted_delays),3),
                'max_simulation_move_ms':round(max(move_delays),3),
                'max_frame_observation_ms':round(max(frame_delays),3)}
        fresh();key('d');key('s');app.update(.2);key('d',False);key('a')
        angle=app.game.yaw_angle;elapsed=0.
        while elapsed<.3:
            app.update(STEP);elapsed+=STEP
            if app.game.yaw_angle!=angle:break
        assert elapsed<=.101,elapsed
        checks['aim_neutral_rotation_wait_under_100ms']=True
        aim_delay=round(elapsed*1000,3)
        fresh();clock=SimpleNamespace(events=lambda:[Event('key_down','d',timestamp=.012)])
        backend=SimpleNamespace(sdl=SimpleNamespace(SDL_GetTicks=lambda:0),logical_point=lambda p:p)
        observed=[]
        def draw_once():observed.append('right' in app.game.held);app.running=False
        with patch.object(app,'backend',backend),patch.object(app,'draw',draw_once),patch.object(app,'close',lambda:None),patch.object(app_module,'EventClock',return_value=clock),patch.object(app_module,'perf_counter',side_effect=[0.,.010,.020,.021]),patch.object(app_module,'sleep',lambda _:None):app.run()
        assert observed==[True]
        checks['event_during_poll_processed_in_current_frame']=True
        from stage_view import StageView
        from PIL import Image
        world=habitat_world();g=Game(app.assets,world=world,directional_yaw=True)
        g.time=.1;g.support=None;g.start_work('x');assert g.notice_priority
        view=StageView.__new__(StageView);view.world=world;view.pond=SimpleNamespace(phase='idle',repels=0)
        view.font=view.title_font=view.small_font=object();view.hud_key=None;view.hud_parts=[]
        screen=Image.new('RGBA',(1280,744));draw=Mock()
        with patch('stage_view.ImageDraw.Draw',return_value=draw):view.overlay(screen,g)
        assert any(call.args[1]==g.notice for call in draw.text.call_args_list)
        for image,_ in view.hud_parts:image.close()
        screen.close();checks['rejection_reason_visible_before_four_seconds']=True
        os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
        from pico_backend import Backend
        native=Backend(96,48)
        try:
            sdl=native.sdl;sdl.SDL_PumpEvents();sdl.SDL_FlushEvents(sdl.SDL_FIRSTEVENT,sdl.SDL_LASTEVENT)
            raw=(sdl.SDL_Event*2)()
            for i,event in enumerate(raw):
                event.type=sdl.SDL_KEYDOWN if i==0 else sdl.SDL_KEYUP;event.common.timestamp=1050+i
                event.key.keysym.sym=sdl.SDLK_F9 if i==0 else sdl.SDLK_UNKNOWN
                event.key.keysym.scancode=sdl.SDL_SCANCODE_D
            assert sdl.SDL_PeepEvents(raw,2,sdl.SDL_ADDEVENT,sdl.SDL_FIRSTEVENT,sdl.SDL_LASTEVENT)==2
            native_clock=EventClock(origin=1000)
            with patch.object(sdl,'SDL_GetTicks',return_value=1100):events=native_clock.events()
            assert [e.key for e in events]==['d','d'] and events[0].symbol=='f9'
            checks['native_scancode_identity_and_original_symbol_preserved']=True
        finally:native.close()
        return {'passed':True,'checks':checks,'short_tap_displacement_px':taps,
                'latency_matrix':latencies,'aim_to_rotation_ms':aim_delay,
                'native_driver':'dummy','computer_use':False,
                'limits':'Synthetic event/tick/frame measurements; physical keyboard rollover, IME/OS hooks and input-to-photon latency not measured.'}
    finally:app.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--asset-root',type=Path)
    report=verify(parser.parse_args().asset_root)
    (ROOT/'input_pipeline_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
