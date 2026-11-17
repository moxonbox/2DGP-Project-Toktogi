"""Headless Game/World effects, boundaries, reachable routes and legacy replay proof."""
import argparse
from dataclasses import replace
import importlib.util
import json
from pathlib import Path

from course import COURSE
from game import Game, POST_WINDOW
from materials import Assets
from physics import STEP
from world import World

ROOT = Path(__file__).resolve().parent


def copy_world(world, **changes):
    fields = dict(course=world.course, revision=world.revision, levels=world.levels,
                  entities=world.entities, portals=world.portals, checkpoints=world.checkpoints,
                  spawn_platform=world.spawn_platform, spawn_level=world.spawn_level)
    fields.update(changes)
    return World(**fields)


def place(game, platform, x, level=None):
    game.close_input()
    game.support, game.x, game.y = platform, x, float(platform.y)
    game.vx = game.vy = game.recovery = 0.
    game.view, game.action = 'right', 'Idle'
    game.set_clip('idle')
    if level is not None:
        game.world.level_id = level


def ticks(game, count):
    for _ in range(count):
        game.step()


def verify_effects(assets):
    game = Game(assets, world=World.seamless())
    world, platforms = game.world, game.course.platforms
    for kind, key, clip, seconds, support, count in (
            ('food', 'f', 'feed_cycle', .22, 0, 55),
            ('beacon', 'e', 'interact_activate_right', .20, 1, 105),
            ('collect', 'e', 'interact_collect_right', .20, 2, 105)):
        targets = world.targets(kind)
        for index, target in enumerate(targets):
            platform = platforms[4 if kind == 'food' and index else support + index * 5]
            place(game, platform, target.point[0], target.level_id)
            game.x += target.touch[0] - game.socket(clip, seconds, 'mouth_marker' if kind == 'food' else 'interaction_work_socket_RF')[0]
            assert game.work_contact(clip, target.touch, seconds)
            assert target.key in game.ready_work()
            before = dict(world.states)
            game.edge(key, True)
            assert game.work['target'] == target.key
            if key == 'e':
                game.edge(key, False)
            ticks(game, count)
            if key == 'f':
                game.edge(key, False)
            expected = 3 if kind == 'food' else True
            assert world.states[target.key] == expected
            assert all(world.states[k] == value for k, value in before.items() if k != target.key)
    for index, target in enumerate(world.targets('shell')):
        place(game, platforms[3 + index * 5], target.point[0] - 33, target.level_id)
        before = dict(world.states)
        game.edge('x', True)
        game.edge('x', False)
        ticks(game, 48)
        assert not world.states[target.key] and game.attack_hits == index + 1
        assert all(world.states[k] == value for k, value in before.items() if k != target.key)
    assert game.food == 3 and game.beacon and game.collected and not game.shell
    # Contact loss cancels an uncommitted bite; a prior commit remains permanent.
    game.reset()
    target = world.targets('food')[0]
    place(game, platforms[0], target.point[0] - 29.8375)
    game.edge('f', True)
    assert game.work
    game.x -= 5
    ticks(game, 60)
    assert game.bites == 0 and world.states[target.key] == 4
    return {'independent_objects': 8, 'effects_from_keys': True, 'lost_contact_cancels': True}


def snapshot(game):
    support = next((i for i, platform in enumerate(game.course.platforms) if platform is game.support), None)
    work = tuple(game.work.get(k) for k in ('key', 'target', 'stage', 'age', 'committed')) if game.work else None
    return (game.x, game.y, game.vx, game.vy, game.view, game.aim, game.run, game.action,
            game.clip, game.visual_time, game.visual(), support, game.prep, work,
            game.transition_time, tuple(sorted(game.held)), game.launch_count,
            game.elastic_count, game.bites, game.attack_hits, game.world.states)


def verify_boundaries(assets):
    modes = ('walk', 'air', 'prep', 'f', 'e', 'x', 'q', 'z')
    for mode in modes:
        world = World.seamless()
        # Nearby second-level targets prove lookup/binding is independent of context.
        entities = tuple(replace(e, point=(1000, 125)) if e.kind == 'beacon' and e.level_id == 'lotus_leaf'
                         else replace(e, point=(1032, 125)) if e.kind == 'shell' and e.level_id == 'lotus_leaf'
                         else e for e in world.entities)
        world = copy_world(world, entities=entities)
        control_world = copy_world(world, portals=(replace(world.portals[0], x=1080),))
        games = (Game(assets, world=world), Game(assets, world=control_world))
        for game in games:
            place(game, game.course.platforms[4], 999.98)
            game.vx = 24.
            if mode == 'walk':
                game.edge('right', True)
            elif mode == 'air':
                game.support, game.y, game.vx, game.vy = None, 90., 148., -120.
                game.flight_started, game.flight_rotation, game.launched = game.time, True, True
                game.set_clip('air_rise')
            elif mode == 'prep':
                game.edge('space', True)
                game.edge('space', False)
            else:
                if mode == 'q':
                    game.edge('right', True)
                game.edge(mode, True)
                if mode != 'f':
                    game.edge(mode, False)
        assert snapshot(games[0]) == snapshot(games[1])
        target = games[0].work['target'] if games[0].work else None
        for _ in range(55 if mode == 'f' else 105 if mode == 'e' else 48 if mode == 'x' else 4):
            for game in games:
                game.step()
            assert snapshot(games[0]) == snapshot(games[1]), mode
        game = games[0]
        assert len(world.events) == (0 if mode == 'z' else 1), mode
        assert not control_world.events
        assert world.run_epoch == control_world.run_epoch == 1
        if target:
            assert game.world.states[target] == (3 if mode == 'f' else True)
        if mode == 'x':
            assert game.attack_hits == 1 and not world.states[world.targets('shell')[1].key]

    game = Game(assets, world=World.seamless())
    place(game, game.course.platforms[4], 999.98)
    before = dict(game.world.states)
    for crossing in range(6):
        direction = 'right' if crossing % 2 == 0 else 'left'
        other = 'left' if direction == 'right' else 'right'
        game.edge(other, False)
        game.edge(direction, True)
        for _ in range(200):
            game.step()
            if len(game.world.events) == crossing + 1:
                break
        else:
            raise AssertionError('Bidirectional crossing did not occur.')
        assert game.world.states == before
    game.close_input()
    ticks(game, 24)
    event_count = len(game.world.events)
    ticks(game, 120)
    assert len(game.world.events) == event_count == 6

    # Pause freezes the boundary; restart/failure take priority over crossing.
    game.reset()
    place(game, game.course.platforms[4], 999.98)
    game.edge('f', True)
    game.pause()
    frozen = snapshot(game)
    ticks(game, 60)
    assert snapshot(game) == frozen and not game.world.events
    game.pause()
    ticks(game, 60)
    assert not game.work and not game.bites and not game.held
    game.reset()
    place(game, game.course.platforms[4], 999.98)
    game.vx = 24.
    game.step(on_input=lambda: game.reset(True))
    assert game.world.run_epoch == 4 and not game.world.events
    assert game.support is game.course.platforms[2] and game.world.level_id == 'pond_duckweed'
    game.reset()
    game.x, game.y, game.vx, game.support = 999., 600., 240., None
    game.step()
    assert game.run == 'Failed' and not game.world.events
    return {'paired_modes': list(modes), 'exact_motion_state': True, 'reverse_crossings': 6,
            'pause_restart_failure_priority': True}


def verify_checkpoint(assets):
    world = World.seamless()
    first, second = (e.key for e in world.targets('beacon'))
    checkpoint = replace(world.checkpoints[1], required_beacons=(second,))
    world = copy_world(world, checkpoints=(checkpoint,))
    game = Game(assets, world=world)
    world.states[first] = world.states[second] = True
    world.states[world.targets('food')[0].key] = 0
    world.states[world.targets('collect')[1].key] = True
    world.states[world.targets('shell')[1].key] = False
    assert world.landed(checkpoint.platform)
    game.reset(True)
    assert world.states[second] and not world.states[first]
    assert game.support is checkpoint.platform and (game.x, game.y) == checkpoint.point
    assert game.view == 'right' and game.clip == 'respawn' and world.level_id == 'lotus_leaf'
    assert game.food == 4 and not game.collected and all(world.states[e.key] for e in world.targets('shell'))
    assert not game.held and not game.prep and not game.work and world.run_epoch == 2
    world.states[first] = True
    place(game, game.course.platforms[9], 1780, 'pond_duckweed')
    ticks(game, 30)
    assert game.run == 'Playing'
    world.level_id = 'lotus_leaf'
    ticks(game, 30)
    assert game.run == 'Cleared' and 'stage_02' in world.completed_stages
    return {'explicit_prerequisites_only': True, 'stable_support': True, 'epoch': 2}


def verify_legacy_api(assets):
    game = Game(assets)
    place(game, COURSE.platforms[0], 150)
    bx, by = game.socket('interact_activate_right', .20, 'interaction_work_socket_RF')
    cx, cy = game.socket('interact_collect_right', .20, 'interaction_work_socket_RF')
    game.course = replace(COURSE, beacon=(bx, by - 7), collect=(cx, cy - 9))
    assert game.ready_work() == {'beacon'}
    game.edge('e', True)
    game.edge('e', False)
    ticks(game, 30)
    assert game.beacon and not game.collected and game.ready_work() == {'collect'}
    game.course = COURSE
    assert game.beacon and game.world.entity('beacon').point == COURSE.beacon
    game.reset()
    game.x = 150
    game.edge('space', True)
    game.edge('space', False)
    game.support = replace(game.support)
    ticks(game, 12)
    assert not game.launch_count and game.prep is None
    return {'course_replacement': True, 'legacy_aliases': True, 'prep_requires_identity': True}


def route(assets, seamless=False):
    game = Game(assets, world=World.seamless() if seamless else World())
    platforms = game.course.platforms
    inputs = []

    def edge(key, down):
        inputs.append((round(game.time / STEP), key, down))
        game.edge(key, down)

    def tap(key):
        edge(key, True)
        edge(key, False)

    def step(ticks):
        for _ in range(ticks):
            game.step()

    def until(test, label, ticks=1200):
        for _ in range(ticks):
            if test():
                return
            game.step()
        raise AssertionError((label, game.x, game.y, game.run, game.clip))

    def stop():
        edge('right', False)
        edge('shift', True)
        step(24)
        edge('shift', False)

    for section in range(2 if seamless else 1):
        dx = 900 * section
        offset = 5 * section
        edge('right', True)
        until(lambda: game.x >= 127 + dx, 'takeoff')
        tap('space')
        until(lambda: game.support is platforms[1 + offset], 'beacon platform')
        edge('right', False)
        step(24)
        edge('right', True)
        until(lambda: game.x >= 339 + dx, 'beacon contact')
        stop()
        tap('e')
        step(105)
        assert game.world.states[game.world.targets('beacon')[section].key]
        tap('space')
        until(lambda: game.support is platforms[2 + offset], 'checkpoint')
        assert game.checkpoint
        edge('shift', True)
        step(13)
        edge('shift', False)
        tap('space')
        assert game.prep[3] and 0 < game.time - game.offer[1] < POST_WINDOW
        until(lambda: game.support is platforms[3 + offset], 'hazard platform')
        stop()
        edge('right', True)
        until(lambda: game.x >= 690 + dx, 'attack range')
        stop()
        tap('x')
        step(48)
        assert not game.world.states[game.world.targets('shell')[section].key]
        edge('right', True)
        until(lambda: game.x >= 746 + dx, 'goal takeoff')
        stop()
        tap('space')
        until(lambda: game.support is platforms[4 + offset], 'goal platform')
        edge('shift', True)
        if seamless and section == 0:
            until(lambda: abs(game.vx) < 1, 'bridge stop')
            step(24)
            assert game.run == 'Playing'
            edge('shift', False)
        else:
            until(lambda: game.run == 'Cleared', 'final goal')
    assert game.launch_count == (8 if seamless else 4)
    assert game.elastic_count == (2 if seamless else 1)
    if seamless:
        assert game.world.completed_stages == {'stage_01', 'stage_02'}
        assert len(game.world.events) == 1
    else:
        assert abs(game.time - 13.75) < 1e-8
    return {'seconds': round(game.time, 6), 'launches': game.launch_count,
            'elastic_launches': game.elastic_count, 'world_revision': game.world.revision,
            'portal_events': game.world.events, 'inputs': inputs}


def compare_legacy(assets, legacy_path):
    """Use the shipped four replay inputs against the original controller itself."""
    import replays
    spec = importlib.util.spec_from_file_location('original_game', legacy_path)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    current_trace, legacy_trace = {}, {}
    current = list(replays.game_replays(assets, trace=current_trace))
    replay_game = replays.Game
    try:
        replays.Game = original.Game
        legacy = list(replays.game_replays(assets, trace=legacy_trace))
    finally:
        replays.Game = replay_game
    assert current_trace == legacy_trace
    for (name, track, events), (old_name, old_track, old_events) in zip(current, legacy):
        assert name == old_name and track.cells == old_track.cells
        assert track.durations == old_track.durations and events == old_events
    ticks = sum(len(value['ticks']) for value in current_trace.values())
    assert len(current) == 4 and ticks == 725
    return {'cases': 4, 'ticks': ticks, 'exact': True}


def verify(assets, legacy_path=None):
    checks = {'effects': verify_effects(assets), 'boundaries': verify_boundaries(assets),
              'checkpoint': verify_checkpoint(assets),
              'legacy_api': verify_legacy_api(assets),
              'legacy_route': route(assets), 'seamless_route': route(assets, True)}
    if legacy_path is not None:
        checks['legacy_replays'] = compare_legacy(assets, legacy_path)
    return checks


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--legacy', type=Path, default=ROOT.parent / 'prototype' / 'game.py')
    args = parser.parse_args()
    assets = Assets(ROOT / 'toktogi_assets.zip')
    try:
        result = verify(assets, args.legacy)
        (ROOT / 'world_game_results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({key: {k: v for k, v in value.items() if k != 'inputs'} for key, value in result.items()}, ensure_ascii=False, indent=2))
    finally:
        assets.close()
