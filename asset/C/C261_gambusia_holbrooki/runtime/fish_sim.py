"""120Hz fish physics owns motion, water crossings and exactly-once effects."""
import copy
import math
from dataclasses import dataclass
import numpy as np
from motion_spec import VARIANTS,DESIGNS,PHASES,SEQUENCES,LOOPS,phase_duration

STEP=1/120
CAMERA_UP=(.19780815385329092,.3085807195346556,.9304030706100593)


@dataclass(frozen=True)
class Water:
    left:float=-12
    right:float=12
    surface:float=0
    bottom:float=-12
    id:str='pond'

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.left,self.right,self.surface,self.bottom)) or self.left>=self.right or self.bottom>=self.surface:
            raise ValueError('invalid water volume')


class FishSim:
    def __init__(self,bundle,variant='female',water=Water(),*,breach_enabled=False):
        if variant not in VARIANTS:raise ValueError('unsupported variant '+variant)
        self.bundle=bundle;self.variant=variant;self.water=water;self.sl=VARIANTS[variant]['sl_bu']
        self.breach_enabled=breach_enabled;self.x=0.;self.z=water.surface-.7*self.sl;self.vx=0.;self.vz=0.
        self.action='hover_or_school';self.phase='pre';self.age=0.;self.time=0.;self.view='left'
        self.state_generation=0;self.phase_instance_id=0;self.cycle_id=0;self.attack_instance_id=0
        self.mode='water_column';self.propulsion=True;self.paused=False;self.failed=False
        self.effects=[];self.committed=set();self.sequence=[];self.sequence_position=0;self.gape_cycles=0
        self.launched=False;self.entry_vz=0.;self.apex_z=0.;self.pending_target=None;self.fed=False
        self.transitions=[];self.accumulator=0.;self.exit_seen=False;self.intersection=None

    @property
    def u(self):return min(1,self.age/phase_duration(self.action,self.phase))

    def cell(self,view=None):return self.bundle.cell(self.variant,self.action,self.phase,self.u,view or self.view)

    def geometry(self):return self.bundle.pose(self.variant,self.action,self.phase,self.u)

    def mouth_point(self,geometry=None):
        geometry=geometry or self.geometry();p=geometry['mouth_tip'];heading=1 if self.view=='left' else -1
        return (self.x+heading*.841879*p[0]-.539666*p[1],self.z+p[2])

    def mouth_depth_bias(self):
        p=self.geometry()['mouth_tip'];heading=1 if self.view=='left' else -1
        return CAMERA_UP[0]*p[0]+heading*CAMERA_UP[1]*p[1]

    def set_action(self,action,phase='pre'):
        if action not in DESIGNS or phase not in PHASES:raise ValueError('unsupported action/phase')
        self.state_generation+=1;self.phase_instance_id+=1;self.action=action;self.phase=phase;self.age=0.
        if action=='surface_snap':self.attack_instance_id+=1
        self.transitions.append({'time':self.time,'action':action,'phase':phase,'generation':self.state_generation,'x':self.x,'z':self.z})

    def request(self,action,*,airspace_clear=True,target=None):
        if self.mode=='airborne':return False
        if action=='out_of_water':return False
        if action=='breach_launch' and (not self.breach_enabled or not airspace_clear or self.mode=='airborne'):return False
        if action in ('airborne_arc','surface_fall','water_reentry'):return False
        if action=='surface_snap' and target is None:return False
        if action not in DESIGNS:raise ValueError('unsupported action '+action)
        self.sequence=[];self.pending_target=target;self.set_action(action)
        if action=='breach_launch':self.cycle_id+=1;self.launched=False;self.exit_seen=False
        return True

    def start_sequence(self,name,*,target=None,airspace_clear=True):
        if name not in SEQUENCES:raise ValueError('unsupported sequence '+name)
        if name=='breach' and (not self.breach_enabled or not airspace_clear or self.mode=='airborne'):return False
        if name=='feeding' and target is None:return False
        self.sequence=list(SEQUENCES[name]);self.sequence_position=0;self.pending_target=target
        self.cycle_id+=1;self.gape_cycles=0;self.launched=False;self.exit_seen=False;self.fed=False
        self.set_action(self.sequence[0]);return True

    def cancel(self):
        self.sequence=[];self.pending_target=None
        if self.mode=='airborne' or (self.launched and self.vz>0):
            self.set_action('out_of_water');self.propulsion=False
        elif self.action in ('surface_rise','surface_peek','surface_gape','surface_snap','swallow'):
            self.set_action('surface_submerge')
        else:self.set_action('cruise')

    def seek(self,action,phase,u):
        # Inspection does not run physics or replay historical effect candidates.
        if action not in DESIGNS or phase not in PHASES or not math.isfinite(u) or not 0<=u<=1:raise ValueError('invalid seek')
        return self.bundle.cell(self.variant,action,phase,u,self.view)

    def emit(self,kind,position,*,target=None):
        key=(self.cycle_id,self.attack_instance_id if kind=='attack' else self.state_generation if kind=='feed' else 0,kind,target)
        if key in self.committed:return
        self.committed.add(key)
        self.effects.append({'kind':kind,'time':self.time,'position':list(map(float,position)),
            'cycle_id':self.cycle_id,'state_generation':self.state_generation,'phase_instance_id':self.phase_instance_id,
            'attack_instance_id':self.attack_instance_id if kind=='attack' else None,'target_id':target})

    def waterline(self,geometry=None):
        geometry=geometry or self.geometry();vertices=geometry['vertices'];triangles=geometry['triangles'];plane=self.water.surface-self.z
        if not geometry['bounds'][0,2]<=plane<=geometry['bounds'][1,2]:return None
        heights=vertices[:,2]-plane;values=heights[triangles]
        active=triangles[(values.min(axis=1)<=0)&(values.max(axis=1)>=0)]
        points=[]
        for a,b in ((0,1),(1,2),(2,0)):
            if not len(active):break
            va=vertices[active[:,a]];vb=vertices[active[:,b]];da=va[:,2]-plane;db=vb[:,2]-plane
            valid=(da*db<=0)&(abs(da-db)>1e-9)
            t=da[valid]/(da[valid]-db[valid]);points.extend(va[valid]+(vb[valid]-va[valid])*t[:,None])
        if not points:return None
        centroid=np.mean(points,axis=0);heading=1 if self.view=='left' else -1
        # Third component is camera-up depth bias, so VFX meet the rendered intersection.
        return (self.x+heading*.841879*centroid[0]-.539666*centroid[1],self.water.surface,float(CAMERA_UP[0]*centroid[0]+heading*CAMERA_UP[1]*centroid[1]))

    def _next(self):
        if self.sequence and self.sequence_position+1<len(self.sequence):
            self.sequence_position+=1;self.set_action(self.sequence[self.sequence_position])
        else:
            self.sequence=[];self.set_action('cruise')

    def _clock(self,dt):
        self.age+=dt
        duration=phase_duration(self.action,self.phase)
        if self.age<duration-1e-9:return
        if self.phase=='mid' and self.action in LOOPS:
            if self.action=='surface_gape':
                self.gape_cycles+=1
                if self.sequence and self.gape_cycles>=2:
                    self.phase='end';self.age=0.;self.phase_instance_id+=1;return
            if not self.sequence or self.action=='surface_gape':self.age-=duration;return
        if self.phase=='end':
            if self.action=='turn':self.view='right' if self.view=='left' else 'left';self.vx=-self.vx
            self._next()
        else:self.phase=PHASES[PHASES.index(self.phase)+1];self.age=0.;self.phase_instance_id+=1

    def step(self,dt=STEP,*,target=None,hazard=False,neighbors=()):
        if not math.isfinite(dt) or dt<0 or dt>STEP+1e-8:raise ValueError('step requires 0..1/120 seconds')
        if self.paused or dt==0:return
        self.time+=dt;geometry=self.geometry()
        if not self.launched and self.mode!='airborne' and (not self.water.left<=self.x<=self.water.right or self.z+geometry['bounds'][0,2]>self.water.surface):
            self.mode='airborne';self.set_action('out_of_water');self.propulsion=False
        target=target if target is not None else self.pending_target
        if hazard and self.mode!='airborne' and self.action not in ('evade_or_dive','surface_submerge'):
            self.cancel()
            if self.action!='surface_submerge':self.set_action('evade_or_dive')
        if self.mode=='airborne' or self.action=='out_of_water' or self.launched:
            self.propulsion=False;self.vz-=3*self.sl*dt;self.x+=self.vx*dt;self.z+=self.vz*dt
            if self.action=='airborne_arc':
                self.phase='mid';self.age=phase_duration(self.action,'mid')*max(0,min(1,1-self.vz/max(self.entry_vz,1e-6)))
                if self.vz<=0:self.apex_z=self.z;self.set_action('surface_fall','mid')
            elif self.action=='surface_fall':
                self.age=phase_duration(self.action,'mid')*max(0,min(1,(self.apex_z-self.z)/max(.05*self.sl,self.apex_z-self.water.surface-.5*self.sl)))
            else:self.age=min(self.age+dt,phase_duration(self.action,self.phase))
        else:
            self.propulsion=self.action!='water_reentry' or self.z+geometry['bounds'][1,2]<self.water.surface
            if self.action=='breach_launch' and self.phase=='mid' and not self.launched:
                self.vz=3.6*self.sl;self.vx=0.;self.launched=True;self._clock(dt)
            else:
                speed={'hover_or_school':0.,'cruise':.20,'forage_cruise':.28,'turn':.12,'evade_or_dive':.45}.get(self.action,0.)*self.sl
                direction=-1 if self.view=='left' else 1
                desired_x=direction*speed
                if self.action=='turn':desired_x=-direction*speed
                if self.action=='forage_cruise' and target:desired_x=max(-speed,min(speed,(target['x']-self.x)*.8))
                for neighbor in neighbors:
                    distance=self.x-neighbor['x']
                    if abs(distance)<self.sl:desired_x+=math.copysign(.15*self.sl,distance or 1)
                self.vx+=(desired_x-self.vx)*min(1,dt*4)
                if self.x<self.water.left+.8*self.sl:self.vx=abs(self.vx);self.view='right'
                if self.x>self.water.right-.8*self.sl:self.vx=-abs(self.vx);self.view='left'
                self.x+=self.vx*dt
                if self.action in ('surface_rise','surface_peek','surface_gape','surface_snap','swallow'):
                    desired_z=self.water.surface-geometry['mouth_tip'][2]+.006*self.sl
                    rate=.36*self.sl if self.action=='surface_rise' else .7*self.sl
                elif self.action=='evade_or_dive':desired_z=self.water.surface-1.1*self.sl;rate=.8*self.sl
                else:desired_z=self.water.surface-.7*self.sl;rate=(.9 if self.action=='water_reentry' else .35)*self.sl
                delta=max(-rate*dt,min(rate*dt,desired_z-self.z));self.vz=delta/dt;self.z+=delta
                self.z=max(self.water.bottom+.35*self.sl,self.z)
                if self.action=='surface_rise' and self.phase=='end' and abs(desired_z-self.z)>.01*self.sl:self.age=min(self.age+dt,.29)
                else:self._clock(dt)
                mouth=self.mouth_point()
                if self.action=='surface_snap' and self.phase=='mid' and .35<=self.u<=.65 and target and target.get('visible',True):
                    if math.hypot(mouth[0]-target['x'],mouth[1]-target['z'])<=.04*self.sl+target.get('radius',0.):
                        self.emit('attack',mouth,target=target['id'])
                caught=target and any(e['kind']=='attack' and e['target_id']==target['id'] and e['cycle_id']==self.cycle_id for e in self.effects)
                if self.action=='swallow' and self.phase=='mid' and self.u>=.6 and caught and target.get('resource',False):
                    self.emit('feed',mouth,target=target['id']);self.fed=True
        geometry=self.geometry();minimum=self.z+geometry['bounds'][0,2]
        in_volume=self.water.left<=self.x<=self.water.right
        self.intersection=self.waterline(geometry) if in_volume else None
        mouth_exposed=self.mouth_point(geometry)[1]>self.water.surface
        if self.launched and mouth_exposed and not self.exit_seen:
            self.exit_seen=True
            if self.intersection:self.emit('exit_ripple',self.intersection)
        if minimum>self.water.surface and self.launched and self.mode!='airborne':
            self.mode='airborne';self.entry_vz=max(self.vz,.001);self.set_action('airborne_arc','mid')
        if self.vz<0 and in_volume and self.intersection is not None and (self.mode=='airborne' or self.action=='out_of_water'):
            self.emit('splash',self.intersection);self.emit('ripple',self.intersection)
            self.mode='surface_boundary';self.launched=False;self.propulsion=False;self.vz*=.22;self.vx*=.6
            self.set_action('water_reentry');self.sequence=[]
        elif not in_volume and (self.launched or self.mode=='airborne'):
            if self.action!='out_of_water':self.set_action('out_of_water')
            self.mode='airborne';self.propulsion=False
        elif self.mode!='airborne':
            self.mode='surface_boundary' if mouth_exposed or self.intersection is not None else 'water_column'
        if self.z<self.water.bottom-self.sl and not in_volume:self.failed=True
        if self.action=='out_of_water' and not self.launched:self.propulsion=False

    def advance(self,dt,**sensors):
        if not math.isfinite(dt) or dt<0:raise ValueError('invalid elapsed time')
        if self.paused:return
        self.accumulator+=dt
        while self.accumulator>=STEP-1e-10:
            self.step(STEP,**sensors);self.accumulator-=STEP

    def snapshot(self):
        state={k:copy.deepcopy(v) for k,v in self.__dict__.items() if k not in ('bundle','water','committed')}
        state['committed']=[list(v) for v in sorted(self.committed,key=str)]
        state['water']=self.water.__dict__.copy();state['schema']=1
        return state

    @classmethod
    def restore(cls,bundle,state):
        if state.get('schema')!=1 or state.get('action') not in DESIGNS or state.get('phase') not in PHASES:raise ValueError('invalid fish snapshot')
        if not all(math.isfinite(state[k]) for k in ('x','z','vx','vz','age','time','accumulator')):raise ValueError('nonfinite fish snapshot')
        obj=cls(bundle,state['variant'],Water(**state['water']),breach_enabled=state['breach_enabled'])
        allowed=set(obj.snapshot())
        if set(state)!=allowed or state['view'] not in ('left','right') or state['mode'] not in ('water_column','surface_boundary','airborne'):
            raise ValueError('invalid fish snapshot fields')
        if state['age']<0 or state['time']<0 or not 0<=state['accumulator']<STEP+1e-8:
            raise ValueError('invalid fish snapshot clock')
        if any(action not in DESIGNS for action in state['sequence']):raise ValueError('invalid snapshot sequence')
        for key,value in state.items():
            if key not in ('schema','water','committed'):setattr(obj,key,copy.deepcopy(value))
        obj.committed={tuple(v) for v in state['committed']}
        return obj
