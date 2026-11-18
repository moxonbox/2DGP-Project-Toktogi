"""Focused storyboard timing, playable controls, stage selection and audio lifetime."""
import argparse
from array import array
from pathlib import Path
from PIL import ImageChops
from app import App
from input_clock import Event
from story_stage import INTRO_END, IMPACT, EYES_OPEN
from story_audio import ambient_pcm, StoryAudio

ROOT = Path(__file__).resolve().parent


def verify(assets_path=ROOT/'toktogi_assets.zip',asset_root=None,capture=None):
    app = App(assets_path,profile='storyboard',asset_root=asset_root)
    g,story = app.game,app.story
    checks = []
    def tap(key):
        app.event(Event('key_down',key))
        app.event(Event('key_up',key))
    try:
        assert story.active and story.intro and app.stage_menu.entries[-1].level_id == 'storyboard_test'
        app.draw()
        assert app.screen.convert('RGB').getbbox() is None
        start = (g.x,g.y,g.time)
        tap('space');tap('d');tap('e');app.update(.5)
        assert (g.x,g.y,g.time) == start and not g.held and g.launch_count == 0
        assert story.firefly() is None
        story.time = 1.2
        first = story.firefly()
        story.time = IMPACT
        impact = story.firefly()
        assert first[0] > impact[0] and abs(impact[0]-g.x)<40
        app.draw()
        assert max(app.screen.convert('RGB').getextrema()[0]) == 255
        story.time = 4.9
        assert story.firefly()[0] < impact[0]
        app.draw()
        sleeping = app.screen.copy()
        story.time = EYES_OPEN
        app.draw()
        assert ImageChops.difference(sleeping,app.screen).getbbox(alpha_only=False)
        opened = story.firefly()
        story.time = 8.
        assert story.firefly()[0] > opened[0]
        story.time = INTRO_END+.1
        assert story.firefly() is None and not story.intro
        if capture:
            app.draw();app.screen.save(capture)
        checks.append('black start, approach, impact, recoil, eyes opening and exit')

        g.x,g.y = story.points[1]
        before = story.strength(g,1)
        tap('e')
        assert story.pulses[1] == 1.2 and g.work is None and not app.physical_keys
        assert story.strength(g,1) > before
        story.pulses[1] = 0
        tap('f')
        assert story.pulses[1] > 0 and g.work and g.work['key'] == 'x'
        g.cancel_work()
        story.step(2.)
        assert story.pulses[1] == 0
        g.x = 125
        assert story.strength(g,1) < before
        tap('d')
        app.event(Event('key_down','d'))
        app.update(.1)
        app.event(Event('key_up','d'))
        assert g.x > 125 and g.time > 0
        checks.append('proximity and fresh E/F brighten mushrooms while F retains attack')

        tap('p')
        frozen = story.time
        app.update(.2)
        assert story.time == frozen
        tap('p');tap('m');app.update(.2);app.draw()
        assert story.time == frozen and app.stage_menu.selected == 3
        for _ in range(3):tap('a')
        tap('return');app.update(.2)
        assert not story.active and g.world.level_id == 'shore' and g.x == 125
        tap('m');app.update(.2)
        for _ in range(3):tap('d')
        tap('e');app.update(.2)
        assert story.active and story.time == 0 and g.x == 520
        tap('r')
        assert story.time == 0 and story.intro and g.x == 520 and not g.held
        tap('f2');app.update(.1)
        assert story.time == 0
        tap('f1')
        checks.append('pause, M original/test round trip, F2 and R replay')

        pcm = array('h')
        pcm.frombytes(ambient_pcm(8000,2))
        assert len(pcm) == 8000*4*2 and 0 < max(map(abs,pcm)) < 32767*.08
        assert pcm[0] == pcm[1] and pcm[-1] == pcm[-2]
        checks.append('deterministic quiet stereo ambience with bounded samples')
        return {'passed':True,'checks':checks,'computer_use':False}
    finally:
        app.close()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root',type=Path)
    parser.add_argument('--capture',type=Path)
    args=parser.parse_args()
    print(verify(asset_root=args.asset_root,capture=args.capture))
