"""Stable objects, per-object progress and seamless level context in logical pixels."""
from dataclasses import dataclass, replace
from math import isfinite

from course import COURSE, Platform


@dataclass(frozen=True)
class Entity:
    key: tuple[str, str, str]
    kind: str
    point: tuple[float, float]
    level_id: str

    @property
    def touch(self):
        return self.point[0], self.point[1] + {'food': -15, 'beacon': 7, 'collect': 9, 'shell': 0}[self.kind]


@dataclass(frozen=True)
class Level:
    level_id: str
    stage_id: str
    bounds: tuple[float, float, float, float]


@dataclass(frozen=True)
class Portal:
    portal_id: str
    left: str
    right: str
    x: float
    y0: float
    y1: float
    priority: int = 0


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    level_id: str
    platform: Platform
    point: tuple[float, float]
    required_beacons: tuple


class World:
    def __init__(self, course=COURSE, *, revision='legacy-r4', levels=None, entities=None,
                 portals=(), checkpoints=None, spawn_platform=None, spawn_level=None):
        self.course = course
        self.revision = revision
        self.legacy = levels is None
        left, right, bottom = course.fail_bounds
        self.levels = tuple((Level('legacy', 'stage_01', (left, -400, right, bottom)),) if levels is None else levels)
        if not self.levels:
            raise ValueError('World needs at least one level.')
        self.spawn_level = spawn_level or self.levels[0].level_id
        self.level_id = self.spawn_level
        self.spawn_platform = course.platforms[0] if spawn_platform is None else spawn_platform
        self.entities = tuple(self._entities(course, self.spawn_level) if entities is None else entities)
        self.portals = tuple(portals)
        beacon = next((e.key for e in self.entities if e.kind == 'beacon'), None)
        if beacon is None:
            raise ValueError('World needs a beacon for its goal condition.')
        default = Checkpoint('checkpoint_01', self.spawn_level, course.platforms[course.checkpoint_platform], course.checkpoint, (beacon,))
        self.checkpoints = tuple((default,) if checkpoints is None else checkpoints)
        if not self.checkpoints:
            raise ValueError('World needs a restart checkpoint.')
        self.validate()
        self.portals = tuple(sorted(self.portals, key=lambda p: (p.priority, p.portal_id)))
        self.platform_ids = self._platform_keys()
        goal = next(p for p in course.platforms if p.kind == 'goal')
        self.final_level_id = self.platform_ids[id(goal)][1]
        self.final_stage_id = next(l.stage_id for l in self.levels if l.level_id == self.final_level_id)
        self.camera_bounds = (left, min(l.bounds[1] for l in self.levels), right, bottom)
        self.run_epoch = 0
        self.checkpoint_id = None
        self.checkpoint_stages = set()
        self.completed_stages = set()
        self.events = []
        self.crossing_sequence = 0
        self._initial_states()

    def _entities(self, course, level_id):
        return tuple(Entity((self.revision, level_id, kind), kind, getattr(course, kind), level_id)
                     for kind in ('food', 'beacon', 'collect', 'shell'))

    def _platform_keys(self):
        result = {}
        for i, platform in enumerate(self.course.platforms):
            x = (platform.x0 + platform.x1) / 2
            owner = next((l.level_id for l in self.levels if l.bounds[0] <= x <= l.bounds[2]
                          and l.bounds[1] <= platform.y <= l.bounds[3]), self.spawn_level)
            result[id(platform)] = (self.revision, owner, f'platform_{i:02d}')
        return result

    @property
    def stage_id(self):
        return next(l.stage_id for l in self.levels if l.level_id == self.level_id)

    def validate(self):
        ids = [l.level_id for l in self.levels]
        if not self.revision or len(ids) != len(set(ids)) or self.spawn_level not in ids:
            raise ValueError('World needs a revision, unique levels and a valid spawn level.')
        for level in self.levels:
            if not level.level_id or not level.stage_id or len(level.bounds) != 4 or not all(map(isfinite, level.bounds)):
                raise ValueError('Invalid level identity or bounds.')
            x0, y0, x1, y1 = level.bounds
            if x0 >= x1 or y0 >= y1:
                raise ValueError('Level bounds must be nonempty.')
        if not any(p is self.spawn_platform for p in self.course.platforms) or not self.spawn_platform.x0 <= self.course.spawn_x <= self.spawn_platform.x1:
            raise ValueError('Spawn must reference its stable support.')
        keys = [e.key for e in self.entities]
        if any(not isinstance(k, tuple) or len(k) != 3 or not all(isinstance(v, str) and v for v in k) for k in keys):
            raise ValueError('Entity keys must be (revision, level_id, local_id).')
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate entity key.')
        for entity in self.entities:
            if (entity.kind not in ('food', 'beacon', 'collect', 'shell') or entity.level_id not in ids
                    or entity.key[:2] != (self.revision, entity.level_id) or len(entity.point) != 2
                    or not all(map(isfinite, entity.point))):
                raise ValueError('Invalid world entity.')
        if len({p.portal_id for p in self.portals}) != len(self.portals):
            raise ValueError('Duplicate portal ID.')
        reached = {self.spawn_level}
        for portal in self.portals:
            if (not portal.portal_id or portal.left not in ids or portal.right not in ids
                    or portal.left == portal.right or type(portal.priority) is not int
                    or not all(map(isfinite, (portal.x, portal.y0, portal.y1))) or portal.y0 >= portal.y1):
                raise ValueError('Invalid portal reference or geometry.')
            for level in self.levels:
                if level.level_id in (portal.left, portal.right):
                    x0, y0, x1, y1 = level.bounds
                    if not x0 <= portal.x <= x1 or max(y0, portal.y0) > min(y1, portal.y1):
                        raise ValueError('Portal does not intersect both levels.')
        for _ in ids:
            for portal in self.portals:
                if portal.left in reached or portal.right in reached:
                    reached.update((portal.left, portal.right))
        if reached != set(ids):
            raise ValueError('World contains a disconnected level.')
        if len({c.checkpoint_id for c in self.checkpoints}) != len(self.checkpoints):
            raise ValueError('Duplicate checkpoint ID.')
        for checkpoint in self.checkpoints:
            if (not checkpoint.checkpoint_id or checkpoint.level_id not in ids
                    or not any(p is checkpoint.platform for p in self.course.platforms)
                    or len(checkpoint.point) != 2 or not all(map(isfinite, checkpoint.point))):
                raise ValueError('Invalid checkpoint identity or support.')
            x, y = checkpoint.point
            if not checkpoint.platform.x0 <= x <= checkpoint.platform.x1 or y != checkpoint.platform.y:
                raise ValueError('Checkpoint must lie on its support.')
            if any(key not in keys or self.entity(key).kind != 'beacon' for key in checkpoint.required_beacons):
                raise ValueError('Checkpoint references an unknown prerequisite.')
        geometry = [(p.x0, p.x1, p.y, p.bottom) for p in self.course.platforms]
        if len(geometry) != len(set(geometry)):
            raise ValueError('Duplicate world platform geometry.')

    def rebind_legacy(self, course):
        """Preserve old Course injection tests without replacing live object state."""
        if not self.legacy:
            raise ValueError('Replace the whole World to change a seamless layout.')
        self.course = course
        self.spawn_platform = course.platforms[0]
        self.entities = self._entities(course, self.spawn_level)
        self.checkpoints = (Checkpoint('checkpoint_01', self.spawn_level, course.platforms[course.checkpoint_platform],
                                       course.checkpoint, (self.entity('beacon').key,)),)
        self.platform_ids = self._platform_keys()
        self.camera_bounds = (course.fail_bounds[0], min(l.bounds[1] for l in self.levels), course.fail_bounds[1], course.fail_bounds[2])

    def entity(self, key):
        found = next((e for e in self.entities if e.key == key or isinstance(key, str) and e.kind == key), None)
        if found is None:
            raise ValueError(f'Unknown world entity: {key}')
        return found

    def value(self, key):
        return self.states[self.entity(key).key]

    def set_value(self, key, value):
        self.states[self.entity(key).key] = value

    def targets(self, kind):
        return tuple(e for e in self.entities if e.kind == kind)

    def _initial_states(self):
        self.states = {e.key: 4 if e.kind == 'food' else e.kind == 'shell' for e in self.entities}

    def stage_entry(self, level_id):
        level = next((level for level in self.levels if level.level_id == level_id),None)
        if level is None:
            raise ValueError(f'Unknown stage level: {level_id}')
        if level_id == self.spawn_level:
            return self.spawn_platform, (self.course.spawn_x,float(self.spawn_platform.y))
        platform = next((platform for platform in self.course.platforms
                         if self.platform_ids[id(platform)][1] == level_id),None)
        if platform is None:
            raise ValueError(f'Stage has no starting support: {level_id}')
        x = min(platform.x0+80.,(platform.x0+platform.x1)/2)
        if any(abs(x-e.point[0])<19 and abs(platform.y-e.point[1])<10 for e in self.targets('shell')):
            raise ValueError('Stage entry must clear enemy contact.')
        return platform, (x,float(platform.y))

    def reset(self, checkpoint=False, *, level_id=None):
        entry = self.stage_entry(level_id) if level_id is not None else None
        selected = None
        if checkpoint:
            selected = next((c for c in self.checkpoints if c.checkpoint_id == self.checkpoint_id), self.checkpoints[0])
        self.run_epoch += 1
        self._initial_states()
        self.events.clear()
        self.crossing_sequence = 0
        self.completed_stages = self.checkpoint_stages.copy() if selected else set()
        if selected:
            for key in selected.required_beacons:
                self.states[key] = True
            self.level_id = selected.level_id
            self.checkpoint_id = selected.checkpoint_id
            return selected.platform, selected.point
        self.checkpoint_id = None
        self.checkpoint_stages.clear()
        if entry is not None:
            preceding = {level.level_id for level in self.levels[:next(
                i for i,level in enumerate(self.levels) if level.level_id == level_id)]}
            self.completed_stages = {level.stage_id for level in self.levels if level.level_id in preceding}
            for entity in self.targets('beacon'):
                if entity.level_id in preceding:
                    self.states[entity.key] = True
            self.level_id = level_id
            return entry
        self.level_id = self.spawn_level
        return self.spawn_platform, (self.course.spawn_x, float(self.spawn_platform.y))

    def landed(self, platform):
        for checkpoint in self.checkpoints:
            if checkpoint.platform is platform and all(self.states[k] for k in checkpoint.required_beacons):
                self.checkpoint_id = checkpoint.checkpoint_id
                self.checkpoint_stages = self.completed_stages.copy()
                return True
        return False

    def advance(self, previous, current):
        if len(previous) != 2 or len(current) != 2 or not all(map(isfinite, (*previous, *current))):
            raise ValueError('World traversal needs finite previous/current positions.')
        x0, y0 = previous
        x1, y1 = current
        if x0 == x1:
            return
        for portal in self.portals:
            right = self.level_id == portal.left and x0 <= portal.x <= x1 and x0 < x1
            left = self.level_id == portal.right and x1 <= portal.x <= x0 and x1 < x0
            if not (right or left):
                continue
            y = y0 + (y1-y0)*(portal.x-x0)/(x1-x0)
            if not portal.y0 <= y <= portal.y1:
                continue
            old = self.level_id
            beacons = [e for e in self.entities if e.level_id == old and e.kind == 'beacon']
            if self.stage_id != self.final_stage_id and beacons and all(self.states[e.key] for e in beacons):
                self.completed_stages.add(self.stage_id)
            self.level_id = portal.right if right else portal.left
            self.crossing_sequence += 1
            self.events.append((self.run_epoch, portal.portal_id, self.crossing_sequence, old, self.level_id))
            break

    def goal_ready(self):
        return all(self.states[e.key] for e in self.entities if e.kind == 'beacon')

    @classmethod
    def seamless(cls):
        # Both levels share one bridge collider; the old goal is no longer final.
        platforms = (*COURSE.platforms[:4], Platform(817, 1101, 125, 144), COURSE.platforms[5],
                     *(Platform(p.x0+900, p.x1+900, p.y-351, p.bottom-351, p.kind) for p in COURSE.platforms[1:]))
        course = replace(COURSE, platforms=platforms, goal_span=(1739, 1840), fail_bounds=(-68, 1928, 585))
        revision = 'seamless-r1'
        levels = (Level('pond_duckweed', 'stage_01', (-68, -400, 1101, 585)),
                  Level('lotus_leaf', 'stage_02', (817, -400, 1928, 585)))
        entities = tuple(Entity((revision, level, kind), kind,
                               (getattr(COURSE, kind)[0]+dx, getattr(COURSE, kind)[1]+dy), level)
                         for level, dx, dy in (('pond_duckweed', 0, 0), ('lotus_leaf', 900, -351))
                         for kind in ('food', 'beacon', 'collect', 'shell'))
        first = (revision, 'pond_duckweed', 'beacon')
        second = (revision, 'lotus_leaf', 'beacon')
        checkpoints = (Checkpoint('pond_checkpoint', 'pond_duckweed', platforms[2], COURSE.checkpoint, (first,)),
                       Checkpoint('lotus_checkpoint', 'lotus_leaf', platforms[7], (1386, -20), (first, second)))
        return cls(course, revision=revision, levels=levels, entities=entities,
                   portals=(Portal('pond_lotus', 'pond_duckweed', 'lotus_leaf', 1000, -400, 585),),
                   checkpoints=checkpoints, spawn_platform=platforms[0], spawn_level='pond_duckweed')
