from input_clock import Event
from geometry import crop_box
"""Exercise the framework-r4 portions of previously untraced v2.1 requirements."""
from dataclasses import replace
from app import CONTROL_KEYS, GAME_KEYS
from course import COURSE
from game import Game
from physics import STEP
from timeline import FixedStepTimeline

def verify(app):
    checks = {}
    game = Game(app.assets)
    course = game.course
    start, _, elastic, hazard, _, recovery = course.platforms

    def place(platform, x, view='right'):
        game.reset()
        game.support = platform
        game.x, game.y, game.view = (x, float(platform.y), view)

    def tap(key):
        game.edge(key, True)
        game.edge(key, False)

    def step(count):
        for _ in range(count):
            game.step()

    def key(keycode, down=True, at=None):
        event = Event('key_down' if down else 'key_up', key=keycode, mod=0)
        app.event(event, at=at)
    app.switch('game')
    app.game.reset()
    app.physical_keys.clear()
    app.control_keys.clear()
    app.timeline = FixedStepTimeline(STEP)
    assert set(GAME_KEYS.values()) == {'left', 'right', 'up', 'down', 'space', 'shift', 'e', 'f', 'g', 'x', 'q', 'z'}
    assert not set(GAME_KEYS) & set(CONTROL_KEYS)
    assert GAME_KEYS['x'] == 'x' and GAME_KEYS['g'] == 'g'
    assert GAME_KEYS['lshift'] == GAME_KEYS['rshift'] == 'shift'
    for unused in ('c', 'v'):
        key(unused)
        key(unused, False)
    assert app.game.action == 'Idle' and (not app.game.held) and (app.game.work is None) and (app.game.prep is None)
    checks['SCOPE-01'] = {'play_bindings': sorted(set(GAME_KEYS.values())), 'unused_play_keys': ['C', 'V']}
    checks['INPUT-08'] = {'game_keys': len(GAME_KEYS), 'control_overlap': 0}
    key('p')
    key('p', False)
    for _ in range(3):
        app.update(1.0)
    assert app.game.run == 'Paused' and app.game.time == 0
    key('p')
    key('p', False)
    for down in (True, False):
        key('space', down, at=app.timeline.tick_wall - 1.0)
    app.update(STEP)
    assert app.game.prep is not None and app.game.launch_count == 0
    for _ in range(30):
        app.update(STEP)
    assert app.game.launch_count == 1
    checks['TIME-05'] = {'paused_wall_seconds': 3, 'late_input_launches': 1}
    for name in ('e', 'f', 'g'):
        place(start, 150, 'left')
        guide = {'e': ('interact_activate', 0.2, 'interaction_work_socket'), 'f': ('feed_cycle', 0.22, 'mouth_marker')}.get(name)
        if guide:
            x, y = game.socket(*guide)
            game.course = replace(course, **{'beacon': (x, y - 7)} if name == 'e' else {'food': (x, y + 15)})
        game.action = 'Jump'
        game.set_clip('recovery_start', game.duration('recovery_start'))
        game.edge(name, True)
        assert game.action == 'Interact' and game.work['key'] == name
        place(start, 150, 'left')
        tap('space')
        game.edge(name, True)
        assert game.prep is not None and game.pending_work is None and (game.work is None) and (not game.launch_count)
        place(start, 150, 'left')
        game.support, game.y = (None, start.y - 10)
        game.edge(name, True)
        assert game.prep is None and game.pending_work is None and (game.work is None) and (not game.launch_count)
        game.course = course
    checks['INPUT-07'] = {'keys': ['E', 'F', 'G'], 'contexts': ['grounded recovery end', 'preparation', 'air']}
    place(start, 150)
    tap('space')
    game.support = replace(start)
    step(20)
    assert game.prep is None and game.launch_count == 0 and (game.offer is None) and (game.recovery == 0)
    place(hazard, course.shell[0] - 33)
    tap('space')
    step(9)
    assert game.prep is not None and game.support is hazard
    game.x = course.shell[0] - 7
    game.step()
    assert game.clip == 'hit_ground' and game.prep is None and (game.launch_count == 0) and (game.recovery == 0)
    checks['JUMP-03'] = {'changed_support_launches': 0, 'hazard_boundary_launches': 0, 'false_recovery': False}
    place(start, 150)
    marker = 'interaction_work_socket_RF'
    bx, by = game.socket('interact_activate_right', 0.2, marker)
    cx, cy = game.socket('interact_collect_right', 0.2, marker)
    game.course = replace(course, beacon=(bx, by - 7), collect=(cx, cy - 9))
    assert game.ready_work() == {'beacon'}
    game.edge('e', True)
    assert game.work['stage'] == 'interact_activate_right'
    step(30)
    assert game.beacon and (not game.collected)
    assert game.ready_work() == {'collect'}
    step(150)
    game.edge('e', True)
    assert game.work is None and (not game.collected)
    game.edge('e', False)
    tap('e')
    step(30)
    assert game.collected
    step(150)
    tap('e')
    assert game.work is None and game.ready_work() == set()
    checks['INTERACT-01'] = {'priority_when_both_reachable': ['beacon', 'collect']}
    checks['INTERACT-07'] = {'hold_restarted': False, 'release_cancels_one_shot': False, 'consumed_targets_readmitted': False}
    game.course = course
    place(hazard, course.shell[0] - 7)
    game.step(on_input=lambda: game.edge('x', True))
    assert game.clip == 'hit_ground' and game.work is None and game.shell and (game.attack_hits == 0)
    hit_until = game.hit_until
    game.x, game.y, game.vx, game.vy = (course.shell[0] - 7, hazard.y, 0, 0)
    game.step()
    assert game.hit_until == hit_until
    checks['COMBAT-03'] = {'same_tick_hit_precedes_attack': True, 'immunity_blocks_second_hit': True}
    place(hazard, course.shell[0] - 33)
    tap('x')
    assert game.work and game.action == 'Combat'
    game.x = course.fail_bounds[1] + 1
    game.step()
    assert game.run == 'Failed' and game.work is None
    tap('space')
    step(60)
    assert game.run == 'Failed' and game.shell and (not game.attack_hits) and (not game.launch_count)
    checks['COMBAT-06'] = {'effects_after_failed': game.attack_hits, 'space_revives': False}
    place(recovery, 380)
    game.support, game.y, game.vy = (None, recovery.y - 3, 150)
    step(12)
    assert game.support is recovery and game.run == 'Playing'
    game.support, game.y = (None, course.fail_bounds[2] + 1)
    game.step()
    assert game.run == 'Failed'
    failed_at = game.time
    step(3)
    assert game.time == failed_at and game.run == 'Failed'
    checks['RUN-02'] = {'recovery_landing': 'Playing', 'outside_boundary': 'Failed'}
    for beacon in (False, True):
        place(elastic, course.checkpoint[0])
        game.beacon = beacon
        tap('e')
        assert not game.checkpoint
        for _ in range(2):
            game.support, game.y, game.vy = (None, elastic.y - 1, 180)
            game.step()
            assert game.support is elastic and game.checkpoint == beacon
    checks['RUN-03'] = {'checkpoint_needs_beacon_and_landing': True, 'manual_e_activates_checkpoint': False}
    return checks
