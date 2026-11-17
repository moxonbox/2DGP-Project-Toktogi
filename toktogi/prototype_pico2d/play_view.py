from PIL import Image, ImageDraw, ImageFont, ImageChops
from pathlib import Path
from geometry import Rect,bounds,circle_bounds,crop_box
"""Playfield renderer. Physics supplies world positions; the renderer owns lighting."""
SCREEN = (1280, 744)
FIELD = Rect(0, 0, 960, 560)
FIELD.center = (SCREEN[0] // 2, SCREEN[1] // 2)
PLAY_CLEAR = (99, 108, 112)
TINT = (240, 246, 223)
LIME = (212, 238, 163)

def platforms(level):
    scenery = Image.new('RGBA', FIELD.size)
    for p in level:
        leaf = p.kind in ('elastic', 'goal')
        base = (97, 125, 62) if leaf else (95, 75, 51)
        shadow = (49, 73, 46) if leaf else (54, 48, 37)
        edge = (166, 193, 104) if leaf else (132, 138, 84)
        x0, x1, y = (p.x0, p.x1, p.y)
        ImageDraw.Draw(scenery).polygon([(x0, y + 5), (x1, y + 4), (x1 - 8, p.bottom), (x0 + 19, p.bottom), (x0 + 7, y + 16)], fill=shadow)
        ImageDraw.Draw(scenery).polygon([(x0 + 6, y - 14), (x1 - 6, y - 14), (x1, y + 6), (x1 - 8, y + 11), (x0 + 7, y + 11), (x0, y + 5)], fill=base)
        ImageDraw.Draw(scenery).line(((x0 + 6, y - 14), (x1 - 6, y - 14)), fill=edge, width=2)
    return scenery

class PlayView:

    def __init__(self, assets, course):
        self.assets = assets
        self.terrain = platforms(course.platforms)
        self.goal = (course.goal_span[1] - 33, next((p.y for p in course.platforms if p.kind == 'goal')))

    def light_at(self, x, y):
        drift = 2 * round(24 * max(0.0, min(1.0, x / FIELD.width))) - 24
        return (FIELD.x + round(x) - 45 + drift, FIELD.y + round(y) - 87)

    def draw(self, screen, g):
        course = g.course
        screen.paste(PLAY_CLEAR, (0, 0, *screen.size))
        x, y = FIELD.topleft
        ready = g.ready_work()
        light = self.light_at(g.x, g.y)
        screen.alpha_composite(self.terrain, FIELD.topleft)
        if g.offer and g.support and (g.prep is None):
            p = g.support
            ImageDraw.Draw(screen).line(((x + p.x0 + 6, y + p.y - 14), (x + p.x1 - 6, y + p.y - 14)), fill=LIME, width=2)
        floor = min((p.y for p in course.platforms if p.x0 <= g.x <= p.x1 and p.y >= g.y - 0.1), default=None)
        if floor is not None:
            lift = max(0, floor - g.y)
            shadow = Image.new('RGBA', (74, 18))
            alpha = max(0, 116 - round(lift * 1.6))
            ImageDraw.Draw(shadow).ellipse(bounds((4, 3, 60, 7)), fill=(10, 16, 14, alpha))
            shift = int((x + g.x - light[0]) * 0.035 * min(1, lift / 30))
            screen.alpha_composite(shadow, tuple(map(round, (x + round(g.x) - 33 + shift, y + floor - 4))))
        for i in range(g.food):
            px = x + course.food_touch[0] + i * 5 - 7
            py = y + course.food_touch[1] + 3
            ImageDraw.Draw(screen).line(((px + 3, py), (px + 3, y + course.food[1])), fill=(118, 141, 83), width=1)
            ImageDraw.Draw(screen).polygon([(px, py - 2), (px + 2, py - 7), (px + 6, py - 3), (px + 3, py)], fill=LIME if 'food' in ready else (214, 190, 123))
        for point, active in ((course.beacon, g.beacon), (self.goal, g.beacon)):
            px, py = (x + point[0], y + point[1])
            ImageDraw.Draw(screen).line(((px, py), (px, py - 24)), fill=(113, 147, 103), width=3)
            ImageDraw.Draw(screen).polygon([(px, py - 33), (px + 8, py - 24), (px, py - 15), (px - 8, py - 24)], fill=(212, 238, 163) if active else (145, 149, 124))
            if point == course.beacon:
                ImageDraw.Draw(screen).ellipse(bounds((x + course.beacon_touch[0] - 4, y + course.beacon_touch[1] - 2, 9, 4)), fill=LIME if active or 'beacon' in ready else (178, 164, 117))
            if point != course.beacon and g.run == 'Cleared':
                ImageDraw.Draw(screen).polygon([(px, py - 33), (px + 8, py - 24), (px, py - 15), (px - 8, py - 24)], fill=TINT)
        if g.checkpoint:
            px, py = (x + course.checkpoint[0], y + course.checkpoint[1])
            ImageDraw.Draw(screen).line(((px, py), (px, py - 18)), fill=(184, 214, 151), width=2)
            ImageDraw.Draw(screen).polygon([(px, py - 18), (px + 13, py - 15), (px, py - 9)], fill=LIME)
        if g.shell:
            px, py = (x + course.shell[0], y + course.shell[1])
            ImageDraw.Draw(screen).polygon([(px - 16, py), (px - 12, py - 10), (px - 6, py - 7), (px, py - 15), (px + 6, py - 7), (px + 12, py - 10), (px + 16, py)], fill=(196, 126, 94))
        if not g.collected:
            px, py = (x + course.collect_touch[0], y + course.collect_touch[1])
            ImageDraw.Draw(screen).ellipse(bounds((px - 4, py - 3, 9, 6)), fill=LIME if 'collect' in ready else (220, 188, 115))
            ImageDraw.Draw(screen).line(((px - 2, py), (px + 2, py - 2)), fill=(102, 124, 69), width=1)
        key = g.visual()
        pivot_x, pivot_y = self.assets.pivot
        origin = (x + round(g.x) - pivot_x, y + round(g.y) - pivot_y)
        image = self.assets.render(key, 'lit', origin, light, power=0.82, ambient=0.34)
        if g.time < g.reject_until:
            image = image.copy()
            image = ImageChops.add(image, Image.new('RGBA', image.size, (30, 6, 0, 0)))
        screen.alpha_composite(image, tuple(map(round, origin)))
