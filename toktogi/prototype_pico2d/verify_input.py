"""Input lifetime checks independent of SDL and presentation rate."""
from app import App
from input_clock import Event,EventClock
from timeline import FixedStepTimeline
from physics import STEP

def verify():
    app=App();checks={}
    def fresh():
        app.scene='game';app.game.reset();app.focused=True
        app.physical_keys.clear();app.control_keys.clear();app.viewer_keys.clear()
        app.epoch=0;app.context_cutoff=float('-inf');app.timeline=FixedStepTimeline(STEP)
        app.viewer.playing=True
    def key(name,down=True,at=None,**kw):app.event(Event('key_down' if down else 'key_up',name,**kw),at=at)
    try:
        key('space',False);app.update(.2);assert app.game.launch_count==0
        key('lshift');key('rshift');key('lshift',False)
        assert 'shift' in app.game.held
        key('rshift',False);assert 'shift' not in app.game.held
        fresh();key('space');key('space');key('p');key('p',False);key('p');key('space',False);app.update(.5)
        assert app.game.launch_count==0 and not app.game.held
        checks['orphan_up_dual_shift_cancel']=True
        fresh();old=app.epoch;key('f2');app.viewer.playing=True
        key('space',epoch=old);assert app.viewer.playing
        key('space');assert not app.viewer.playing
        key('space',repeat=True);assert not app.viewer.playing
        checks['explicit_stale_epoch_both_scenes']=True
        fresh();key('f2',at=.1);app.update(.2)
        key('space',at=.05,timestamp=.05)
        app.update(.1);assert app.viewer.playing
        checks['delayed_native_old_context']=True
        fresh();key('p',at=.01);key('p',False,at=.01);key('p',at=.03);app.update(.1)
        assert app.game.run=='Playing'
        checks['same_timestamp_control_release']=True
        runs=[]
        for hz in (10,15,20,30,60):
            for phase in (0,.003,.006):
                fresh()
                for name,down,at in (('p',True,.01+phase),('p',False,.011+phase),('p',True,.02+phase),('right',True,.03+phase)):
                    key(name,down,at=at)
                for _ in range(hz):app.update(1/hz)
                runs.append((phase,app.game.run,round(app.game.x,9),app.game.action))
        for phase in (0,.003,.006):assert len({r[1:] for r in runs if r[0]==phase})==1
        checks['pause_batch_and_start_phases']=runs
        fresh();key('f2',at=.01);key('space',at=.02);app.update(.1)
        assert app.scene=='viewer' and not app.viewer.playing
        fresh();key('f2',at=.01);key('space',at=.01);app.update(.1)
        assert app.scene=='viewer' and app.viewer.playing
        checks['new_context_later_timestamp_and_old_same_time']=True
        fresh();app.switch('viewer');app.viewer.focus_search()
        app.event(Event('text_editing',text='한'));assert app.viewer.composition=='한' and not app.viewer.search
        app.event(Event('text_input',text='한글'));assert app.viewer.search=='한글' and not app.viewer.composition
        app.event(Event('focus_lost'));assert not app.viewer.searching and not app.viewer.composition
        checks['ime_commit_and_focus_cancel']=True
    finally:app.close()
    return checks

if __name__=='__main__':print(verify())
