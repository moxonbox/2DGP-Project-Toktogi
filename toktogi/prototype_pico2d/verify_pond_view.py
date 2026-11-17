"""Focused headless pond-view proof; leaves remain procedural test geometry."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from materials import Assets
from game import Game
from pond import Pond, test_world
from pond_view import PondView
from play_view import SCREEN, FIELD, PLAY_CLEAR


def verify(asset_root=None):
    root = Path(__file__).resolve().parent
    assets = Assets(root / 'toktogi_assets.zip')
    view = None
    try:
        world = test_world()
        game = Game(assets, world=world)
        pond = Pond(world)
        view = PondView(assets, world, pond, asset_root)
        view.step(game, 0)
        frame = Image.new('RGBA', SCREEN)
        folder = root / 'pond_artifacts'
        folder.mkdir(exist_ok=True)
        screenshots = {}
        before = game.x, game.y, game.time, game.launch_count, tuple(world.states.items())
        for name, phase, action, u, mouth_y in (
                ('idle', 'idle', 'water_reentry', 1., 420.),
                ('warning', 'warn', 'surface_peek', .8, 392.),
                ('jump', 'attack', 'airborne_arc', .5, 300.)):
            pond.phase, pond.action, pond.u = phase, action, u
            pond.mouth = pond.target_x, mouth_y
            sprite, anchor = view.fish.frame(action, u)
            original = hashlib.sha256(sprite.tobytes()).hexdigest()
            view.draw(frame, game)
            assert hashlib.sha256(sprite.tobytes()).hexdigest() == original
            assert frame.getpixel((0, 0))[:3] == PLAY_CLEAR
            assert frame.getpixel((FIELD.x+500, FIELD.y+500))[:3] == (46, 89, 97)
            assert before == (game.x, game.y, game.time, game.launch_count, tuple(world.states.items()))
            path = folder / f'pond_{name}.png'
            frame.save(path)
            screenshots[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        assert len(set(screenshots.values())) == 3
        assert all(platform.y == 360 for platform in world.course.platforms)
        assert len(view.leaves) == len(world.course.platforms)
        view.close()
        view.close()
        assert view.fish.closed and not view.leaves
        report = {'passed': True, 'screenshots': screenshots, 'water_y': pond.water_y,
                  'leaf_support_y': 360, 'below_water_alpha_factor': .35,
                  'player_and_world_unchanged_by_draw': True, 'authored_fish_frames_unmodified': True,
                  'visual_status': 'Procedural test leaves and flat water; not production lotus assets.',
                  'physical_window_validation': 'not performed'}
        (root / 'pond_view_results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return report
    finally:
        if view:
            view.close()
        assets.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', type=Path)
    print(json.dumps(verify(parser.parse_args().asset_root), indent=2))
