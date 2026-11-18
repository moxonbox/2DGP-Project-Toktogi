"""Focused CPU checks for the F1 stage drawer, input isolation and stage restart."""
import argparse
from pathlib import Path
from input_clock import Event
from app import App
from physics import STEP

ROOT = Path(__file__).resolve().parent


def verify(assets_path=ROOT/'toktogi_assets.zip', asset_root=None, capture=None):
    app = App(assets_path,profile='habitat',asset_root=asset_root)
    g = app.game
    menu = app.stage_menu
    checks = []

    def key(name, down=True, *, at=None, **values):
        app.event(Event('key_down' if down else 'key_up',name,**values),at=at)

    def tap(name):
        key(name)
        key(name,False)

    def open_menu():
        if not menu.opened:
            tap('m')
        app.update(.2)
        app.draw()
        assert menu.opened and menu.progress == 1.

    try:
        # M owns one edge, including events collected in the same low-rate frame.
        key('d',at=.001,timestamp=.001)
        key('m',at=.01,timestamp=.01)
        key('m',at=.02,timestamp=.02,repeat=True)
        key('m',False,at=.03,timestamp=.03)
        key('space',at=.04,timestamp=.04)
        key('space',False,at=.05,timestamp=.05)
        app.update(.1)
        assert menu.opened and 0 < menu.progress < 1.
        frozen = (g.x,g.y,g.time,g.pond.time,app.play_view.camera.x,dict(g.world.states))
        app.update(.2)
        assert frozen == (g.x,g.y,g.time,g.pond.time,app.play_view.camera.x,dict(g.world.states))
        assert not g.held and not app.physical_keys and g.launch_count == 0
        app.draw()
        assert len(app.buttons) == len(menu.entries)+2
        if capture:
            app.screen.save(capture)
        checks.append('animated drawer freezes simulation and consumes held keys')

        # Click the third card, then the start button. Closing retains modal ownership.
        card = app.buttons[3][0]
        app.event(Event('mouse_down',pos=card.center,button=1))
        assert menu.selected == 2
        button = app.buttons[-1][0]
        epoch = g.world.run_epoch
        app.event(Event('mouse_down',pos=button.center,button=1))
        assert not menu.opened and menu.visible and not app.buttons
        assert g.world.level_id == 'reeds' and g.world.run_epoch == epoch+1
        tap('space')
        app.update(.2)
        assert not menu.visible and g.launch_count == 0 and menu.background is None
        app.update(STEP*2)
        assert g.hit_until == 0 and g.run == 'Playing'
        checks.append('mouse selection starts safely and closing blocks game input')

        for index, level in enumerate(g.world.levels):
            open_menu()
            for _ in range(4):
                tap('a')
            for _ in range(index):
                tap('right')
            assert menu.selected == index
            tap('return')
            app.update(.2)
            assert g.world.level_id == level.level_id
            assert (g.support,(g.x,g.y)) == g.world.stage_entry(level.level_id)
            assert g.stable_feet(app.assets.tracks['idle','right'])
            earlier = {item.level_id for item in g.world.levels[:index]}
            assert all(g.world.states[e.key] == (e.level_id in earlier) for e in g.world.targets('beacon'))
            assert g.checkpoint is False and g.work is None and not g.held
            entry = (g.x,g.y)
            g.x += 20
            tap('r')
            assert (g.x,g.y) == entry and g.world.level_id == level.level_id
        checks.append('all three stage entries, prerequisites and R restart')

        checkpoint = g.world.checkpoints[-1]
        assert g.world.landed(checkpoint.platform)
        g.checkpoint = True
        tap('r')
        assert g.world.level_id == checkpoint.level_id and (g.x,g.y) == checkpoint.point
        checks.append('activated checkpoint retains restart priority')

        open_menu()
        frozen = (g.time,g.x,g.y,dict(g.world.states))
        tap('escape')
        app.update(.2)
        assert frozen == (g.time,g.x,g.y,dict(g.world.states)) and g.run == 'Playing'
        app.update(.02)
        assert g.time > frozen[0] and not g.held
        tap('p')
        open_menu()
        tap('m')
        app.update(.2)
        assert g.run == 'Paused'
        checks.append('cancel preserves progress and prior paused state')

        tap('p')
        open_menu()
        app.event(Event('focus_lost'))
        app.event(Event('focus_gained'))
        tap('escape')
        app.update(.2)
        assert g.run == 'Paused'
        checks.append('focus loss prevents automatic game resume')

        open_menu()
        tap('f2')
        assert app.scene == 'viewer' and not menu.visible and menu.background is None
        mode = app.viewer.mode
        tap('m')
        assert app.viewer.mode == (mode+1)%7
        tap('f1')
        assert app.scene == 'game' and not menu.visible
        checks.append('F2 retains M material mode and closes the drawer')

        g.reset()
        open_menu()
        app.update(.2)
        tap('m')
        app.update(.05)
        progress = menu.progress
        tap('m')
        assert menu.opened
        app.update(.02)
        assert menu.progress > progress
        epoch = g.world.run_epoch
        state = dict(g.world.states)
        try:
            g.reset(level_id='missing')
        except ValueError:
            pass
        else:
            raise AssertionError('Unknown stage accepted')
        assert g.world.run_epoch == epoch and g.world.states == state
        checks.append('animation reversal and invalid entry preserve state')
        return {'passed':True,'checks':checks,'computer_use':False}
    finally:
        app.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root',type=Path)
    parser.add_argument('--capture',type=Path)
    args = parser.parse_args()
    print(verify(asset_root=args.asset_root,capture=args.capture))
