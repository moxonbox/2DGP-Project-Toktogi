"""Temporary storyboard presentation over the prepared habitat course."""
from math import sin, hypot
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from stage_view import StageView
from play_view import FIELD

TEST_STAGE = 'storyboard_test'
INTRO_END = 8.3
IMPACT = 4.2
EYES_OPEN = 6.6


class Story:
    def __init__(self, world):
        self.world = world
        self.active = False
        self.time = 0.
        self.points = tuple((p.x1-35,p.y) for p in world.course.platforms)
        platform = world.course.platforms[1]
        self.start = ((platform.x0+platform.x1)/2,float(platform.y))
        self.pulses = [0.]*len(self.points)
        self.audio_status = ''

    @property
    def intro(self):
        return self.active and self.time < INTRO_END

    def reset(self, game, active):
        self.active = active
        self.time = 0.
        self.pulses = [0.]*len(self.points)
        if active:
            # The second shore platform places the sleeping character near the screen center.
            game.support = self.world.course.platforms[1]
            game.x = (game.support.x0+game.support.x1)/2
            game.y = float(game.support.y)
            if not game.stable_feet(game.assets.tracks['idle','right']):
                raise ValueError('Storyboard start needs a supported idle pose.')

    def step(self, dt):
        self.time += dt
        self.pulses = [max(0.,pulse-dt) for pulse in self.pulses]

    def firefly(self):
        t = self.time
        target = (self.start[0]+23,self.start[1]-26)
        if t < 1.2:
            return None
        if t < IMPACT:
            u = (t-1.2)/(IMPACT-1.2)
            return 1000+(target[0]-1000)*u,target[1]+sin(u*4*3.14159)*25*(1-u)
        if t < 4.9:
            u = (t-IMPACT)/.7
            return target[0]-42*sin(u*1.5708),target[1]-36*sin(u*1.5708)
        if t < EYES_OPEN:
            return target[0]-42+sin(t*5)*4,target[1]-36+sin(t*3)*7
        if t < INTRO_END:
            u = (t-EYES_OPEN)/(INTRO_END-EYES_OPEN)
            return target[0]-42+600*u,target[1]-36+sin(u*9)*13
        return None

    def strength(self, game, index):
        x,y = self.points[index]
        proximity = max(0.,1-hypot(game.x-x,game.y-y)/135)
        return 1+1.8*proximity+2.5*min(1.,self.pulses[index]/.25)

    def interact(self, game):
        if self.intro:
            return False
        index = min(range(len(self.points)),key=lambda i:hypot(game.x-self.points[i][0],game.y-self.points[i][1]))
        if hypot(game.x-self.points[index][0],game.y-self.points[index][1]) > 85:
            return False
        self.pulses[index] = 1.2
        return True


class StoryView(StageView):
    def __init__(self, assets, world, pond, asset_root=None):
        super().__init__(assets,world,pond,asset_root)
        self.story = Story(world)
        self.story_game = None
        self.light_pool = Image.new('L',(256,256))
        ImageDraw.Draw(self.light_pool).ellipse((60,60,196,196),fill=255)
        blurred = self.light_pool.filter(ImageFilter.GaussianBlur(26))
        self.light_pool.close()
        self.light_pool = blurred

    def step(self, game, dt):
        self.story_game = game
        super().step(game,dt)

    def light(self, game):
        story = self.story
        if not story.active:
            return super().light(game)
        fly = story.firefly()
        if story.time < 1.2:
            return self.camera.point(game.x,game.y-30),0.,0.
        if story.intro and fly:
            flash = max(0.,1-abs(story.time-IMPACT)/.35)
            return self.camera.point(*fly),.85+2*flash,0.
        index = min(range(len(story.points)),key=lambda i:hypot(game.x-story.points[i][0],game.y-story.points[i][1]))
        x,y = story.points[index]
        return self.camera.point(x,y-20),.6*story.strength(game,index),.012

    def _eyelids(self, frame, key, origin, light, power):
        if self.story.time >= EYES_OPEN:
            return
        image = self.assets.render(key,'lit',origin,light,power=power,ambient=0.)
        box = self.assets.maps(key)['emissive'].convert('RGB').getbbox()
        if box is None:
            return
        x0,y0,x1,y1 = box
        cx,cy = (x0+x1)//2,(y0+y1)//2
        skin = image.getpixel((max(0,x0-3),cy))
        ox,oy = origin
        draw = ImageDraw.Draw(frame)
        draw.ellipse((ox+x0-2,oy+y0-1,ox+x1+2,oy+y1+1),fill=skin)
        opening = max(0.,min(1.,(self.story.time-4.9)/(EYES_OPEN-4.9)))
        half = round((y1-y0+4)*opening/2)
        if half:
            patch = image.crop((x0-2,cy-half,x1+3,cy+half+1))
            frame.alpha_composite(patch,(ox+x0-2,oy+cy-half))
            patch.close()
        else:
            draw.line((ox+x0,oy+cy,ox+x1,oy+cy),fill=(5,8,8,255))

    def effects(self, frame, key, origin, light, power):
        if not self.story.active:
            return super().effects(frame,key,origin,light,power)
        game = self.story_game
        story = self.story
        self._eyelids(frame,key,origin,light,power)
        visibility = Image.new('L',frame.size,0 if story.time < IMPACT else 8)

        def pool(point, gain):
            x,y = self.camera.point(*point)
            left,top = max(0,x-128),max(0,y-128)
            right,bottom = min(frame.width,x+128),min(frame.height,y+128)
            if left >= right or top >= bottom:
                return
            tile = self.light_pool.crop((left-x+128,top-y+128,right-x+128,bottom-y+128))
            tile = tile.point([min(255,round(value*gain)) for value in range(256)])
            previous = visibility.crop((left,top,right,bottom))
            combined = ImageChops.lighter(previous,tile)
            visibility.paste(combined,(left,top))
            previous.close();tile.close();combined.close()

        fly = story.firefly()
        if fly:
            flash = max(0.,1-abs(story.time-IMPACT)/.35)
            pool(fly,.55+2*flash)
        reveal = max(0.,min(1.,(story.time-4.5)/1.0))
        if reveal:
            for index,point in enumerate(story.points):
                if abs(point[0]-self.camera.x-FIELD.w/2)<FIELD.w/2+128:
                    pool(point,reveal*(.35+.15*story.strength(game,index)))
        rgb = ImageChops.multiply(frame.convert('RGB'),visibility.convert('RGB'))
        rgb.putalpha(frame.getchannel('A'))
        frame.paste(rgb)
        visibility.close();rgb.close()
        draw = ImageDraw.Draw(frame)
        actor_alpha = self.assets.maps(key)['sprite'].getchannel('A')
        if reveal:
            for index,(wx,wy) in enumerate(story.points):
                x,y = self.camera.point(wx,wy)
                if not -24<x<frame.width+24:
                    continue
                gain = story.strength(game,index)
                color = (round(80*reveal),round(min(255,100+38*gain)*reveal),round(min(255,95+38*gain)*reveal),255)
                mushroom = Image.new('RGBA',(32,30))
                cap = ImageDraw.Draw(mushroom)
                cap.rectangle((14,10,18,29),fill=tuple(round(c*reveal) for c in (48,87,72))+(255,))
                cap.ellipse((1,3,31,18),fill=color)
                cap.line((4,17,28,17),fill=(153,255,211,round(255*reveal)),width=2)
                for dx,dy in ((-7,-20),(4,-23),(8,-17)):
                    cap.point((16+dx,29+dy),fill=tuple(round(c*reveal) for c in (198,255,217))+(255,))
                # The mushroom layer stays behind the sprite even when their screenspace bounds overlap.
                covered = actor_alpha.crop((x-16-origin[0],y-29-origin[1],x+16-origin[0],y+1-origin[1]))
                mushroom.putalpha(ImageChops.multiply(mushroom.getchannel('A'),ImageChops.invert(covered)))
                frame.alpha_composite(mushroom,(x-16,y-29))
                covered.close();mushroom.close()
        actor_alpha.close()
        if fly:
            x,y = self.camera.point(*fly)
            glow = Image.new('RGBA',(42,42))
            gd = ImageDraw.Draw(glow)
            gd.ellipse((9,9,33,33),fill=(172,231,87,100))
            blurred = glow.filter(ImageFilter.GaussianBlur(7))
            frame.alpha_composite(blurred,(x-21,y-21))
            draw.ellipse((x-4,y-2,x+4,y+2),fill=(224,255,157,255))
            draw.ellipse((x-6,y-6,x,y-1),fill=(134,176,149,180))
            draw.ellipse((x,y-6,x+6,y-1),fill=(134,176,149,180))
            glow.close();blurred.close()
            flash = max(0.,1-abs(story.time-IMPACT)/.22)
            if flash:
                draw.ellipse((x-12,y-12,x+12,y+12),fill=(255,255,220,round(255*flash)))
        if story.time >= EYES_OPEN:
            self.assets.renderer.composite_bloom(frame,key,origin,light=light,power=power,in_place=True)
        return frame

    def overlay(self, screen, game):
        if not self.story.active:
            return super().overlay(screen,game)
        # Keep the opening frame fully black, including the usual HUD and outer clear color.
        if self.story.time < 1.2:
            screen.paste((0,0,0,255),(0,0,*screen.size))
        else:
            draw = ImageDraw.Draw(screen)
            for box in ((0,0,screen.width,FIELD.y),(0,FIELD.bottom,screen.width,screen.height),
                        (0,FIELD.y,FIELD.x,FIELD.bottom),(FIELD.right,FIELD.y,screen.width,FIELD.bottom)):
                draw.rectangle(box,fill=(0,0,0,255))
            draw.text((FIELD.x,20),'스토리보드 #1 · 임시 테스트',font=self.font,fill=(173,198,180))
            message = '' if self.story.intro else '빛나는 버섯을 따라 이동하세요. 가까이 다가가거나 E / F를 누르면 더 밝아집니다.'
            if game.run == 'Paused':
                message = '일시정지 · P / Esc 계속'
            elif game.run in ('Failed','Cleared'):
                message = 'R 처음부터 다시 보기 · M 기존 스테이지 선택'
            draw.text((FIELD.x,FIELD.bottom+12),message,font=self.font,fill=(199,218,201))
        if self.story.time < 1.2:
            return
        draw = ImageDraw.Draw(screen)
        draw.text((FIELD.x,screen.height-28),'M 스테이지 선택 · R 연출 재시작 · P 일시정지'+self.story.audio_status,
                  font=self.small_font,fill=(126,153,135))

    def close(self):
        if hasattr(self,'light_pool'):
            self.light_pool.close()
        super().close()
