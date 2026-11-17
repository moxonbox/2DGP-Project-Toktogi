from input_clock import Event
from geometry import crop_box
"""Acceptance tests for modular reuse and playable yaw turns."""
import json
import os
from dataclasses import replace
from math import dist
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', PYGAME_HIDE_SUPPORT_PROMPT='1')
from app import App, ROOT
from course import COURSE, LEVEL, Platform
from game import Game
from physics import STEP, sweep_x
from motion import Track
from timeline import FixedStepTimeline
from materials import Assets
from sprite_renderer import SpriteRenderer

def verify():
    app = App()
    g, a = (app.game, app.assets)
    checks = {}

    def reset(platform=0, x=125, view='right'):
        g.reset()
        g.support = LEVEL[platform]
        g.x, g.y, g.view = (x, g.support.y, view)
        app.physical_keys.clear()
        app.control_keys.clear()

    def press(k, down):
        event = Event('key_down' if down else 'key_up', key=k, mod=0)
        app.event(event, at=app.timeline.wall_time)
        app.update(0.0)

    def tap(k):
        press(k, True)
        press(k, False)

    def ticks(n):
        for _ in range(n):
            app.update(STEP)
    turn_runs = {}
    for view in ('left', 'right'):
        reset(view=view)
        idle = g.visual()
        tap('z')
        assert g.full_turn and g.transition and (g.transition[1] == view)
        track = g.transition[0]
        assert len(track.cells) == 62 and abs(track.duration - 1.55) < 1e-09
        assert all((a.sample(c)[1] for c in track.cells))
        pixels = lambda c: a.maps(c)['sprite'].convert('RGBA').tobytes()
        assert pixels(track.cells[0]) == pixels(idle) == pixels(track.cells[-1]), view
        shown = []
        while g.transition and len(shown) < 240:
            shown.append(track.index(g.transition_time))
            ticks(1)
            assert g.support is LEVEL[0] and g.x == 125 and (g.vx == g.vy == 0.0)
        assert g.transition is None and g.visual() == idle and (g.view == view)
        assert len(set(shown)) == 62
        for fps in (10, 15, 30, 60):
            step = 120 // fps
            assert all(({x // 16 for x in shown[offset::step]} == {0, 1, 2, 3} for offset in range(step)))
        turn_runs[view] = {'pose_count': len(set(shown)), 'seconds': track.duration}
    checks['both_headings_full_spin'] = turn_runs
    reset()
    g.set_clip('idle', 0.85)
    idle = g.visual()
    tap('z')
    assert g.visual() == idle and g.transition[0].duration > 1.55
    ticks(220)
    assert not g.transition and g.view == 'right'
    checks['idle_spin_current_pose_entry'] = True
    for view in ('left', 'right'):
        reset(view=view)
        direction = 'left' if view == 'left' else 'right'
        press(direction, True)
        ticks(42)
        before = g.visual()
        assert before[0] == 'walk'
        tap('z')
        assert g.transition and g.transition[0].cells[0][0].startswith('brake')
        assert pixels(g.visual()) == pixels(before)
        x = g.x
        ticks(60)
        assert g.x == x and g.transition is not None
        ticks(160)
        assert not g.transition and g.action == 'Walk' and ((g.x > x) == (view == 'right'))
    checks['walk_spin_walk_shared_boundary'] = True
    reset(3, 690, 'right')
    tap('z')
    ticks(40)
    tap('x')
    assert g.pending_work == 'x' and (not g.attack_hits)
    ticks(200)
    assert g.attack_hits == 1 and (not g.shell) and (g.view == 'right')
    reset(view='left')
    tap('z')
    ticks(40)
    tap('space')
    assert g.pending_jump and (not g.launch_count)
    ticks(175)
    assert g.launch_count == 1 and g.view == 'left' and (g.vx < 0)
    reset()
    tap('z')
    ticks(40)
    tap('space')
    press('space', True)
    ticks(190)
    assert not g.launch_count and (not g.pending_jump)
    checks['ordered_spin_follow_ups'] = True
    reset(x=200)
    tap('z')
    assert g.transition is None and g.reject_until > 0
    reset()
    tap('space')
    ticks(30)
    tap('z')
    assert g.transition is None and (not g.full_turn) and (g.launch_count == 1)
    reset()
    tap('z')
    ticks(45)
    freeze = g.visual()
    t = g.time
    tap('p')
    ticks(120)
    assert g.visual() == freeze and g.time == t and (g.run == 'Paused')
    tap('p')
    ticks(150)
    assert not g.transition and g.run == 'Playing'
    checks['spin_guards_and_pause'] = True
    reset()
    cell = g.visual()
    assert app.play_view.light_at(100, 476)[0] - 100 != app.play_view.light_at(800, 209)[0] - 800
    rgb = []
    for x, y in ((100, 476), (800, 209)):
        ox, oy = app.play_view.light_at(x, y)
        sprite = a.render(cell, 'lit', (160 + x - 64, 92 + y - 88), (ox, oy), power=0.82, ambient=0.34)
        rgb.append(sprite.convert('RGBA').tobytes())
    changed = sum((rgb[0][i:i + 3] != rgb[1][i:i + 3] for i in range(0, len(rgb[0]), 4) if rgb[0][i + 3]))
    assert changed > 500 and rgb[0][3::4] == rgb[1][3::4]
    checks['course_lighting_changes_pixels'] = changed
    light = SpriteRenderer(a.maps, 0.0)
    assert light.render(cell, 'normal', (0, 0), (0, 0)).size == (128, 128)
    light.close()
    course = replace(COURSE, spawn_x=165.0)
    repeat = Game(a, course)
    repeat.edge('right', True)
    repeat.step()
    assert repeat.support is LEVEL[0] and repeat.x > 165 and (g.x == 125.0)
    checks['independent_course_and_renderer'] = True
    feeds = []
    for view, x in (('left', 159.8375), ('right', 100.1625)):
        for n in range(49):
            reset(x=x, view=view)
            press('f', True)
            ticks(n)
            before = g.visual()
            bites = g.bites
            press('f', False)
            assert g.work is None and pixels(g.visual()) == pixels(before), (view, n, before, g.visual())
            ticks(90)
            assert g.bites == bites and g.clip == 'idle' and (not g.transition)
            feeds.append(n)
    reset(x=100.1625)
    press('f', True)
    ticks(24)
    press('f', False)
    assert g.transition_kind == 'feed_return' and g.transition
    tap('x')
    assert g.work and g.work['stage'] == 'attack_demo' and (g.pending_work is None)
    checks['feed_cancel_and_new_attack'] = {'samples': len(feeds), 'attack_delay_ticks': 0}
    for i in range(641, 654):
        reset(x=i / 4, view='left')
        assert 'food' not in g.ready_work()
        tap('f')
        assert not g.work
    reset(x=100.1625)
    assert 'food' in g.ready_work()
    tap('f')
    assert not g.work
    checks['work_hint_and_admission'] = True
    walls = (Platform(102, 110, 0, 100), Platform(101, 110, 0, 100))
    for order in (walls, walls[::-1]):
        assert sweep_x(order, 86.8, 70, 172, STEP) == (87.0, 0.0)
    walls = (Platform(92, 100, 0, 100), Platform(92, 101, 0, 100))
    for order in (walls, walls[::-1]):
        assert sweep_x(order, 115.2, 70, -172, STEP) == (115.0, 0.0)
    for invalid in (lambda: replace(COURSE, checkpoint=(486, 360)), lambda: replace(COURSE, platforms=()), lambda: Track(range(3), [0.1, -0.2, 0.3], False), lambda: Track([], [], False), lambda: FixedStepTimeline(0), lambda: FixedStepTimeline(STEP, 0)):
        try:
            invalid()
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid configuration was accepted.')
    checks['nearest_wall_and_configuration_validation'] = True
    contacts = {}
    for view in ('left', 'right'):
        motion = g.motion.track('ground_spin', view)
        groups = [motion.cells[i:i + 5] for i in range(1, 61, 5)]
        units = a.manifest['coordinate_contract']['world_units_per_pixel']
        max_height = max_slide = 0.0
        min_lift = float('inf')
        lifted = set()
        for group in groups:
            samples = [a.sample(cell) for cell in group]
            legs = samples[0][1]
            assert len(legs) == 3 and all((stance == legs for _, stance in samples))
            for leg in legs:
                points = [m['foot_contact_' + leg]['world'] for m, _ in samples]
                max_height = max(max_height, *(abs(p[2]) / units for p in points))
                max_slide = max(max_slide, *(dist(p[:2], q[:2]) / units for p in points for q in points))
            min_lift = min(min_lift, *(v['world'][2] / units for name, v in samples[2][0].items() if name.startswith('foot_contact_') and name[-2:] not in legs))
            for cell, (markers, stance) in zip(group, samples):
                if min((v['world'][2] / units for name, v in markers.items() if name.startswith('foot_contact_') and name[-2:] not in stance)) > 1.7:
                    lifted.add(cell)
        assert max_height < 0.3 and max_slide < 1.0 and (min_lift > 1.7), (view, max_height, max_slide, min_lift)
        for hz in (10, 15, 20, 30, 60):
            period = 120 // hz
            for offset in range(period):
                frames = [motion.index(i * STEP) for i in range(offset, 186, period)]
                assert len({tuple(a.sample(motion.cells[i])[1]) for i in frames if 0 < i < 61}) == 2
                assert any((motion.cells[i] in lifted for i in frames)), (view, hz, offset)
        contacts[view] = dict(stances=len(groups), max_z_px=max_height, max_slide_px=max_slide, min_peak_lift_px=min_lift)
    checks['replanted_spin_10_60fps'] = contacts
    for view in ('left', 'right'):
        reset(view=view)
        g.set_clip('idle', 0.85)
        before = g.visual()
        tap('q')
        assert g.visual() == before
        native = g.motion.track('flight_roll', view)
        mid = native.cells[len(native.cells) // 2]
        reset(x=180 if view == 'right' else 115, view=view)
        tap('space')
        frames = []
        for _ in range(105):
            ticks(1)
            frames.append(g.visual())
        for start in range(12):
            shown = frames[start::12]
            assert mid in shown, (view, start)
            ranges = ({4, 5, 6, 7}, {12, 13, 14, 15})
            indices = {native.cells.index(c) for c in shown if c in native.cells}
            assert all((indices & side for side in ranges)), (view, start, indices)
    for name, track in g.motion.game_previews():
        app.viewer.select(app.viewer.names.index(name))
        assert app.viewer.track.durations == track.durations and app.viewer.track.cells == track.cells
    checks['q_idle_and_game_timing_previews'] = len(app.viewer.game_previews)
    for view, x, shell in (('left', 159.8375, 124), ('right', 100.1625, 135)):
        app.game = g = Game(a, replace(COURSE, shell=(shell, 476)))
        for interruption in ('release', 'pause', 'viewer', 'attack'):
            reset(x=x, view=view)
            press('f', True)
            ticks(30)
            source = g.visual()
            if interruption == 'release':
                press('f', False)
            if interruption == 'pause':
                tap('p')
                ticks(12)
                tap('p')
            if interruption == 'viewer':
                tap('f2')
                ticks(12)
                tap('f1')
            if interruption == 'attack':
                tap('x')
            assert pixels(source) == pixels(g.visual()), (view, interruption, source, g.visual())
            if interruption == 'attack':
                seen = []
                hit_tick = None
                for i in range(43):
                    seen.append(g.visual())
                    ticks(1)
                    if g.attack_hits and hit_tick is None:
                        hit_tick = i + 1
                assert g.attack_hits == 1 and hit_tick == 10, (view, hit_tick)
                assert all((('attack_demo', view, 4) in seen[offset::12] for offset in range(12)))
            else:
                assert g.transition_kind == 'feed_return' and g.transition
                ticks(5)
                assert g.transition and g.x == x and (g.visual()[0] in ('feed_pre', 'feed_cycle'))
                ticks(30)
            assert not g.bites, (view, interruption)
    checks['connected_feed_and_readable_attack'] = {'directions': 2, 'attack_effect_tick': 10, 'visible_at_all_10hz_phases': True}
    cards = app.viewer.replay_events
    assert len(cards) == 4 and any((event == 'hit' for event, _ in cards['replay_feed_attack']))
    assert [name for name, _ in cards['replay_jump_land']] == ['launch', 'land']
    assert any((cell[0] == 'ground_spin_right' for cell in app.viewer.game_previews['replay_walk_z'].cells))
    assert any((cell[0] == 'turn_right_left' for cell in app.viewer.game_previews['replay_q_reverse'].cells))
    checks['four_live_input_replays'] = list(cards)
    for bad in (lambda: replace(COURSE, food=(float('nan'), 476)), lambda: replace(COURSE, fail_bounds=(-68, 1028, 460)), lambda: Game(a, replace(COURSE, platforms=(replace(LEVEL[0], x0=119, x1=122), *LEVEL[1:])))):
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid course should fail at admission.')
    a.maps(('idle', 'right', 0))
    cached = a.maps.cache_info().currsize
    second = Assets(ROOT / 'toktogi_assets.zip', ROOT / 'toktogi_runtime_poses.zip')
    second.maps(('idle', 'right', 0))
    second.close()
    assert a.maps.cache_info().currsize == cached and cached > 0
    checks['course_validation_and_cache_isolation'] = True
    app.game = g = Game(a)
    for x, view, inside in ((200.0, 'right', 'left'), (36.0, 'left', 'right')):
        reset(x=x, view=view)
        press('lshift', True)
        ticks(35)
        edge = g.visual()
        tap('q')
        assert not g.transition and g.visual() == edge
        press(inside, True)
        ticks(20)
        assert not g.transition and g.visual() == edge and (g.x == x)
        press('lshift', False)
        started = False
        for _ in range(330):
            ticks(1)
            if g.transition and g.turn_origin:
                started = True
            if g.visual()[0].startswith(('edge_', 'turn_')) and g.support:
                markers, legs = a.sample(g.visual())
                assert all((g.support.x0 <= g.x + markers['foot_contact_' + leg]['xy'][0] - a.pivot[0] <= g.support.x1 for leg in legs))
        assert started and g.view != view and (g.support is LEVEL[0])
    checks['ledge_q_direction_share_support_gate'] = True
    for view, x, forward, reverse in (('right', 100.1625, 'right', 'left'), ('left', 159.8375, 'left', 'right')):
        for button in (forward, reverse, 'f', 'g'):
            if button == 'g' and view == 'right':
                continue
            reset(x=x, view=view)
            press('f', True)
            ticks(30)
            old_cell = g.visual()
            press('f', False)
            press(button, True)
            assert g.visual() == old_cell
            if button in (forward, reverse):
                ticks(1)
                assert g.x != x and g.visual() == old_cell
                assert g.transition_kind in ('turn', 'feed_move')
                ticks(5)
                assert abs(g.x - x) < 1.0
                ticks(1)
                assert g.visual()[0] not in ('feed_cycle', 'feed_pre')
            else:
                for _ in range(25):
                    if not g.work or 'entry' not in g.work:
                        break
                    ticks(1)
                assert g.bites == 0 and g.work and ('entry' not in g.work)
    checks['feed_to_move_restart_and_groom'] = True
    for obstacle in (Platform(100, 140, 435, 470), Platform(470, 500, 290, 320)):
        try:
            Game(a, replace(COURSE, platforms=(*LEVEL, obstacle)))
        except ValueError as error:
            assert 'clear other solid platforms' in str(error)
        else:
            raise AssertionError('A solid overlaps an admitted spawn or checkpoint.')
    checks['course_spawn_and_checkpoint_clearance'] = True
    for view in ('left', 'right'):
        reset(view=view)
        tap('q')
        frames = []
        while g.transition:
            frames.append(g.visual())
            ticks(1)
        assert 0.48 <= len(frames) * STEP < 0.49
        for offset in range(12):
            masks = {tuple(legs) for cell in frames[offset::12] if len((legs := a.sample(cell)[1])) == 3}
            assert len(masks) == 2, (view, offset, masks)
    checks['q_both_support_sets_all_10hz_phases'] = True
    app.close()
    None
    (ROOT / 'framework_results.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf8')
    return checks
if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
