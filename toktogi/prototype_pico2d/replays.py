"""Representative game inputs replayed with the same 120 Hz controller."""
from dataclasses import replace
from itertools import groupby

from course import COURSE
from game import Game
from motion import Track
from physics import STEP
from world import World


def game_replays(assets,*,trace=None):
    cases=(
        ('replay_feed_attack',100.1625,replace(COURSE,shell=(135,476)),85,
         [(0,'f',True),(30,'f',False),(32,'x',True),(33,'x',False)]),
        ('replay_walk_z',125,COURSE,286,
         [(0,'right',True),(42,'z',True),(43,'z',False),(259,'right',False)]),
        ('replay_q_reverse',125,COURSE,206,
         [(101,'q',True),(102,'q',False),(113,'right',True),(123,'right',False),(124,'left',True),(160,'left',False)]),
        ('replay_jump_land',165,COURSE,148,[(0,'space',True),(1,'space',False)]),
    )
    for name,x,course,ticks,inputs in cases:
        game=Game(assets,course)
        game.x=x
        commands={}
        for tick,key,down in inputs:
            commands.setdefault(tick,[]).append((key,down))
        if trace is not None:
            trace[name]={'tick_seconds':STEP,'inputs':inputs,
                         'fields':['x','y','vx','vy','support','action','cell'],'ticks':[]}
        samples=[]
        events=[]
        for tick in range(ticks):
            before=(game.bites,game.attack_hits,game.launch_count,game.support)
            def input_at_boundary():
                for command in commands.get(tick,()):
                    game.edge(*command)
            game.step(on_input=input_at_boundary)
            for label,old,new in zip(('bite','hit','launch'),before,(game.bites,game.attack_hits,game.launch_count)):
                if new>old:
                    events.append((label,game.time))
            if before[3] is None and game.support is not None:
                events.append(('land',game.time))
            cell=game.visual()
            samples.append(cell)
            if trace is not None:
                support=next((i for i,p in enumerate(course.platforms) if p is game.support),None)
                trace[name]['ticks'].append((game.x,game.y,game.vx,game.vy,support,game.action,cell))
        rows=[(cell,sum(1 for _ in repeated)*STEP) for cell,repeated in groupby(samples)]
        yield name,Track((k for k,_ in rows),(d for _,d in rows),False),tuple(events)


def world_replays(assets,*,trace=None):
    """Initialized boundary scenarios; full-route proof lives in verify_world_game."""
    cases=(
        ('replay_world_walk_cross',90,[(0,'right',True),(60,'right',False)]),
        ('replay_world_air_cross',100,[(0,'right',True),(0,'space',True),(1,'space',False),(80,'right',False)]),
    )
    for name,ticks,inputs in cases:
        world=World.seamless()
        game=Game(assets,world=world)
        game.support=world.course.platforms[4]
        game.x,game.y=995.,float(game.support.y)
        commands={}
        for tick,key,down in inputs:
            commands.setdefault(tick,[]).append((key,down))
        if trace is not None:
            trace[name]={
                'tick_seconds':STEP,'inputs':inputs,
                'fields':['x','y','vx','vy','support','action','cell'],'ticks':[],
                'context_fields':['level_id','stage_id','run_epoch','portal_sequence','held','launch_count'],
                'context_ticks':[],'portal_events':[],
                'world':{'profile':'seamless','revision':world.revision,
                         'levels':[(level.level_id,level.stage_id) for level in world.levels],
                         'portals':[(p.portal_id,p.left,p.right,p.x,p.y0,p.y1,p.priority) for p in world.portals],
                         'platforms':[(world.platform_ids[id(p)],p.x0,p.x1,p.y,p.bottom,p.kind) for p in world.course.platforms],
                         'objects':[(e.key,e.kind,e.point,world.states[e.key]) for e in world.entities]},
                'initial':{'x':game.x,'y':game.y,'vx':game.vx,'vy':game.vy,
                           'support':world.platform_ids[id(game.support)],'view':game.view,'aim':game.aim,
                           'level_id':world.level_id,'stage_id':world.stage_id,'run_epoch':world.run_epoch,
                           'time':game.time,'held':tuple(game.held),'action':game.action,'cell':game.visual()},
            }
        samples=[]
        events=[]
        for tick in range(ticks):
            before=(game.bites,game.attack_hits,game.launch_count,game.support,len(world.events))
            def input_at_boundary():
                for command in commands.get(tick,()):
                    game.edge(*command)
            game.step(on_input=input_at_boundary)
            for label,old,new in zip(('bite','hit','launch'),before,(game.bites,game.attack_hits,game.launch_count)):
                if new>old:
                    events.append((label,game.time))
            if before[3] is None and game.support is not None:
                events.append(('land',game.time))
            for event in world.events[before[4]:]:
                events.append(('portal:'+event[1],game.time))
                if trace is not None:
                    trace[name]['portal_events'].append((tick,game.time,event))
            cell=game.visual()
            samples.append(cell)
            if trace is not None:
                support=next((i for i,p in enumerate(world.course.platforms) if p is game.support),None)
                trace[name]['ticks'].append((game.x,game.y,game.vx,game.vy,support,game.action,cell))
                trace[name]['context_ticks'].append((world.level_id,world.stage_id,world.run_epoch,
                                                      world.crossing_sequence,tuple(sorted(game.held)),game.launch_count))
        rows=[(cell,sum(1 for _ in repeated)*STEP) for cell,repeated in groupby(samples)]
        yield name,Track((k for k,_ in rows),(d for _,d in rows),False),tuple(events)
