"""Static course data in logical world pixels."""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class Platform:
    x0: int
    x1: int
    y: int
    bottom: int
    kind: str = 'normal'


LEVEL = (
    Platform(35,201,476,500),
    Platform(243,407,404,424),
    Platform(398,603,331,350,'elastic'),
    Platform(607,858,209,228),
    Platform(817,950,125,144,'goal'),
    Platform(354,606,515,532),
)
BEACON = (339,404)
FOOD = (130,476)
SHELL = (723,209)
CHECKPOINT = (486,331)
COLLECT = (545,331)
FOOD_TOUCH = (FOOD[0],FOOD[1]-15)
BEACON_TOUCH = (BEACON[0],BEACON[1]+7)
COLLECT_TOUCH = (COLLECT[0],COLLECT[1]+9)

@dataclass(frozen=True)
class Course:
    platforms: tuple[Platform, ...] = LEVEL
    spawn_x: float = 120.
    checkpoint_platform: int = 2
    checkpoint: tuple[int, int] = CHECKPOINT
    food: tuple[int, int] = FOOD
    beacon: tuple[int, int] = BEACON
    collect: tuple[int, int] = COLLECT
    shell: tuple[int, int] = SHELL
    goal_span: tuple[int, int] = (839, 940)
    fail_bounds: tuple[int, int, int] = (-68, 1028, 585)

    def __post_init__(self):
        if not self.platforms or any(not all(map(isfinite,(p.x0,p.x1,p.y,p.bottom))) or
                                     p.x0>=p.x1 or p.y>=p.bottom for p in self.platforms):
            raise ValueError('Course needs finite, nonempty platforms.')
        start=self.platforms[0]
        if not start.x0<=self.spawn_x<=start.x1:
            raise ValueError('Course spawn_x must lie on the first platform.')
        if not isinstance(self.checkpoint_platform,int) or not 0<=self.checkpoint_platform<len(self.platforms):
            raise ValueError('Course checkpoint_platform is out of range.')
        checkpoint=self.platforms[self.checkpoint_platform]
        x,y=self.checkpoint
        if not checkpoint.x0<=x<=checkpoint.x1 or y!=checkpoint.y:
            raise ValueError('Course checkpoint must lie on its support platform.')
        goals=[p for p in self.platforms if p.kind=='goal']
        lo,hi=self.goal_span
        if len(goals)!=1 or not goals[0].x0<=lo<hi<=goals[0].x1:
            raise ValueError('Course needs one goal platform containing goal_span.')
        for point in (self.food,self.beacon,self.collect,self.shell):
            if len(point)!=2 or not all(map(isfinite,point)):
                raise ValueError('Course target coordinates must be finite (x, y) pairs.')
        left,right,bottom=self.fail_bounds
        if (not all(map(isfinite,self.fail_bounds)) or
                any(not left<=sx<=right or sy>bottom for sx,sy in
                    ((self.spawn_x,start.y),self.checkpoint,(lo,goals[0].y),(hi,goals[0].y)))):
            raise ValueError('Course failure bounds must contain spawn, checkpoint and goal.')

    @property
    def food_touch(self):
        return self.food[0], self.food[1]-15

    @property
    def beacon_touch(self):
        return self.beacon[0], self.beacon[1]+7

    @property
    def collect_touch(self):
        return self.collect[0], self.collect[1]+9


COURSE = Course()
