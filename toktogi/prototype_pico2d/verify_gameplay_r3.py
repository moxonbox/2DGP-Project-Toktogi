from input_clock import Event
from geometry import crop_box
"""Regression proof through the normal App input timeline."""
import os
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', PYGAME_HIDE_SUPPORT_PROMPT='1')
import json
from legacy_test_app import App, ROOT
from game import LEVEL, STEP

def verify():
    app = App()
    g = app.game
    a = app.assets
    checks = {}

    def fresh(platform=0, x=155, view='right'):
        g.reset()
        g.support = LEVEL[platform]
        g.x = x
        g.y = g.support.y
        g.view = view
        app.timeline.pending.clear()
        app.physical_keys.clear()
        app.control_keys.clear()
        app.timeline.accumulator = app.timeline.wall_time = app.timeline.tick_wall = 0.0
        app.focused = True
        app.scene = 'game'

    def key(k, down, at=None):
        app.event(Event('key_down' if down else 'key_up', key=k, mod=0), at=app.timeline.wall_time if at is None else at)

    def ticks(n):
        for _ in range(n):
            app.update(STEP)
    fresh(3, 690, 'left')
    key('g', True, 0.05)
    ticks(375)
    key('right', True)
    key('g', False)
    app.update(0.0)
    ticks(32)
    before = g.visual()
    key('x', True)
    app.update(0.0)
    assert g.visual() == before and g.pending_work == 'x'
    ticks(45)
    assert g.attack_hits == 1 and (not g.shell) and (g.view == 'right')
    checks['groom_turn_attack_direction'] = True
    fresh(1, 300)
    g.support = None
    g.y = 403.8
    g.vy = 400
    g.action = 'Jump'
    g.clip = 'air_fall'
    key('left', True)
    shown = []
    for _ in range(20):
        ticks(1)
        shown.append(g.visual()[0])
    assert shown.count('land_hard') >= 18, shown
    checks['opposite_landing_compression_ticks'] = shown.count('land_hard')
    fresh(1, 300)
    g.support = None
    g.y = 403.8
    g.vy = 400
    g.clip = 'air_fall'
    ticks(4)
    at = app.timeline.wall_time + STEP
    key('left', True, at)
    key('space', True, at)
    key('space', False, at)
    ticks(1)
    track = g.transition[0]
    assert track.cells[-1] == ('jump_pre', 'left', 1)
    assert g.prep[0] - g.time == track.duration
    ticks(20)
    assert g.launch_count == 1 and g.visual()[1] == 'left' and (g.vx < 0)
    checks['opposite_rejump_shared_heading'] = True
    fresh()
    key('left', True, 0.05)
    key('left', False, 0.15)
    key('right', True, 0.15)
    ticks(45)
    assert g.view == 'right' and (not g.transition)
    checks['reverse_turn_returns_early'] = True
    fresh()
    for at, k, down in ((0.05, 'left', True), (0.15, 'left', False), (0.15, 'right', True), (0.18, 'right', False), (0.18, 'left', True), (0.22, 'left', False), (0.22, 'right', True)):
        key(k, down, at)
    ticks(90)
    assert g.view == 'right' and g.transition is None
    checks['repeated_turn_reversals'] = True
    edges = []
    for view in ('left', 'right'):
        for x in (36, 200):
            for aim in ('up', 'down'):
                fresh(x=x, view=view)
                key('lshift', True)
                ticks(40)
                key(aim, True)
                ticks(35)
                markers, legs = a.sample(g.visual())
                assert legs and all((g.support.x0 <= g.x + markers['foot_contact_' + leg]['xy'][0] - 64 <= g.support.x1 for leg in legs))
                previous = g.visual()
                key('x', True)
                app.update(0.0)
                assert not g.work and g.visual() == previous and (g.reject_until > g.time)
                edges.append((view, x, aim, legs))
    checks['edge_aim_and_attack_admission'] = edges
    fresh(4, 835)
    g.beacon = True
    key('right', True)
    ticks(70)
    assert g.run == 'Playing'
    key('right', False)
    key('lshift', True)
    ticks(30)
    assert g.run == 'Cleared' and abs(g.vx) < 1
    checks['goal_requires_stop'] = True
    fresh(x=100.1625)
    key('x', True, 0.05)
    ticks(10)
    assert not g.ready_work()
    key('f', True)
    app.update(0.0)
    assert g.work['key'] == 'x' and g.reject_until > g.time
    checks['work_hint_matches_admission'] = True
    fresh()
    key('p', True, 0.05)
    key('p', True, 0.05)
    ticks(12)
    assert g.run == 'Paused'
    key('p', False)
    key('p', True)
    app.update(0.0)
    assert g.run == 'Playing'
    fresh()
    app.event(Event('focus_lost'), at=0.05)
    key('p', True, 0.06)
    ticks(60)
    assert not app.focused and g.run == 'Paused'
    checks['progress_key_edge_and_focus'] = True
    fresh(view='left')
    key('g', True, 0.05)
    ticks(150)
    cell = g.visual()
    key('p', True)
    app.update(0.0)
    ticks(30)
    assert g.visual() == cell
    key('p', False)
    key('p', True)
    app.update(0.0)
    assert g.visual() == cell
    ticks(42)
    assert not g.work and g.visual()[0] == 'idle'
    checks['pause_resumes_effect_free_pose_return'] = True
    count = 0
    max_error = 0.0
    for name, clip in a.pose_clips.items():
        if name.startswith(('flight_roll_', 'ground_spin_')):
            continue
        for sample in clip['samples']:
            assert sample['support']
            marks = next(iter(sample['views'].values()))['markers']
            max_error = max(max_error, max((abs(marks['foot_contact_' + leg]['world'][2]) for leg in sample['support'])) / a.manifest['coordinate_contract']['world_units_per_pixel'])
            count += 1
    assert count == 780 and max_error < 0.3
    checks['support_labels'] = {'cells': count, 'max_normal_error_px': max_error}
    app.close()
    None
    (ROOT / 'gameplay_r3_results.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    return checks
if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
