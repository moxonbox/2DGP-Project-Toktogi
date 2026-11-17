"""Run the Toktogi game or its headless verification suite."""
import sys
from app import App, ROOT, pg
from motion_viewer import MODES
from physics import STEP
from play_view import FIELD, PLAY_CLEAR


if __name__=='__main__':
    if '--verify' in sys.argv:
        from verify_prototype import verify
        verify()
    else:
        App().run()
