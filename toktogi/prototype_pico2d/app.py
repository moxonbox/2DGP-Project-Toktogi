"""Scene composition and input ownership; native SDL stays behind Backend."""
from pathlib import Path
from time import perf_counter,sleep
from PIL import Image
from course import COURSE
from game import Game
from input_clock import Event,EventClock,CTRL
from materials import Assets
from motion_viewer import Viewer,MODES
from physics import STEP
from play_view import PlayView,SCREEN
from replays import game_replays
from timeline import FixedStepTimeline

ROOT=Path(__file__).resolve().parent
GAME_KEYS={k:k for k in ('left','right','up','down','space','e','f','g','x','q','z')}
GAME_KEYS.update(lshift='shift',rshift='shift')
CONTROL_KEYS=('p','escape','r','f1','f2','tab')

def route_event(event):
    if event.type=='focus_gained' or event.type in ('key_down','key_up') and event.key in GAME_KEYS:return 'tick'
    if event.type in ('quit','focus_lost') or event.type=='key_down' and event.key in CONTROL_KEYS and event.key!='f1':return 'close'
    return 'after'

class App:
    def __init__(self,assets_path=ROOT/'toktogi_assets.zip',course=COURSE,*,pose_path=None,native=False,profile='legacy'):
        self.backend=None;self.assets=None
        try:
            self.assets=Assets(assets_path,pose_path)
            self.game=Game(self.assets,course)
            self.viewer=Viewer(self.assets,dict(self.game.motion.game_previews()),list(game_replays(self.assets)))
            self.screen=Image.new('RGBA',SCREEN)
            self.play_view=PlayView(self.assets,course)
            self.scene='game';self.buttons=self.viewer.buttons
            self.timeline=FixedStepTimeline(STEP)
            self.running=True;self.focused=True
            self.physical_keys={};self.control_keys=set();self.viewer_keys=set()
            self.epoch=0;self.context_cutoff=float('-inf');self.dispatch_time=0.
            self.input_clock=None
            self.viewer.draw(self.screen,self.switch,header=False)
            self.buttons.clear()
            if native:
                from pico_backend import Backend
                self.backend=Backend(*SCREEN)
                self.viewer.native_text=self.backend.draw_text
        except BaseException:
            self.close()
            raise

    def close_context(self):
        self.epoch+=1;self.context_cutoff=self.dispatch_time
        self.physical_keys.clear();self.viewer_keys.clear()
        self.game.close_input(preserve_pose=True)
        self.viewer.searching=False;self.viewer.composition=''
        if self.backend:self.backend.set_text_input(False)

    def switch(self,which):
        if which!=self.scene:
            self.close_context();self.scene=which

    def event(self,event,*,at=None):
        event.collected_epoch=self.epoch
        event.input_time=self.timeline.wall_time if at is None else at
        if at is None:self._event(event)
        else:self.timeline.push(event,at)

    def update(self,dt):
        self.timeline.advance(dt,self._event,self.step_scene,route_event)
        self.viewer.light_time+=dt

    def step_scene(self,dt,on_input):
        if self.scene=='game':self.game.step(dt,on_input if self.game.run=='Playing' else None)
        else:self.viewer.step(dt)

    def draw(self):
        self.buttons.clear()
        if self.scene=='game':self.play_view.draw(self.screen,self.game)
        else:
            self.screen.paste((18,30,25,255),(0,0,*SCREEN))
            self.viewer.draw(self.screen,self.switch)
        if self.backend:
            self.backend.set_text_input(self.scene=='viewer' and self.viewer.searching,(34,89,306,38))
            self.backend.present(self.screen)
        return self.screen

    def _event(self,e):
        self.dispatch_time=getattr(e,'input_time',self.timeline.wall_time)
        contextual=e.type in ('key_down','key_up','text_input','text_editing','mouse_down','mouse_up','wheel')
        if contextual and (e.epoch is not None and e.epoch!=self.epoch or getattr(e,'collected_epoch',self.epoch)<self.epoch and self.dispatch_time<=self.context_cutoff):return
        if e.type=='quit':self.running=False
        elif e.type=='render_reset':raise RuntimeError('SDL renderer reset; restart the application.')
        elif e.type=='window_changed':
            if self.backend:self.backend.refresh_coordinates()
        elif e.type=='focus_lost':
            self.focused=False;self.control_keys.clear()
            if self.scene=='game' and self.game.run=='Playing':self.game.pause()
            self.close_context()
        elif e.type=='focus_gained':self.focused=True
        elif not self.focused:return
        elif e.type in ('mouse_motion','mouse_down','mouse_up'):
            self.viewer.pointer=e.pos
            if e.type=='mouse_down' and e.button==1:
                for rect,callback in reversed(self.buttons):
                    if rect.collidepoint(e.pos):callback();break
        elif e.type=='wheel' and self.scene=='viewer':self.viewer.select(self.viewer.selected-e.y)
        elif e.type=='text_input' and self.scene=='viewer' and self.viewer.searching:
            self.viewer.search=(self.viewer.search+e.text)[:100];self.viewer.composition='';self.viewer.filter()
        elif e.type=='text_editing' and self.scene=='viewer' and self.viewer.searching:self.viewer.composition=e.text
        elif e.type in ('key_down','key_up'):
            key,down=e.key,e.type=='key_down'
            if key in CONTROL_KEYS:
                if not down:self.control_keys.discard(key);return
                if key in self.control_keys or e.repeat:return
                self.control_keys.add(key)
            if down and key in ('f1','f2','tab'):
                self.switch('viewer' if key=='f2' or key=='tab' and self.scene=='game' else 'game')
            elif self.scene=='viewer' and self.viewer.searching:
                if down and key in ('escape','return'):
                    self.viewer.searching=False;self.viewer.composition=''
                    if self.backend:self.backend.set_text_input(False)
                elif down and key=='backspace':self.viewer.search=self.viewer.search[:-1];self.viewer.filter()
            elif down and key=='escape':
                if self.scene=='viewer':self.switch('game')
                else:self.game.pause();self.close_context()
            elif self.scene=='game':
                if down and key=='r':self.close_context();self.game.reset(self.game.checkpoint)
                elif down and key=='p':self.game.pause();self.close_context()
                elif key in GAME_KEYS and self.game.run=='Playing':
                    physical=e.scancode if e.scancode is not None else key
                    binding=GAME_KEYS[key]
                    if down:
                        if e.repeat or physical in self.physical_keys:return
                        already=binding in self.physical_keys.values()
                        self.physical_keys[physical]=binding
                        if not already:self.game.edge(binding,True)
                    elif physical in self.physical_keys:
                        del self.physical_keys[physical]
                        if binding not in self.physical_keys.values():self.game.edge(binding,False)
            elif self.scene=='viewer':
                repeatable=key in ('up','down','left','right','backspace')
                if not down:self.viewer_keys.discard(key);return
                if not repeatable and (key in self.viewer_keys or e.repeat):return
                self.viewer_keys.add(key);v=self.viewer
                if key=='m':v.mode=(v.mode+1)%len(MODES)
                elif key=='l':v.light_mode=(v.light_mode+1)%3
                elif key=='f3':v.markers=not v.markers
                elif key=='f' and e.mod&CTRL:v.focus_search()
                elif key in ('up','down'):v.select(v.selected+(1 if key=='down' else -1))
                elif key in ('left','right'):v.move_frame(1 if key=='right' else -1)
                elif key=='space':v.toggle()
                elif key=='v':v.next_view()

    def run(self):
        if self.backend is None:raise RuntimeError('Native run requires App(native=True).')
        self.input_clock=EventClock(position_transform=self.backend.logical_point)
        previous=perf_counter()
        try:
            while self.running:
                begin=perf_counter();dt=begin-previous;previous=begin
                for event in self.input_clock.events():self.event(event,at=event.timestamp)
                self.update(dt);self.draw()
                sleep(max(0,1/60-(perf_counter()-begin)))
        finally:self.close()

    def close(self):
        if hasattr(self,'viewer'):self.viewer.text_surface.cache_clear()
        try:
            if self.assets:self.assets.close();self.assets=None
        finally:
            if self.backend:self.backend.close();self.backend=None
