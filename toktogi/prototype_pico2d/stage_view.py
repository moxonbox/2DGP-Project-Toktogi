"""Habitat composition, world-space light pools, and contextual action guidance."""
from math import sin
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pond_view import PondView
from play_view import FIELD
from stage_art import StageArt
from stage_world import ZONES, LIGHTS


class StageView(PondView):
    def __init__(self,assets,world,pond,asset_root=None):
        super().__init__(assets,world,pond,asset_root,make_leaves=False)
        self.art=None; self.halo=None
        self.hud_key=None;self.hud_parts=[]
        try:
            self.art=StageArt(world,asset_root)
            font=Path(os.environ.get('TOKTOGI_FONT',str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/malgun.ttf')))
            self.font=ImageFont.truetype(str(font),16)
            self.title_font=ImageFont.truetype(str(font),25)
            self.small_font=ImageFont.truetype(str(font),13)
            self.halo=Image.new('RGBA',(120,120))
            ImageDraw.Draw(self.halo).ellipse((34,34,86,86),fill=(174,223,115,105))
            blurred=self.halo.filter(ImageFilter.GaussianBlur(16));self.halo.close();self.halo=blurred
        except BaseException:
            self.close();raise

    def background(self,game):
        x,y=round(self.camera.x),round(self.camera.y)
        frame=self.art.image.crop((x,y,x+FIELD.w,y+FIELD.h))
        draw=ImageDraw.Draw(frame)
        # Subtle world-anchored water motion; physics and pause use game time.
        for wx in range(0,3120,100):
            px,py=self.camera.point(wx+sin(game.time+wx)*5,415+(wx//100%4)*29)
            draw.line((px,py,px+24,py),fill=(83,143,147,120),width=1)
        for e in self.world.targets('beacon'):
            if self.world.states[e.key]:
                x,y=self.camera.point(e.point[0],e.point[1]-24)
                frame.alpha_composite(self.halo,(x-60,y-60))
        return frame

    def platforms(self,frame,game):
        draw=ImageDraw.Draw(frame)
        phase=round(2*sin(game.time*.8))+2
        for frames in self.art.platform_frames:
            tile,origin=frames[phase]
            x,y=self.camera.point(*origin)
            if x<frame.width and x+tile.width>0:frame.alpha_composite(tile,(x,y))
        for key,(tile,origin) in self.art.food_tiles:
            if self.world.states[key]:frame.alpha_composite(tile,self.camera.point(*origin))
        for p in self.world.course.platforms:
            x,y=self.camera.point(p.x0,p.y);x1,_=self.camera.point(p.x1,p.y)
            if x1<0 or x>FIELD.w:continue
            color=(125,190,111,255) if p.kind=='elastic' else (132,163,135,185)
            draw.line((x+4,y,x1-4,y),fill=color,width=1)
            if p.kind=='elastic':
                for offset in (-8,0,8):
                    mid=(x+x1)//2+offset
                    draw.line((mid-3,y+8,mid,y+5,mid+3,y+8),fill=(180,227,136,255))

    def _fish(self,frame):
        if self.pond.phase!='idle':super()._fish(frame)

    def light(self,game):
        light=min(LIGHTS,key=lambda p:abs(p[0]-game.x))
        # Quantized moving light keeps the existing material cache bounded/useful.
        drift=20*round(2*sin(game.time*.8))
        return self.camera.point(light[0]+drift,light[1]),1.15,.25

    def effects(self,frame,game,origin):
        return self.assets.renderer.composite_bloom(frame,game.visual(),origin,in_place=True)

    def overlay(self,screen,game):
        key=(screen.size,self.world.level_id,tuple(self.world.states.values()),game.bites,
             game.launch_count,self.pond.repels,game.run,self.pond.phase,
             tuple(sorted(game.ready_work())),game.notice if 4<game.time<game.notice_until else None)
        if key!=self.hud_key:
            for image,_ in self.hud_parts:image.close()
            layer=Image.new('RGBA',screen.size)
            self._paint_overlay(layer,game)
            boxes=[(0,0,screen.width,FIELD.y),(0,FIELD.bottom,screen.width,screen.height),
                   (0,FIELD.y,FIELD.x,FIELD.bottom),(FIELD.right,FIELD.y,screen.width,FIELD.bottom)]
            if game.run in ('Paused','Failed','Cleared'):
                boxes.append((FIELD.x+225,FIELD.y+160,FIELD.right-224,FIELD.y+266))
            self.hud_parts=[(layer.crop(box),box[:2]) for box in boxes]
            layer.close();self.hud_key=key
        for image,at in self.hud_parts:
            if at==(FIELD.x+225,FIELD.y+160):
                mask=image.getchannel('A').point([0]+[255]*255)
                screen.paste(image,at,mask);mask.close()
            else:screen.paste(image,at)

    def _paint_overlay(self,screen,game):
        draw=ImageDraw.Draw(screen)
        draw.rectangle((0,FIELD.y,FIELD.x-1,FIELD.bottom),fill=(12,23,27,255))
        draw.rectangle((FIELD.right,FIELD.y,screen.width,FIELD.bottom),fill=(12,23,27,255))
        draw.rectangle((0,0,screen.width,FIELD.y-1),fill=(12,23,27,255))
        draw.rectangle((0,FIELD.bottom,screen.width,screen.height),fill=(12,23,27,255))
        index=next(i for i,z in enumerate(ZONES) if z[0]==self.world.level_id)
        draw.text((FIELD.x,14),'TOKTOGI  /  이슬의 길',font=self.title_font,fill=(225,237,203))
        draw.text((FIELD.x+600,25),f'{index+1:02d}  {ZONES[index][1]}',font=self.font,fill=(177,211,171))
        beacons=self.world.targets('beacon'); seeds=self.world.targets('collect')
        lamps=sum(bool(self.world.states[e.key]) for e in beacons)
        collected=sum(bool(self.world.states[e.key]) for e in seeds)
        draw.text((FIELD.x,51),f'등불 {lamps}/3    씨앗 {collected}/3    섭식 {game.bites}    도약 {game.launch_count}    반격 {self.pond.repels}',font=self.small_font,fill=(157,180,174))
        for i in range(3):
            x=FIELD.x+600+i*100
            draw.line((x,62,x+80,62),fill=(190,225,145) if i<=index else (48,69,66),width=3)
        prompt=ZONES[index][2]
        if game.run=='Paused': prompt='일시정지  ·  P / Esc 계속하기  ·  R 체크포인트 재시작'
        elif game.run=='Failed': prompt='물에 떨어졌습니다. R로 마지막 쉼터에서 다시 시작하세요.'
        elif game.run=='Cleared': prompt='이슬의 길 완료! 세 등불이 숲과 연못을 잇습니다.  R 다시 시작'
        elif self.pond.phase=='warn': prompt='물결 경고!  Space 도약으로 피하거나, 입이 올라올 때 E / F로 반격하세요.'
        elif game.ready_work():
            kinds={self.world.entity(k).kind for k in game.ready_work()}
            prompt='E 유지: 이끼 섭식' if kinds=={'food'} else 'E: 등불 켜기 / 씨앗 수집'
        elif game.time<game.notice_until and game.time>4: prompt=game.notice
        draw.text((FIELD.x,FIELD.bottom+12),prompt,font=self.font,fill=(224,232,201))
        draw.text((FIELD.x,FIELD.bottom+45),'WASD 회전 · A/D 이동 · W/S 조준 · Space 도약 · Ctrl 제동 · Shift 달리기 · E 상호작용 · F 공격 · Q 반전 · Z 회전 · P 일시정지 · F2 모션·재질',font=self.small_font,fill=(152,174,168))
        if game.run in ('Paused','Failed','Cleared'):
            box=(FIELD.x+225,FIELD.y+160,FIELD.right-225,FIELD.y+265)
            draw.rounded_rectangle(box,12,fill=(15,31,35,245),outline=(117,166,126),width=2)
            label={'Paused':'잠시 쉬어가기','Failed':'다시 도약할 시간','Cleared':'세 등불, 하나의 길'}[game.run]
            draw.text((box[0]+30,box[1]+18),label,font=self.title_font,fill=(222,238,198))
            draw.text((box[0]+30,box[1]+62),'P / Esc 계속' if game.run=='Paused' else 'R 체크포인트 재시작',font=self.font,fill=(162,190,176))

    def close(self):
        for image,_ in getattr(self,'hud_parts',[]):image.close()
        self.hud_parts=[]
        if getattr(self,'art',None):self.art.close()
        if getattr(self,'halo',None):self.halo.close();self.halo=None
        super().close()
