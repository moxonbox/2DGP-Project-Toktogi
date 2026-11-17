"""World data, identity, swept traversal and reset checks without SDL or assets."""
from dataclasses import replace
import json
from pathlib import Path

from course import COURSE
from world import World


def rebuild(world, **changes):
    values = dict(course=world.course, revision=world.revision, levels=world.levels,
                  entities=world.entities, portals=world.portals, checkpoints=world.checkpoints,
                  spawn_platform=world.spawn_platform, spawn_level=world.spawn_level)
    values.update(changes)
    return World(**values)


def verify():
    checks = {}
    legacy = World()
    support, point = legacy.reset()
    assert support is COURSE.platforms[0] and point == (120, 476)
    legacy.set_value('food', 2)
    moved = replace(COURSE, food=(160, 476))
    legacy.rebind_legacy(moved)
    assert legacy.entity('food').point == moved.food and legacy.value('food') == 2
    support, point = legacy.reset(True)
    assert support is COURSE.platforms[2] and point == COURSE.checkpoint
    assert legacy.value('beacon') and legacy.value('food') == 4
    assert legacy.value('shell') and not legacy.value('collect')
    checks['legacy_course_identity_and_rebind'] = True

    world = World.seamless()
    world.reset()
    platforms = world.course.platforms
    assert len(platforms) == len(world.platform_ids) == 11
    assert platforms[4].x0 == 817 and platforms[4].x1 == 1101 and platforms[4].y == 125
    assert platforms[9].kind == 'goal' and platforms[4].kind != 'goal'
    assert len(world.entities) == len(world.states) == 8
    assert (world.final_level_id, world.final_stage_id) == ('lotus_leaf', 'stage_02')
    first, second = (e.key for e in world.targets('beacon'))
    world.states[first] = True
    world.states[world.targets('food')[0].key] = 1
    identity = dict(world.platform_ids)
    epoch = world.run_epoch
    world.advance((990, 125), (1010, 125))
    assert world.level_id == 'lotus_leaf' and world.stage_id == 'stage_02'
    assert world.completed_stages == {'stage_01'} and world.run_epoch == epoch
    assert world.platform_ids == identity and world.value('food') == 1
    world.advance((1010, 125), (1010, 125))
    assert len(world.events) == 1
    world.advance((1010, 125), (990, 125))
    assert world.level_id == 'pond_duckweed' and len(world.events) == 2
    assert world.events[0][:3] == (epoch, 'pond_lotus', 1)
    assert world.events[1][:3] == (epoch, 'pond_lotus', 2)
    world.advance((1000, 125), (1001, 125))
    assert world.level_id == 'lotus_leaf' and len(world.events) == 3
    assert not world.goal_ready()
    world.states[second] = True
    assert world.goal_ready()
    world.advance((1010, 125), (990, 125))
    assert world.completed_stages == {'stage_01'}
    world.advance((990, 125), (1010, 125))
    checks['swept_bidirectional_context_and_state'] = True

    # The interpolated crossing height, not either endpoint, determines admission.
    portal = replace(world.portals[0], y0=100, y1=150)
    narrow = rebuild(world, portals=(portal,))
    narrow.reset()
    narrow.advance((990, 0), (1010, 250))
    assert narrow.level_id == 'lotus_leaf'
    narrow.reset()
    narrow.advance((990, 100), (1010, 300))
    assert narrow.level_id == 'pond_duckweed'
    high = replace(portal, portal_id='high', priority=-1)
    priority = rebuild(world, portals=(portal, high))
    priority.reset()
    priority.advance((990, 125), (1010, 125))
    assert len(priority.events) == 1 and priority.events[0][1] == 'high'
    checks['swept_height_and_portal_priority'] = True

    assert not world.landed(replace(platforms[7]))
    assert world.landed(platforms[7])
    world.states[world.targets('shell')[1].key] = False
    world.states[world.targets('collect')[1].key] = True
    support, point = world.reset(True)
    assert support is platforms[7] and point == (1386, -20)
    assert world.level_id == 'lotus_leaf' and world.run_epoch == epoch + 1
    assert world.completed_stages == {'stage_01'} and not world.events
    assert all(world.states[e.key] == 4 for e in world.targets('food'))
    assert all(world.states[e.key] for e in world.targets('shell'))
    assert not any(world.states[e.key] for e in world.targets('collect'))
    assert world.goal_ready()
    # Explicit checkpoint prerequisites do not restore unrelated beacons.
    special = rebuild(world, checkpoints=(replace(world.checkpoints[1], required_beacons=(second,)),))
    special.reset(True)
    assert special.states[second] and not special.states[first] and not special.goal_ready()
    special.reset(False)
    assert special.level_id == 'pond_duckweed' and not special.checkpoint_id and not special.completed_stages
    checks['checkpoint_identity_prerequisites_and_epoch'] = True

    malformed = (
        lambda: World(levels=()),
        lambda: World(entities=()),
        lambda: World(checkpoints=()),
        lambda: rebuild(world, entities=(*world.entities, world.entities[0])),
        lambda: rebuild(world, entities=(replace(world.entities[0], point=(float('nan'), 1)), *world.entities[1:])),
        lambda: rebuild(world, levels=(replace(world.levels[0], bounds=(0, 0, float('nan'), 1)), world.levels[1])),
        lambda: rebuild(world, portals=(replace(portal, right='missing'),)),
        lambda: rebuild(world, portals=(replace(portal, x=1500),)),
        lambda: rebuild(world, portals=()),
        lambda: rebuild(world, checkpoints=(replace(world.checkpoints[0], platform=replace(platforms[2])),)),
        lambda: rebuild(world, checkpoints=(replace(world.checkpoints[0], point=(486, 330)),)),
        lambda: rebuild(world, checkpoints=(replace(world.checkpoints[0], required_beacons=(('missing', 'x', 'y'),)),)),
    )
    for factory in malformed:
        try:
            factory()
        except ValueError:
            pass
        else:
            raise AssertionError('Malformed World admitted.')
    checks['malformed_world_cases'] = len(malformed)
    Path(__file__).with_name('world_results.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
    return checks


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
