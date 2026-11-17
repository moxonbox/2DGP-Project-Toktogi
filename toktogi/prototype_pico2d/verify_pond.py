"""Focused CPU fish trials; actual jump keys avoid both locked attack types."""
import json
from pathlib import Path

from game import Game
from materials import Assets
from physics import STEP
from pond import Pond,test_world

ROOT=Path(__file__).resolve().parent


def verify(assets):
    results={}
    for kind in ('peek','jump'):
        for dodge in (False,True):
            game=Game(assets,world=test_world())
            pond=Pond(game.world)
            pond.cycle=int(kind=='jump')
            # Keep this pure hazard test independent of App's optional Pond wiring.
            def step():
                game.step()
                pond.step(game,STEP)
            for _ in range(421):
                step()
                if pond.phase=='warn':
                    break
            assert pond.phase=='warn' and pond.kind==kind
            target=pond.target_x
            if dodge:
                game.edge('space',True)
                game.edge('space',False)
            for _ in range(155):
                step()
                assert pond.target_x==target
            assert pond.hits==(0 if dodge else 1),(kind,dodge,pond.hits,game.x,game.y)
            assert game.launch_count==int(dodge)
            results[kind+('_jump_avoids' if dodge else '_idle_hit')]={'hits':pond.hits,'launches':game.launch_count}
    game=Game(assets,world=test_world())
    pond=Pond(game.world)
    pond.phase,pond.age='attack',.16
    pond.target_x=game.x+30
    pond.step(game,0)
    game.edge('x',True)
    game.edge('x',False)
    # The same active-window segment supplied by Game must repel only once.
    start,end=(game.x+29.55,game.y-11.66),(game.x+29,game.y-19.58)
    assert pond.counter(game,start,end)
    assert not pond.counter(game,start,end) and pond.repels==1 and pond.phase=='recover'
    before=(pond.time,pond.phase,pond.mouth)
    game.pause()
    pond.step(game,1)
    assert (pond.time,pond.phase,pond.mouth)==before
    game.reset()
    pond.step(game,STEP)
    assert pond.run_epoch==game.world.run_epoch and pond.hits==pond.repels==0 and pond.phase=='idle'
    results['counter_pause_reset']={'repel_once':True,'pause_frozen':True,'epoch_reset':True}
    for kind,age in (('peek',.10),('jump',0.)):
        game=Game(assets,world=test_world())
        game.pond=Pond(game.world)
        game.pond.phase,game.pond.kind,game.pond.age='attack',kind,age
        game.pond.target_x=game.x+30
        game.pond.step(game,0)
        game.edge('x',True)
        game.edge('x',False)
        for _ in range(60):
            game.step()
        assert game.pond.repels==game.attack_hits==1 and not game.pond.hits,(kind,game.pond.phase,game.pond.mouth)
        results[kind+'_key_counter']={'repels':1,'attack_hits':1,'player_hits':0}
    return results


if __name__=='__main__':
    assets=Assets(ROOT/'toktogi_assets.zip')
    try:
        result=verify(assets)
        (ROOT/'pond_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,indent=2))
    finally:
        assets.close()
