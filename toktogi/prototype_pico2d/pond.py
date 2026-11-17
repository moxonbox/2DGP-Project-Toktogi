"""One horizontal pond test course and a deterministic, telegraphed fish hazard."""
from math import hypot, isfinite, pi, sin

from course import Course, Platform
from physics import CAP_HEIGHT, CAP_RADIUS, segment_box
from world import Level, World


def test_world():
    platforms=tuple(Platform(35+210*i,205+210*i,360,378,
                             'elastic' if i==2 else 'goal' if i==5 else 'normal') for i in range(6))
    course=Course(platforms=platforms,spawn_x=120,checkpoint_platform=2,checkpoint=(540,360),
                  food=(130,360),beacon=(339,360),collect=(545,360),shell=(900,360),
                  goal_span=(1100,1240),fail_bounds=(-68,1328,460))
    return World(course,revision='pond-test-r1',levels=(Level('pond_test','pond_stage',(-68,0,1328,460)),),
                 spawn_platform=platforms[0],spawn_level='pond_test')


class Pond:
    water_y=380.
    warning_seconds=.65
    attack_seconds=.64
    recovery_seconds=.60

    def __init__(self,world,active_span=None,water_y=380.):
        self.world=world
        if not isfinite(water_y):raise ValueError('Pond waterline must be finite.')
        self.water_y=float(water_y)
        self.active_span=active_span
        self.reset()

    def reset(self):
        self.run_epoch=self.world.run_epoch
        self.time=self.age=0.
        self.phase,self.kind='idle','peek'
        self.cycle=0
        self.next_attack=3.5
        self.target_x=self.world.course.spawn_x
        self.mouth=(self.target_x,self.water_y+40)
        self.action,self.u='water_reentry',1.
        self.hits=self.repels=0
        self.struck=self.repelled=False
        self.return_y=self.mouth[1]

    def enemy_near(self,game):
        return self.phase in ('warn','attack') and abs(game.x-self.mouth[0])<=75 and abs(game.y-self.mouth[1])<=120

    def counter(self,game,start,end):
        if game.run!='Playing' or self.phase!='attack' or self.repelled:
            return False
        x,y=self.mouth
        if not segment_box(start,end,(x-18,y-18,x+18,y+18)):
            return False
        self.repelled=True
        self.repels+=1
        self.phase,self.age='recover',0.
        self.return_y=y
        self.action,self.u='water_reentry',0.
        return True

    def step(self,game,dt):
        if game.run!='Playing':
            return
        if self.world.run_epoch!=self.run_epoch:
            self.reset()
        if not isfinite(dt) or dt<0:
            raise ValueError('Pond dt must be finite and nonnegative.')
        self.time+=dt
        if self.active_span and not self.active_span[0]<=game.x<=self.active_span[1]:
            self.phase,self.age='idle',0.
            self.next_attack=self.time+3.5
            return
        self.age+=dt
        if self.phase=='idle':
            if self.time+1e-9<self.next_attack:
                return
            self.phase,self.age='warn',0.
            self.kind='peek' if self.cycle%2==0 else 'jump'
            self.cycle+=1
            self.target_x=game.x
            self.struck=self.repelled=False
        if self.phase=='warn':
            self.u=min(1.,self.age/self.warning_seconds)
            self.action='surface_peek'
            self.mouth=(self.target_x,self.water_y+40-26*self.u)
            if self.age+1e-9<self.warning_seconds:
                return
            self.phase,self.age='attack',0.
        if self.phase=='attack':
            self.u=min(1.,self.age/self.attack_seconds)
            amplitude=50 if self.kind=='peek' else 118
            self.mouth=(self.target_x,self.water_y+18-amplitude*sin(pi*self.u))
            self.action='surface_snap' if self.kind=='peek' else (
                'breach_launch' if self.u<.2 else 'airborne_arc' if self.u<.72 else 'surface_fall')
            mx,my=self.mouth
            axis_y=max(game.y-CAP_HEIGHT+CAP_RADIUS,min(game.y-CAP_RADIUS,my))
            if not self.struck and game.time>=game.hit_until and hypot(mx-game.x,my-axis_y)<CAP_RADIUS+12:
                self.struck=True
                self.hits+=1
                game.hit()
                game.vx=-160 if game.x<=mx else 160
            if self.age+1e-9<self.attack_seconds:
                return
            self.phase,self.age='recover',0.
            self.return_y=self.mouth[1]
        if self.phase=='recover':
            self.u=min(1.,self.age/self.recovery_seconds)
            self.action='water_reentry'
            self.mouth=(self.target_x,self.return_y+(self.water_y+40-self.return_y)*self.u)
            if self.age+1e-9>=self.recovery_seconds:
                self.phase,self.age='idle',0.
                self.next_attack=self.time+3.5+1.25*(self.cycle%3)
