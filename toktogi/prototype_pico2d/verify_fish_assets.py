"""Small headless smoke check for the 72 selected C261 sprites."""
from pathlib import Path
from unittest.mock import patch
import argparse
import json
import sys

from fish_assets import ACTIONS, FishAssets, MAX_MEMORY


def verify(asset_root=None):
    assets = FishAssets(asset_root)
    try:
        assert assets.metadata['revision'] == 'gambusia-r03'
        assert assets.memory_bytes == 72*384*384*4 < MAX_MEMORY
        with patch.object(Path,'open',side_effect=AssertionError('Frame selection performed disk I/O')):
            for action in ACTIONS:
                assert assets.frame(action,-1) is assets.frame(action,0)
                assert assets.frame(action,1) is assets.frame(action,2)
                for index in range(12):
                    image,mouth = assets.frame(action,index/12)
                    assert image.mode == 'RGBA' and image.size == (384,384)
                    assert len(mouth) == 2 and image.getbbox() is not None
        for action,u in (('unknown',0),('surface_snap',float('nan'))):
            try: assets.frame(action,u)
            except ValueError: pass
            else: raise AssertionError('Invalid fish frame input accepted')
        assert not any(name in sys.modules for name in ('pygame','numpy'))
        report = {'passed':True, 'metadata':assets.metadata, 'memory_bytes':assets.memory_bytes,
                  'frames_checked':72, 'frame_io_calls':0, 'pygame_or_numpy_imported':False}
    finally:
        assets.close()
        assets.close()
    assert assets.memory_bytes == 0
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset-root',type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.asset_root),indent=2))
