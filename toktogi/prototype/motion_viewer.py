"""Standalone Pygame motion and material inspection scene."""
import math
from functools import lru_cache
import pygame as pg

TINT=(240,246,223)
INK=(219,232,218)
MUTED=(157,183,169)
LIME=(212,238,163)
TEXT=(18,31,27)
PANEL=(27,44,38)
RIM=(65,91,78)
MODES=(('lit','실시간 조명'),('sprite','원본 Sprite'),('base','Base · Alpha'),('normal','Normal'),
       ('rm','Rough · Metal'),('emissive','Emissive'),('outline','윤곽선'))
LABELS={'idle':'대기','walk_start':'보행 시작','walk':'보행','jump_pre':'도약 준비','jump_release':'도약 발사',
        'land_soft':'착지','land_hard':'강한 착지','elastic_release':'탄성 도약','groom':'더듬이·도약기관 손질',
        'air_rise':'상승','air_apex':'정점','air_fall':'하강','feed_pre':'섭식 준비','feed_cycle':'섭식',
        'feed_end':'섭식 종료','attack_demo':'공격','hit_ground':'피격','goal':'목표 도달','failed':'낙하 실패',
        'respawn':'재시작','obs_antenna_clean':'06 더듬이 손질','obs_furca_clean':'07 도약기관 손질',
        'obs_saliva_clean':'08 방울 손질','transition_antenna_furca.png':'06–07 손질 연결'}


class Viewer:
    def __init__(self,assets,game_previews=None,replays=()):
        self.assets=assets
        self.game_previews=dict(game_previews or {})
        self.replay_events={name:events for name,_,events in replays}
        self.game_previews.update((name,track) for name,track,_ in replays)
        self.names=list(assets.clips)+list(assets.sequences)+list(self.game_previews)
        self.filtered=self.names.copy()
        self.search=''
        self.searching=False
        self.selected=0
        self.view=0
        self.time=0.
        self.playing=True
        self.background=0
        self.scale=3
        self.mode=0
        self.light_mode=0
        self.light_time=0.
        self.roughness=None
        self.metallic=None
        self.emission=True
        self.power=1.
        self.markers=False
        self.buttons=[]
        font=pg.font.match_font('malgungothic') or pg.font.match_font('arial')
        self.fonts={size:pg.font.Font(font,size) for size in (13,14,15,16,18,20,22,23,28,34)}

    @property
    def name(self):
        return self.filtered[self.selected] if self.filtered else None

    @property
    def views(self):
        if self.name in self.assets.clips:
            return self.assets.clips[self.name]['supported_views']
        return ['sequence']

    @property
    def track(self):
        if not self.name:
            return None
        if self.name in self.game_previews:
            return self.game_previews[self.name]
        return self.assets.sequences[self.name] if self.name in self.assets.sequences else self.assets.tracks[self.name,self.views[self.view]]

    def filter(self):
        words=self.search.casefold().split()
        self.filtered=[n for n in self.names if all(w in (n+' '+LABELS.get(n,'')+' '+self.assets.clips.get(n,{}).get('description','')).casefold() for w in words)]
        self.select(0)

    def select(self,index):
        self.selected=max(0,min(index,len(self.filtered)-1))
        self.time=0.
        self.view=0
        self.playing=True

    def move_frame(self,direction):
        track=self.track
        if track:
            i=max(0,min(track.index(self.time)+direction,len(track.cells)-1))
            self.time=track.start(i)
            self.playing=False

    def toggle(self):
        track=self.track
        if track:
            if not track.loop and self.time>=track.duration:
                self.time=0.
            self.playing=not self.playing

    def step(self,dt):
        if not self.playing or self.track is None:
            return
        track=self.track
        self.time+=dt
        if track.loop:
            self.time%=track.duration
        elif self.time>=track.duration:
            self.time=track.duration
            self.playing=False

    def text(self,label,x,y,size=16,color=INK):
        surface=self.text_surface(str(label),size,color)
        self.screen.blit(surface,(x,y))

    @lru_cache(maxsize=512)
    def text_surface(self,label,size,color):
        return self.fonts[size].render(label,True,color)

    def rect(self,rect,color=PANEL,radius=12):
        pg.draw.rect(self.screen,color,rect,border_radius=radius)

    def button(self,label,x,y,w,callback,active=False):
        rect=pg.Rect(x,y,w,33)
        hover=rect.collidepoint(pg.mouse.get_pos())
        fill=LIME if active else (50,74,62) if hover else (35,55,47)
        self.rect(rect,fill,7)
        pg.draw.rect(self.screen,RIM,rect,1,border_radius=7)
        rendered=self.text_surface(label,14,TEXT if active else INK)
        self.screen.blit(rendered,rendered.get_rect(center=rect.center))
        self.buttons.append((rect,callback))

    def cycle(self,name,options):
        current=getattr(self,name)
        setattr(self,name,options[(options.index(current)+1)%len(options)])

    def header(self,switch):
        self.text('톡토기',20,14,34,TINT)
        self.text('작은 톡토기의 큰 도약',132,29,16,MUTED)
        self.button('F1  플레이',1040,21,106,lambda:switch('game'),False)
        self.button('F2  모션·조명',1155,21,105,lambda:switch('viewer'),True)

    def light_at(self,area,default):
        if self.light_mode==1:
            point=pg.mouse.get_pos()
            return point if area.collidepoint(point) else default
        if self.light_mode==2:
            return round(default[0]+math.sin(self.light_time*1.35)*130),round(default[1]+math.cos(self.light_time*1.35)*81)
        return default

    def material_panel(self,top):
        x=994
        self.rect((x,top,266,345))
        self.text('조명과 재질',x+15,top+12,20,TINT)
        for i,(mode,label) in enumerate(MODES):
            self.button(label,x+14+(i%2)*121,top+49+36*(i//2),116,lambda i=i:setattr(self,'mode',i),self.mode==i)
        self.text('광원',x+15,top+201,14,MUTED)
        for i,label in enumerate(('고정','마우스','이동')):
            self.button(label,x+58+i*62,top+194,56,lambda i=i:setattr(self,'light_mode',i),self.light_mode==i)
        self.button('거칠기  '+('원본' if self.roughness is None else f'{self.roughness:.2f}'),x+14,top+235,116,
                    lambda:self.cycle('roughness',(None,.22,.52,.85)))
        self.button('금속성  '+('원본' if self.metallic is None else f'{self.metallic:.2f}'),x+135,top+235,116,
                    lambda:self.cycle('metallic',(None,.0,.5,1.)))
        self.button('발광 '+('켜짐' if self.emission else '꺼짐'),x+14,top+273,116,lambda:setattr(self,'emission',not self.emission),self.emission)
        self.button('강도 '+f'{self.power:.1f}',x+135,top+273,116,lambda:self.cycle('power',(1.,.4,1.65)))
        self.text('L  광원 전환    M  패스 전환',x+14,top+320,13,MUTED)

    def sprite(self,key,origin,light,scale=1):
        local_light=tuple(origin[i]+(light[i]-origin[i])/scale for i in (0,1))
        image=self.assets.render(key,MODES[self.mode][0],origin,local_light,
                                 self.roughness,self.metallic,self.power,self.emission)
        if scale>1:
            image=pg.transform.scale(image,(128*scale,128*scale))
        self.screen.blit(image,origin)
        if self.markers:
            markers,support=self.assets.sample(key)
            for name,data in markers.items():
                if name.startswith('foot_contact_'):
                    color=LIME if name[-2:] in support else (245,156,125)
                    pg.draw.circle(self.screen,color,tuple(round(origin[i]+scale*data['xy'][i]) for i in (0,1)),2*scale)
                elif name in ('mouth_marker','furca_marker'):
                    pg.draw.circle(self.screen,(142,213,235),tuple(round(origin[i]+scale*data['xy'][i]) for i in (0,1)),2*scale,1)

    def draw(self,screen,switch,*,header=True):
        self.screen=screen
        if header:self.header(switch)
        v=self
        self.rect((20,77,334,560))
        self.rect((34,89,306,38),(39,64,53) if v.searching else (28,51,41),7)
        self.buttons.append((pg.Rect(34,89,306,38),self.focus_search))
        self.text(v.search[-27:]+'▏' if v.searching else (v.search[-30:] or '검색  ·  Ctrl+F'),44,99,15,TINT)
        self.text(f'{len(v.filtered)} / {len(v.names)}   ·   클립 {len(self.assets.clips)}   ·   전환 {len(self.assets.sequences)}',35,137,14,MUTED)
        offset=max(0,min(v.selected-6,len(v.filtered)-15))
        for i in range(offset,min(offset+15,len(v.filtered))):
            item=v.filtered[i]
            rect=pg.Rect(33,166+(i-offset)*29,307,27)
            if i==v.selected or rect.collidepoint(pg.mouse.get_pos()):
                self.rect(rect,LIME if i==v.selected else (50,75,64),5)
            self.text(item.removesuffix('.png'),42,rect.y+3,14,TEXT if i==v.selected else INK)
            self.buttons.append((rect,lambda i=i:v.select(i)))
        area=pg.Rect(371,77,609,560)
        self.rect(area,PANEL)
        self.material_panel(77)
        self.rect((994,437,266,200))
        self.text('프리뷰 조작',1008,450,20,TINT)
        for i,line in enumerate(('↑ ↓  클립 선택','← →  프레임 이동','Space  재생 / 정지','V  지원 방향 · F3 접지점','마우스  광원 이동')):
            self.text(line,1008,485+i*25,15,MUTED)
        self.text('F1 코스  ·  F2 검수  ·  M 패스  ·  L 광원',21,659,16,TINT)
        track=v.track
        if not track:
            self.text('검색 결과가 없습니다.',430,300,22,TINT)
            return
        index=track.index(v.time)
        key=track.cells[index]
        name=v.name.removesuffix('.png')
        title=LABELS.get(v.name,name)
        self.text(title,395,94,23 if self.fonts[23].size(title)[0]<553 else 18,TINT)
        self.text(f'{key[1]}    {index+1} / {len(track.cells)} 프레임    {track.duration:.2f}초',396,128,15,MUTED)
        if v.name in self.game_previews:
            note='게임 입력 리플레이' if v.name in self.replay_events else '게임 재생 시간'
            self.text(note,815,128,15,LIME)
        if events:=self.replay_events.get(v.name):
            self.text(' · '.join(f'{label} {t:.3f}s' for label,t in events),515,128,13,MUTED)
        center=pg.Rect(430,159,488,385)
        self.rect(center,((47,63,56),(122,134,99),(224,226,200))[v.background],10)
        light=self.light_at(center,(714,262))
        scale=v.scale
        origin=(center.centerx-128*scale//2,center.centery-128*scale//2)
        foot_y=origin[1]+self.assets.pivot[1]*scale
        pg.draw.line(self.screen,(145,167,139),(center.left+42,foot_y),(center.right-42,foot_y),1)
        self.sprite(key,origin,light,scale)
        pg.draw.circle(self.screen,TINT,light,5,1)
        self.button('일시정지' if v.playing else '재생',395,558,89,v.toggle,v.playing)
        self.button('이전',491,558,57,lambda:v.move_frame(-1))
        self.button('다음',555,558,57,lambda:v.move_frame(1))
        self.button('방향 '+key[1][:7],619,558,107,self.next_view)
        self.button('배경',733,558,65,lambda:setattr(v,'background',(v.background+1)%3))
        self.button(f'{v.scale}×',805,558,62,lambda:setattr(v,'scale',v.scale%3+1))
        bar=pg.Rect(395,606,551,10)
        self.rect(bar,(48,74,61),4)
        self.rect((bar.x,bar.y,round(bar.w*(index+1)/len(track.cells)),bar.h),LIME,4)
        self.buttons.append((bar.inflate(0,13),lambda:self.seek_viewer(bar)))

    def seek_viewer(self,bar):
        track=self.track
        ratio=max(0.,min(.999,(pg.mouse.get_pos()[0]-bar.x)/bar.w))
        self.time=track.start(int(ratio*len(track.cells)))
        self.playing=False

    def next_view(self):
        v=self
        if not v.name:
            return
        v.view=(v.view+1)%len(v.views)

    def focus_search(self):
        self.searching=True
        pg.key.start_text_input()

