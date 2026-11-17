"""A three-part habitat course using the existing action and checkpoint rules."""
from course import Course, Platform
from world import World, Level, Entity, Portal, Checkpoint

REVISION = 'habitat-r1'
ZONES = (
    ('shore', '젖은 숲바닥', '이끼를 먹고 첫 등불을 켜세요. Q · Z 회전, 왼쪽을 향해 E 유지로 손질을 연습하세요.'),
    ('pond', '수면 잎길', '물결 경고 뒤 Space로 회피. 착지 직전 Space를 눌러 탄성 도약을 이어가세요.'),
    ('reeds', '갈대숲 귀환', '가시 장애물은 E/X로 공격. 세 등불을 켠 뒤 마지막 깃발에서 멈추세요.'),
)
# Art is bound to each support's surface anchor, with uniform nearest scaling.
SURFACES = ('A04', 'A05', 'A04', 'A01', 'A01', 'A01', 'A04', 'A05', 'A01', 'A04')
LIGHTS = ((720, 225), (1660, 210), (2840, 150))


def habitat_world():
    p = tuple(Platform(*values) for values in (
        (25, 355, 380, 410), (410, 630, 340, 390), (685, 990, 380, 410),
        (1040, 1240, 360, 378, 'elastic'), (1290, 1500, 340, 358),
        (1550, 1760, 360, 378, 'elastic'), (1810, 2110, 350, 380),
        (2165, 2380, 310, 360), (2435, 2650, 280, 298, 'elastic'),
        (2705, 3050, 300, 330, 'goal')))
    course = Course(platforms=p, spawn_x=125, checkpoint_platform=2, checkpoint=(835,380),
                    food=(190,380), beacon=(810,380), collect=(535,340), shell=(2285,310),
                    goal_span=(2890,3020), fail_bounds=(0,3120,560))
    levels = (Level('shore','stage_01',(0,0,1010,560)),
              Level('pond','stage_02',(980,0,2140,560)),
              Level('reeds','stage_03',(2100,0,3120,560)))
    items = (('shore','food',(190,380)), ('shore','beacon',(810,380)), ('shore','collect',(535,340)),
             ('pond','food',(1400,340)), ('pond','beacon',(1960,350)), ('pond','collect',(1660,360)),
             ('reeds','food',(2790,300)), ('reeds','beacon',(2850,300)), ('reeds','collect',(2540,280)),
             ('reeds','shell',(2285,310)))
    entities = tuple(Entity((REVISION,zone,kind),kind,point,zone) for zone,kind,point in items)
    beacons = tuple(e.key for e in entities if e.kind=='beacon')
    return World(course, revision=REVISION, levels=levels, entities=entities,
                 portals=(Portal('shore_pond','shore','pond',1000,0,560),
                          Portal('pond_reeds','pond','reeds',2120,0,560)),
                 checkpoints=(Checkpoint('shore_rest','shore',p[2],(875,380),beacons[:1]),
                              Checkpoint('pond_rest','pond',p[6],(2020,350),beacons[:2])),
                 spawn_platform=p[0],spawn_level='shore')
