"""Animated F1 stage drawer using the current world's levels and prepared stage art."""
from PIL import Image, ImageDraw, ImageOps
from geometry import Rect, bounds
from stage_world import ZONES

HEIGHT = 320
DURATION = .18
NAMES = {key: title for key, title, _ in ZONES}


class StageMenu:
    def __init__(self, world):
        self.world = world
        self.opened = False
        self.progress = 0.
        self.selected = 0
        self.background = None
        self.previews = []

    @property
    def visible(self):
        return self.opened or self.progress > 0.

    def open(self, background, art=None):
        self.opened = True
        self.selected = next(i for i, level in enumerate(self.world.levels)
                             if level.level_id == self.world.level_id)
        self._release_images()
        self.background = background.copy()
        width = (background.width-48-12*(len(self.world.levels)-1))//len(self.world.levels)
        for level in self.world.levels:
            if art is None:
                self.previews.append(None)
                continue
            source = art.crop(tuple(round(value) for value in level.bounds))
            self.previews.append(ImageOps.fit(source, (width-24,112),
                                             method=Image.Resampling.NEAREST, centering=(.5,.75)))
            source.close()

    def step(self, dt):
        change = dt / DURATION
        self.progress = min(1., self.progress+change) if self.opened else max(0., self.progress-change)
        if not self.visible:
            self._release_images()

    def hide(self):
        self.opened = False
        self.progress = 0.
        self._release_images()

    def _release_images(self):
        if self.background is not None:
            self.background.close()
            self.background = None
        for preview in self.previews:
            if preview is not None:
                preview.close()
        self.previews.clear()

    def move(self, direction):
        self.selected = max(0,min(len(self.world.levels)-1,self.selected+direction))

    def draw(self, screen, viewer, start, dismiss):
        screen.paste(self.background)
        shade = Image.new('RGBA',screen.size,(0,0,0,round(70*self.progress)))
        screen.alpha_composite(shade)
        shade.close()
        eased = 1-(1-self.progress)**3
        top = screen.height-round(HEIGHT*eased)
        panel = Image.new('RGBA',(screen.width,HEIGHT),(23,26,31,255))
        draw = ImageDraw.Draw(panel)
        draw.line((0,0,screen.width,0),fill=(81,91,104),width=2)

        def text(label,x,y,size=16,color=(226,232,238)):
            panel.alpha_composite(viewer.text_surface(label,size,color),(x,y))

        def button(label,rect,callback):
            hover = rect.collidepoint((viewer.pointer[0],viewer.pointer[1]-top))
            draw.rounded_rectangle(bounds(rect),5,fill=(63,96,129) if hover else (44,65,87))
            text(label,rect.x+14,rect.y+8,14)
            if self.opened and self.progress == 1.:
                viewer.buttons.append((Rect(rect.x,top+rect.y,rect.w,rect.h),callback))

        text('스테이지 선택',24,13,22)
        text('선택한 구간에서 새 도전을 시작합니다. 이전 구간의 등불은 완료 처리됩니다.',24,45,14,(159,172,185))
        button('닫기  M / Esc',Rect(screen.width-158,16,134,36),dismiss)
        count = len(self.world.levels)
        width = (screen.width-48-12*(count-1))//count
        for index, level in enumerate(self.world.levels):
            rect = Rect(24+index*(width+12),78,width,180)
            hover = rect.collidepoint((viewer.pointer[0],viewer.pointer[1]-top))
            active = self.selected == index
            draw.rounded_rectangle(bounds(rect),5,fill=(39,45,55) if hover else (30,34,41),
                                   outline=(108,181,242) if active else (62,71,84),
                                   width=2 if active else 1)
            preview = self.previews[index]
            if preview is not None:
                panel.alpha_composite(preview,(rect.x+12,rect.y+10))
            else:
                text(level.level_id,rect.x+16,rect.y+48,20,(159,172,185))
            text(NAMES.get(level.level_id,level.level_id),rect.x+14,rect.y+128,18)
            current = ' · 현재 구간' if level.level_id == self.world.level_id else ''
            text(level.stage_id+current,rect.x+14,rect.y+153,13,(159,172,185))
            if self.opened and self.progress == 1.:
                viewer.buttons.append((Rect(rect.x,top+rect.y,rect.w,rect.h),
                                       lambda index=index: setattr(self,'selected',index)))
        text('A / D 또는 ← / → 선택    Enter / E 시작',24,283,14,(159,172,185))
        button('선택한 스테이지 시작',Rect(screen.width-226,273,202,36),start)
        screen.alpha_composite(panel,(0,top))
        panel.close()
