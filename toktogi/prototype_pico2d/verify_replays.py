"""Reproduce both recorded World scenarios from their declared initial state."""
import json
from pathlib import Path

from game import Game
from materials import Assets
from motion import MotionSet
from physics import STEP
from replays import game_replays, world_replays
from world import World

ROOT=Path(__file__).resolve().parent


def verify(assets):
    play=Game(assets)
    play.edge('right',True)
    untouched=(play.x,play.y,play.time,play.visual(),dict(play.world.states),set(play.held))
    legacy_trace,trace={},{}
    legacy=list(game_replays(assets,trace=legacy_trace))
    recordings=list(world_replays(assets,trace=trace))
    assert len(legacy)==4 and sum(len(t['ticks']) for t in legacy_trace.values())==725
    assert len(recordings)==2 and len({name for name,_,_ in (*legacy,*recordings)})==6
    base_count=len(assets.clips)+len(assets.sequences)+len(dict(MotionSet(assets).game_previews()))
    assert base_count+len(legacy)==261 and base_count+len(legacy)+len(recordings)==263
    results={}
    for name,track,events in recordings:
        recorded=trace[name]
        assert recorded['fields']==['x','y','vx','vy','support','action','cell']
        assert recorded['world']['profile']=='seamless'
        world=World.seamless()
        game=Game(assets,world=world)
        initial=recorded['initial']
        assert recorded['world']['revision']==world.revision
        assert initial['time']==0 and initial['action']=='Idle' and not initial['held']
        game.support=next(p for p in game.course.platforms if world.platform_ids[id(p)]==initial['support'])
        for field in ('x','y','vx','vy','view','aim'):
            setattr(game,field,initial[field])
        assert world.level_id==initial['level_id'] and world.run_epoch==initial['run_epoch']
        assert len(recorded['world']['platforms'])==11 and len(recorded['world']['objects'])==8
        commands={}
        for tick,key,down in recorded['inputs']:
            commands.setdefault(tick,[]).append((key,down))
        for tick,expected in enumerate(recorded['ticks']):
            def input_at_boundary():
                for command in commands.get(tick,()):
                    game.edge(*command)
            game.step(on_input=input_at_boundary)
            support=next((i for i,p in enumerate(game.course.platforms) if p is game.support),None)
            actual=(game.x,game.y,game.vx,game.vy,support,game.action,game.visual())
            context=(world.level_id,world.stage_id,world.run_epoch,world.crossing_sequence,
                     tuple(sorted(game.held)),game.launch_count)
            assert actual==expected and context==recorded['context_ticks'][tick]
            assert track.cells[track.index(tick*STEP)]==game.visual()
        assert len(world.events)==len(recorded['portal_events'])==1
        portal_tick,portal_time,event=recorded['portal_events'][0]
        assert event==(1,'pond_lotus',1,'pond_duckweed','lotus_leaf')
        assert ('portal:pond_lotus',portal_time) in events
        row=recorded['ticks'][portal_tick]
        before=recorded['ticks'][portal_tick-1]
        context=recorded['context_ticks'][portal_tick]
        assert before[0]<1000<=row[0] and abs(row[0]-before[0]-row[2]*STEP)<1e-9
        assert context[0:4]==('lotus_leaf','stage_02',1,1) and 'right' in context[4]
        if name.endswith('air_cross'):
            assert row[4] is None and row[5]=='Jump' and context[5]==1
            assert len([event for event in events if event[0]=='launch'])==1
        else:
            assert row[4]==4 and row[5]=='Walk' and context[5]==0
            assert row[1]==before[1]==125 and not any(e[0]=='launch' for e in events)
        assert game.run=='Playing' and not game.bites and not game.attack_hits
        # Seeking the immutable Track is display-only, including backwards seeks.
        for moment in (track.duration,0,portal_time,0):
            assert track.cells[track.index(moment)] in assets.cells
        results[name]={'ticks':len(recorded['ticks']),'crossing_tick':portal_tick,
                       'crossing_seconds':portal_time,'events':events,'exact_reproduction':True}
    assert untouched==(play.x,play.y,play.time,play.visual(),dict(play.world.states),set(play.held))
    json.dumps(trace)
    return {'legacy_replays':4,'world_replays':2,'legacy_catalog':261,'seamless_catalog':263,
            'live_game_unchanged':True,'recordings':results},trace


if __name__=='__main__':
    assets=Assets(ROOT/'toktogi_assets.zip')
    try:
        result,trace=verify(assets)
        (ROOT/'replay_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        (ROOT/'world_replay_trace.json').write_text(json.dumps(trace,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,indent=2))
    finally:
        assets.close()
