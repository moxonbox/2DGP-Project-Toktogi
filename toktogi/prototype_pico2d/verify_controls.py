"""Focused production WASD/contextual E smoke; old fixtures remain separate."""
from app import App
from input_clock import Event
from pond import Pond,test_world

def verify(asset_root=None):
    app=App(profile='pond_test',asset_root=asset_root)
    g=app.game
    def key(name,down=True):app.event(Event('key_down' if down else 'key_up',name))
    try:
        x=g.x;key('right');app.update(.2);key('right',False);assert g.x==x
        key('d');app.update(.2);key('d',False);assert g.x>x
        key('w');assert 'up' in g.held;key('w',False)
        g.reset();g.x=100.1625;key('e');app.update(.8);assert g.bites>0
        key('e',False);bites=g.bites;app.update(.4);assert g.bites==bites
        g.reset();g.support=g.course.platforms[1];g.x=336.9;g.y=360
        key('e');key('e',False);app.update(.3);assert g.beacon
        g.reset();g.support=g.course.platforms[4];g.x=930;g.y=360
        key('e');assert g.work and g.work['key']=='x';key('e',False)
        g.reset();g.pond.phase='attack';g.pond.mouth=(g.x+30,g.y-15)
        key('e');assert g.work and g.work['key']=='x';key('e',False)
        key('p');key('p',False);frozen=g.pond.time;app.update(.3);assert g.pond.time==frozen
        key('r');key('r',False);assert g.pond.phase=='idle' and not g.pond.hits
        app.draw()
        app.screen.save(__import__('pathlib').Path(__file__).with_name('pond_controls_preview.png'))
        return {'WASD':True,'arrows_disabled':True,'E_feed_release':True,'E_activate':True,'E_shell_and_fish_attack':True,'pause_restart':True,'pond_draw':True}
    finally:app.close()

if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument('--asset-root',type=Path)
    result=verify(parser.parse_args().asset_root)
    Path(__file__).with_name('controls_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result)
