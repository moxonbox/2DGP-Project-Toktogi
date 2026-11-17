"""Pygame application composition, event routing and mode ownership."""
import os
from pathlib import Path

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import pygame as pg

from course import COURSE
from game import Game
from input_clock import EventClock
from materials import Assets
from motion_viewer import Viewer, MODES
from physics import STEP
from play_view import PlayView, SCREEN
from replays import game_replays
from timeline import FixedStepTimeline

ROOT=Path(__file__).resolve().parent
GAME_KEYS={pg.K_LEFT:'left',pg.K_RIGHT:'right',pg.K_UP:'up',pg.K_DOWN:'down',pg.K_SPACE:'space',
           pg.K_LSHIFT:'shift',pg.K_RSHIFT:'shift',pg.K_e:'e',pg.K_f:'f',pg.K_g:'g',pg.K_x:'x',pg.K_q:'q',pg.K_z:'z'}

CONTROL_KEYS=(pg.K_p,pg.K_ESCAPE,pg.K_r,pg.K_F1,pg.K_F2,pg.K_TAB)

def route_event(event):
    key_event=event.type in (pg.KEYDOWN,pg.KEYUP)
    if event.type==pg.WINDOWFOCUSGAINED or key_event and event.key in GAME_KEYS:
        return 'tick'
    if event.type in (pg.QUIT,pg.WINDOWFOCUSLOST) or event.type==pg.KEYDOWN and event.key in CONTROL_KEYS and event.key!=pg.K_F1:
        return 'close'
    return 'after'


class App:
    def __init__(self,assets_path=ROOT/'toktogi_assets.zip',course=COURSE,*,pose_path=None):
        pg.init()
        pg.display.set_caption('톡토기 · 작은 톡토기의 큰 도약')
        self.screen=pg.display.set_mode(SCREEN)
        self.assets=Assets(assets_path,pose_path)
        self.game=Game(self.assets,course)
        self.viewer=Viewer(self.assets,dict(self.game.motion.game_previews()),list(game_replays(self.assets)))
        self.scene='game'
        self.clock=pg.time.Clock()
        self.play_view=PlayView(self.assets,course)
        self.buttons=self.viewer.buttons
        self.timeline=FixedStepTimeline(STEP)
        self.running=True
        self.focused=True
        self.physical_keys=set()
        self.control_keys=set()
        self.input_clock=EventClock()
        self.viewer.draw(pg.Surface(SCREEN),self.switch,header=False)
        self.buttons.clear()
        self.clock.tick()
        self.clock_origin=pg.time.get_ticks()

    def switch(self,which):
        if which==self.scene:
            return
        self.game.close_input(preserve_pose=True)
        self.physical_keys.clear()
        self.viewer.searching=False
        pg.key.stop_text_input()
        self.scene=which

    def event(self,event,*,at=None):
        if at is None:
            self._event(event)
        else:
            self.timeline.push(event,at)

    def update(self,dt):
        self.timeline.advance(dt,self._event,self.step_scene,route_event)
        self.viewer.light_time+=dt

    def step_scene(self,dt,on_input):
        if self.scene=='game':
            self.game.step(dt,on_input if self.game.run=='Playing' else None)
        else:
            self.viewer.step(dt)

    def draw(self):
        self.buttons.clear()
        if self.scene=='game':
            self.play_view.draw(self.screen,self.game)
        else:
            self.screen.fill((18,30,25))
            self.viewer.draw(self.screen,self.switch)
        pg.display.flip()

    def _event(self,e):
        if e.type==pg.QUIT:
            self.running=False
        elif e.type==pg.WINDOWFOCUSLOST:
            self.focused=False
            self.physical_keys.clear()
            self.control_keys.clear()
            if self.scene=='game' and self.game.run=='Playing':
                self.game.pause()
            self.game.close_input(preserve_pose=True)
        elif e.type==pg.WINDOWFOCUSGAINED:
            self.focused=True
        elif e.type==pg.MOUSEBUTTONDOWN and e.button==1:
            for rect,callback in reversed(self.buttons):
                if rect.collidepoint(e.pos):
                    callback()
                    break
        elif e.type==pg.MOUSEWHEEL and self.scene=='viewer':
            self.viewer.select(self.viewer.selected-e.y)
        elif e.type==pg.TEXTINPUT and self.viewer.searching:
            self.viewer.search=(self.viewer.search+e.text)[:100]
            self.viewer.filter()
        elif e.type in (pg.KEYDOWN,pg.KEYUP):
            key,down=e.key,e.type==pg.KEYDOWN
            if key in CONTROL_KEYS:
                if not down:
                    self.control_keys.discard(key)
                    return
                if key in self.control_keys or not self.focused or getattr(e,'repeat',False):
                    return
                self.control_keys.add(key)
            if down and key in (pg.K_F1,pg.K_F2,pg.K_TAB):
                self.switch('viewer' if key==pg.K_F2 or key==pg.K_TAB and self.scene=='game' else 'game')
            elif self.viewer.searching:
                if down and key in (pg.K_ESCAPE,pg.K_RETURN):
                    self.viewer.searching=False
                    pg.key.stop_text_input()
                elif down and key==pg.K_BACKSPACE:
                    self.viewer.search=self.viewer.search[:-1]
                    self.viewer.filter()
            elif down and key==pg.K_ESCAPE:
                if self.scene=='viewer':
                    self.switch('game')
                else:
                    self.game.pause()
            elif down and self.scene=='viewer' and key==pg.K_m:
                self.viewer.mode=(self.viewer.mode+1)%len(MODES)
            elif down and self.scene=='viewer' and key==pg.K_l:
                self.viewer.light_mode=(self.viewer.light_mode+1)%3
            elif down and self.scene=='viewer' and key==pg.K_F3:
                self.viewer.markers=not self.viewer.markers
            elif self.scene=='game':
                if down and key==pg.K_r:
                    self.game.reset(self.game.checkpoint)
                    self.physical_keys.clear()
                elif down and key==pg.K_p:
                    self.game.pause()
                    self.physical_keys.clear()
                elif key in GAME_KEYS and self.focused:
                    binding=GAME_KEYS[key]
                    if down:
                        if getattr(e,'repeat',False):
                            return
                        self.physical_keys.add(key)
                        self.game.edge(binding,True)
                    else:
                        self.physical_keys.discard(key)
                        if not any(GAME_KEYS[k]==binding for k in self.physical_keys):
                            self.game.edge(binding,False)
            elif down:
                v=self.viewer
                if key==pg.K_f and e.mod & pg.KMOD_CTRL:
                    self.viewer.focus_search()
                elif key in (pg.K_UP,pg.K_DOWN):
                    v.select(v.selected+(1 if key==pg.K_DOWN else -1))
                elif key in (pg.K_LEFT,pg.K_RIGHT):
                    v.move_frame(1 if key==pg.K_RIGHT else -1)
                elif key==pg.K_SPACE:
                    v.toggle()
                elif key==pg.K_v:
                    self.viewer.next_view()

    def run(self):
        while self.running:
            dt=self.clock.tick(60)/1000
            for event in self.input_clock.events():
                stamp=getattr(event,'timestamp',None)
                at=self.timeline.wall_time+dt if stamp is None else (((stamp-self.clock_origin+0x80000000)&0xffffffff)-0x80000000)/1000
                self.event(event,at=at)
            self.update(dt)
            self.draw()
        self.assets.close()
        pg.quit()


