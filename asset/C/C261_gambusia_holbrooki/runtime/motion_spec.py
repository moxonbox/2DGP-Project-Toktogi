"""Authored poses and timings; these are game design values, not fish biology."""
import math

REVISION='gambusia-r03'
ASSET_ID='C261_gambusia_holbrooki'
PIXELS_PER_BU=128/1.78
VARIANTS={'female':{'sl_mm':60,'sl_bu':.965396*6,'cell':640},
          'male':{'sl_mm':35,'sl_bu':.965396*3.5,'cell':384}}
PHASES=('pre','mid','end')
VIEWS=('left','right','front','top')
# start pitch, mid entry pitch, mid exit pitch, exit pitch, tail amplitude, mid seconds
DESIGNS={
 'hover_or_school':(0,0,0,0,.035,1.6),'cruise':(0,0,0,0,.11,1.2),
 'turn':(0,0,0,0,.16,.8),'surface_rise':(0,20,55,55,.07,1.8),
 'surface_peek':(55,55,55,55,.025,.8),'surface_gape':(55,55,55,55,.025,1.2),
 'surface_submerge':(55,55,0,0,.08,1.2),'surface_snap':(55,55,55,55,.07,.6),
 'swallow':(55,55,55,55,.025,.8),'forage_cruise':(0,0,0,0,.095,1.2),
 'evade_or_dive':(0,-35,-25,0,.22,.8),'breach_launch':(0,55,55,55,.24,.6),
 'airborne_arc':(55,55,0,0,.015,.7),'surface_fall':(0,0,-65,-65,.02,.7),
 'water_reentry':(-65,-65,0,0,.10,.8),'out_of_water':(0,0,-65,-65,.0,.8)}
LOOPS={'hover_or_school','cruise','forage_cruise','surface_gape'}
SEQUENCES={'surface':['cruise','surface_rise','surface_peek','surface_gape','surface_submerge','cruise'],
           'breach':['cruise','breach_launch','airborne_arc','surface_fall','water_reentry','cruise'],
           'feeding':['surface_rise','surface_peek','surface_snap','swallow','surface_submerge','cruise']}


def smooth(u):
    u=max(0.,min(1.,u))
    return u*u*(3-2*u)


def phase_duration(action,phase):
    if action not in DESIGNS or phase not in PHASES:
        raise ValueError(f'unsupported action/phase: {action}/{phase}')
    return DESIGNS[action][5] if phase=='mid' else .3


def samples(action,phase):
    count=12 if phase=='mid' else 3
    duration=phase_duration(action,phase)
    return [{'index':i,'time':i*duration/count,'u':i/count,'duration':duration/count} for i in range(count)]


def pose(action,phase,u,*,speed_weight=1.,turn_weight=1.,hit_weight=0.):
    if action not in DESIGNS or phase not in PHASES or not all(math.isfinite(x) for x in (u,speed_weight,turn_weight,hit_weight)):
        raise ValueError(f'invalid pose {action}/{phase}/{u}')
    a,b,c,d,amplitude,_=DESIGNS[action]
    u=max(0.,min(1.,u)); ease=smooth(u)
    pitch=a+(b-a)*ease if phase=='pre' else b+(c-b)*ease if phase=='mid' else c+(d-c)*ease
    envelope=1 if phase=='mid' else smooth(u) if phase=='pre' else 1-smooth(u)
    wave=math.tau*u
    weights=max(0,min(1,speed_weight))
    result={'fish_body':[0,math.radians(pitch),0],'head':[0,0,0]}
    for i in range(1,5):
        result[f'spine_{i:02}']=[0,0,amplitude*weights*math.sin(wave)*(.35+i*.16)*envelope]
    result['tail_peduncle']=[0,0,amplitude*weights*math.sin(wave-.35)*envelope]
    result['caudal_fin']=[0,0,amplitude*1.5*weights*math.sin(wave-.7)*envelope]
    if action in ('turn','evade_or_dive','forage_cruise'):
        result['fish_body'][2]=(.45 if action!='forage_cruise' else .12)*math.sin(math.pi*u)**2*turn_weight*envelope
    result['fish_body'][0]=-.08*math.sin(math.pi*u)**2*hit_weight
    for side,sign in (('L',1),('R',-1)):
        result[f'pectoral_{side}']=[sign*(.10+.12*math.sin(2*wave))*envelope,0,sign*.12*math.sin(wave)*envelope]
        result[f'pelvic_{side}']=[sign*.08*math.sin(wave+.3)*envelope,0,0]
        result[f'operculum_{side}']=[0,0,sign*.025*(1-math.cos(wave))*envelope]
    result['dorsal_fin']=[.07*math.sin(wave)*envelope,0,0]
    result['anal_fin']=[-.06*math.sin(wave)*envelope,0,0]
    opening=0.
    if phase=='mid':
        if action=='surface_gape': opening=.5*(1-math.cos(wave))
        elif action=='surface_snap': opening=smooth(u/.3)*(1-smooth((u-.55)/.35))
        elif action=='swallow': opening=.18*math.sin(math.pi*u)**2
    result['jaw_upper_ctrl']=[0,.12*opening,0]
    result['jaw_lower_ctrl']=[0,-.55*opening,0]
    return result


def catalog():
    return {action:{'phases':{phase:{'duration':phase_duration(action,phase),'loop':phase=='mid' and action in LOOPS,
                     'samples':samples(action,phase)} for phase in PHASES},
                    'attack_interval':[.35,.65] if action=='surface_snap' else None,
                    'feed_marker':.6 if action=='swallow' else None} for action in DESIGNS}


if __name__=='__main__':
    assert len(DESIGNS)==16
    for action in DESIGNS:
        for phase in PHASES:
            assert phase_duration(action,phase)>0
            assert pose(action,phase,0)==pose(action,phase,0)
    for sequence in SEQUENCES.values():
        for before,after in zip(sequence,sequence[1:]):
            assert DESIGNS[before][3]==DESIGNS[after][0],(before,after)
    print('PASS 16 actions / 48 phases / sequence pitch boundaries')
