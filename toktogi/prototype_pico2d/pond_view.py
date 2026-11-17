"""Pond test view: procedural leaves are provisional, not production lotus assets."""
import math
from PIL import Image, ImageDraw, ImageChops
from camera import Camera
from fish_assets import FishAssets
from play_view import FIELD, PLAY_CLEAR


class PondView:
    def __init__(self, assets, world, pond, asset_root=None, *, make_leaves=True):
        self.assets, self.world, self.pond = assets, world, pond
        self.camera = Camera(world)
        self.environment = None
        self.fish = FishAssets(asset_root)
        self.leaves = {}
        self.closed = False
        for platform in (world.course.platforms if make_leaves else ()):
            width = max(8, round(platform.x1 - platform.x0))
            leaf = Image.new('RGBA', (width + 2, 44))
            draw = ImageDraw.Draw(leaf)
            draw.ellipse((0, 8, width, 42), fill=(35, 72, 51, 210))
            draw.ellipse((0, 3, width, 35), fill=(78, 124, 66, 255), outline=(145, 176, 93, 255), width=2)
            center = (width // 2, 19)
            for angle in (0, 35, 70, 110, 145, 180, 220, 270, 320):
                radians = math.radians(angle)
                end = (center[0] + int((width / 2 - 5) * math.cos(radians)),
                       center[1] + int(12 * math.sin(radians)))
                draw.line((center, end), fill=(117, 155, 82, 255), width=1)
            draw.polygon((center, (width // 2 - 8, 0), (width // 2 + 8, 0)), fill=(0, 0, 0, 0))
            self.leaves[id(platform)] = leaf

    def step(self, game, dt):
        self.camera.step(game, dt)

    def _fish(self, frame):
        image, anchor = self.fish.frame(self.pond.action, self.pond.u)
        x, y = self.camera.point(*self.pond.mouth)
        origin = round(x - anchor[0]), round(y - anchor[1])
        fish = image.copy()
        alpha = fish.getchannel('A')
        water = self.camera.point(0, self.pond.water_y)[1]
        split = max(0, min(fish.height, water - origin[1]))
        if split < fish.height:
            submerged = alpha.crop((0, split, fish.width, fish.height)).point(lambda value: round(value * .35))
            alpha.paste(submerged, (0, split))
            submerged.close()
        fish.putalpha(alpha)
        frame.alpha_composite(fish, origin)
        alpha.close()
        fish.close()

    def draw(self, screen, game):
        if self.closed:
            raise RuntimeError('PondView is closed.')
        screen.paste(PLAY_CLEAR, (0, 0, *screen.size))
        frame = self.background(game)
        self._fish(frame)
        self.platforms(frame,game)
        draw = ImageDraw.Draw(frame)
        if self.pond.phase == 'warn':
            x, y = self.camera.point(self.pond.target_x, self.pond.water_y)
            radius = 13 + round(6 * math.sin(self.pond.time * 12))
            draw.ellipse((x-radius, y-5, x+radius, y+5), outline=(226, 213, 133, 255), width=2)
            draw.ellipse((x-radius-10, y-8, x+radius+10, y+8), outline=(143, 183, 171, 255), width=1)
        ready = game.ready_work()
        for entity in self.world.entities:
            value = self.world.states[entity.key]
            x, y = self.camera.point(*entity.point)
            tx, ty = self.camera.point(*entity.touch)
            color = (212, 238, 163, 255) if entity.key in ready else (214, 190, 123, 255)
            if entity.kind == 'food':
                for index in range(value):
                    px = tx + index * 5 - 7
                    draw.line((px + 3, ty + 3, px + 3, y), fill=(118, 141, 83, 255))
                    draw.ellipse((px, ty-5, px+5, ty+2), fill=color)
            elif entity.kind == 'beacon':
                draw.line((x, y, x, y-24), fill=(113, 147, 103, 255), width=3)
                draw.polygon(((x, y-33), (x+8, y-24), (x, y-15), (x-8, y-24)),
                             fill=(212, 238, 163, 255) if value else (145, 149, 124, 255))
            elif entity.kind == 'collect' and not value:
                draw.ellipse((tx-4, ty-3, tx+4, ty+2), fill=color)
            elif entity.kind == 'shell' and value:
                draw.polygon(((x-16, y), (x-10, y-10), (x-4, y-5), (x, y-15),
                              (x+5, y-5), (x+12, y-10), (x+16, y)), fill=(196, 126, 94, 255))
        goal = next(platform for platform in self.world.course.platforms if platform.kind == 'goal')
        x, y = self.camera.point(self.world.course.goal_span[1]-30, goal.y)
        draw.line((x, y, x, y-27), fill=(184, 214, 151, 255), width=2)
        draw.polygon(((x, y-27), (x+14, y-22), (x, y-17)),
                     fill=(240, 246, 223, 255) if self.world.goal_ready() else (140, 158, 116, 255))
        x, y = self.camera.point(game.x, game.y)
        origin = x-self.assets.pivot[0], y-self.assets.pivot[1]
        shadow = Image.new('RGBA', (64, 12))
        ImageDraw.Draw(shadow).ellipse((2, 2, 61, 9), fill=(10, 24, 22, 90))
        if game.support:
            frame.alpha_composite(shadow, (x-32, y-3))
        shadow.close()
        light,power,ambient=self.light(game)
        sprite = self.assets.render(game.visual(), 'lit', origin, light, power=power, ambient=ambient)
        if game.time < game.reject_until:
            sprite = ImageChops.add(sprite, Image.new('RGBA', sprite.size, (30, 6, 0, 0)))
        frame.alpha_composite(sprite, origin)
        output=self.effects(frame,game,origin)
        if output is not frame:frame.close();frame=output
        # Source-over onto the opaque clear: avoid an RGB copy, then restore opaque alpha.
        alpha=frame.getchannel('A')
        screen.paste(frame,FIELD.topleft,alpha)
        screen.putalpha(255);alpha.close()
        frame.close()
        self.overlay(screen,game)

    def background(self,game):
        frame = Image.new('RGBA', FIELD.size, (*PLAY_CLEAR, 255))
        draw = ImageDraw.Draw(frame)
        water = self.camera.point(0, self.pond.water_y)[1]
        draw.rectangle((0, max(0, water), FIELD.w, FIELD.h), fill=(46, 89, 97, 255))
        if 0 <= water < FIELD.h:
            draw.line((0, water, FIELD.w, water), fill=(117, 159, 158, 255), width=2)
        # World-anchored water marks move with the same camera as actors and leaves.
        for world_x in range(-120, 2100, 120):
            x, y = self.camera.point(world_x, self.pond.water_y + 35 + (world_x // 120 % 3) * 25)
            draw.line((x, y, x + 32, y), fill=(66, 111, 119, 255), width=1)
        return frame

    def platforms(self,frame,game):
        for platform in self.world.course.platforms:
            x, y = self.camera.point(platform.x0, platform.y)
            frame.alpha_composite(self.leaves[id(platform)], (x, y - 9))

    def light(self,game):
        x,y=self.camera.point(game.x,game.y)
        return (x-45,y-87),.82,.34

    def effects(self,frame,game,origin):return frame

    def overlay(self,screen,game):pass

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.fish.close()
        for image in self.leaves.values():
            image.close()
        self.leaves.clear()
