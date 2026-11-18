"""Fixed-step platformer rules. Animation reads simulation state and never moves the player."""
from math import ceil, copysign, cos, floor, hypot, isfinite, radians
from course import COURSE, BEACON, BEACON_TOUCH, CHECKPOINT, COLLECT, COLLECT_TOUCH, FOOD, FOOD_TOUCH, LEVEL, SHELL, Platform
from physics import STEP, GRAVITY, CAP_RADIUS, CAP_HEIGHT, approach, capsule_overlaps, overhang, segment_box, sweep_x, sweep_y
from motion import MotionSet, Track, validate_playable
from world import World

JUMP_SPEED = 426
ELASTIC_SPEED = 541
WALK_SPEED = 24.
POST_WINDOW = .165
PRE_WINDOW = .10


ATTACK_ACTIVE = (.078,.162)
YAW_DETENT_SECONDS = .10


class Game:
    def __init__(self,assets,course=COURSE,*,world=None,walk_speed=WALK_SPEED,directional_yaw=False):
        if not isfinite(walk_speed) or walk_speed<=0:raise ValueError('Walk speed must be positive and finite.')
        self.walk_speed=float(walk_speed)
        self.directional_yaw=directional_yaw
        self.assets = assets
        validate_playable(assets)
        self.motion = MotionSet(assets)
        self.world = world if world is not None else World(course)
        self.pond=None
        course = self.course
        starts = ((course.spawn_x,self.world.spawn_platform),
                  *((c.point[0],c.platform) for c in self.world.checkpoints))
        for x,platform in starts:
            self.x,self.view,self.support=x,'right',platform
            if not self.stable_feet(assets.tracks['idle','right']):
                raise ValueError('Course spawn and checkpoint need room for a supported idle pose.')
            if any(capsule_overlaps(p,x,platform.y) for p in course.platforms if p is not platform):
                raise ValueError('Course spawn and checkpoint must clear other solid platforms.')
        self.reset()

    @property
    def course(self):
        return self.world.course

    @course.setter
    def course(self,value):
        self.world.rebind_legacy(value)

    @property
    def food(self):
        return self.world.value('food')

    @food.setter
    def food(self,value):
        self.world.set_value('food',value)

    @property
    def beacon(self):
        return self.world.value('beacon')

    @beacon.setter
    def beacon(self,value):
        self.world.set_value('beacon',value)

    @property
    def shell(self):
        return self.world.value('shell')

    @shell.setter
    def shell(self,value):
        self.world.set_value('shell',value)

    @property
    def collected(self):
        return self.world.value('collect')

    @collected.setter
    def collected(self,value):
        self.world.set_value('collect',value)

    def reset(self, checkpoint=False):
        self.support,(self.x,self.y) = self.world.reset(checkpoint)
        self.vx=self.vy=0.
        self.time=self.recovery=self.goal_hold=0.
        self.held=set()
        self.view='right'
        self.yaw_angle=0.
        self.yaw_pose=None
        self.yaw_turning=False
        self.yaw_detent_until=0.
        self.yaw_detent_direction=0
        self.aim=0
        self.aim_time=0.
        self.run='Playing'
        self.action='Idle'
        self.clip='idle'
        self.visual_time=0.
        self.gait=0.
        self.stride=self.assets.clips['walk']['gait_reference']['visual_speed_model_units_s']*.48/self.assets.manifest['coordinate_contract']['world_units_per_pixel']
        self.transition=None
        self.transition_kind=None
        self.turn_origin=None
        self.turn_path=None
        self.turn_foot_offsets=None
        self.full_turn=False
        self.pending_work=None
        self.transition_time=0.
        self.edge_pose=None
        self.edge_time=0.
        self.jump_source=None
        self.pending_jump=False
        self.flight_started=None
        self.flight_delay=0.
        self.flight_rotation=False
        self.paused_cell=None
        self.balancing=False
        self.prep=None
        self.work=None
        self.elastic_at=None
        self.offer=None
        self.space_pressed=False
        self.was_walking=False
        self.launched=False
        self.launch_count=self.elastic_count=self.bites=self.attack_hits=0
        self.checkpoint=checkpoint
        self.hurt_until=0.
        self.hit_until=0.
        self.reject_until=0.
        self.notice='발판을 올라 꼭대기 등불까지 도달하세요.'
        self.notice_until=4.
        if checkpoint:
            self.set_clip('respawn')
        if self.pond:self.pond.reset()

    def duration(self,clip,to=None):
        return self.motion.duration(clip,self.view,to)

    def tell(self,text):
        self.notice=text
        self.notice_until=self.time+2.7

    def set_clip(self,name,time=0.):
        self.clip=name
        self.visual_time=time

    def visual(self):
        return self.motion.cell(self)

    def cancel_work(self):
        if self.work and self.work.get('entry') and self.support:
            track=self.motion.feed_return(self.visual())
            if track:
                self.transition=(track,self.view)
                self.transition_kind='feed_return'
                self.transition_time=0.
        elif self.work and self.work['stage']=='groom' and self.work['age']<self.assets.groom.duration and self.support:
            direction=int('right' in self.held)-int('left' in self.held)
            target=('right' if direction>0 else 'left') if direction else self.view
            self.transition=(self.motion.groom_return(self.visual_time,target),target)
            self.transition_kind='groom_return'
            self.transition_time=0.
            self.turn_origin=None
        if self.work:self.was_walking=False
        self.work=None
        if self.action in ('Interact','Combat'):
            self.action='Idle'
            self.set_clip('idle')

    def close_input(self,preserve_pose=False):
        self.held.clear()
        self.space_pressed=False
        self.elastic_at=None
        self.prep=None
        if preserve_pose and self.work and self.work['key']=='f' and self.support:
            self.end_work()
        else:
            self.cancel_work()
        if not preserve_pose:
            self.transition=None
            self.turn_origin=None
        self.pending_work=None
        self.pending_jump=False
        self.edge_pose=None
        self.was_walking=False
        if self.run in ('Playing','Paused'):
            self.action='Idle'
            if self.support:self.set_clip('idle')

    def pause(self):
        if self.run=='Playing':
            self.paused_cell=self.visual()
            self.close_input(preserve_pose=True)
            self.run='Paused'
        elif self.run=='Paused':
            self.run='Playing'
            self.paused_cell=None

    def edge(self,key,down):
        if self.run!='Playing':
            return
        if down:
            if key in self.held:
                return
            self.held.add(key)
        else:
            if key not in self.held:
                return
            self.held.remove(key)
        if key=='space':
            if down:
                self.jump_source=(self.visual(),self.time)
                self.pending_jump=False
                self.pending_work=None
                self.space_pressed=True
                self.elastic_at=None
                self.prep=None
                self.cancel_work()
                if not self.turn_origin:
                    self.transition=None
                self.edge_pose=None
                if self.time>=self.hurt_until:
                    self.action='Idle'
                    if self.support:self.set_clip('idle')
            elif self.space_pressed:
                self.space_pressed=False
                if self.transition and self.turn_origin:
                    self.pending_work=None
                    self.pending_jump=True
                    return
                self.jump_request()
        elif down and key in ('e','f','g','x','q','z'):
            self.start_work(key)
        elif not down and self.work and self.work['key']==key and key in ('f','g'):
            self.end_work()

    def jump_request(self):
        if self.time<self.hurt_until:
            return
        self.cancel_work()
        self.transition=None
        self.turn_origin=None
        self.edge_pose=None
        self.action='Jump'
        if self.support is None:
            self.elastic_at=self.time
            return
        direction=int('right' in self.held)-int('left' in self.held)
        if direction:self.view='right' if direction>0 else 'left'
        self.aim=int('up' in self.held)-int('down' in self.held)
        bonus = self.offer is not None and self.offer[0] is self.support and self.time-self.offer[1]<=POST_WINDOW
        self.request_prep(bonus)

    def request_prep(self,bonus):
        recovery=self.recovery>0 and not bonus
        self.prep=(self.time+(.045 if bonus else .08),self.support,self.vx,bonus,recovery,self.aim,self.view)
        self.action='Jump'
        self.set_clip(self.motion.recovery_prep(self.view,self.gait) if recovery else 'jump_pre')
        source,when=self.jump_source or (('idle',self.view,0),-1.)
        immediate=self.time-when<=STEP+1e-9
        if immediate and source[0] in ('land_soft','land_hard'):
            track=self.motion.landing_prep(source,self.view)
            self.transition=(track,self.view)
            self.transition_kind='landing_prep'
            self.transition_time=0.
            self.prep=(self.time+track.duration,*self.prep[1:])
        elif recovery and not (immediate and source[0] in ('walk','recovery_walk')):
            self.set_clip('jump_pre')
        self.jump_source=None
        self.was_walking=False

    def launch(self):
        _,surface,speed,bonus,recovery,aim,view=self.prep
        self.prep=None
        self.transition=None
        self.turn_origin=None
        if self.support is not surface:
            return
        self.offer=None
        self.elastic_at=None
        self.support=None
        self.launched=True
        self.recovery=0.
        self.launch_count+=1
        self.flight_started=self.time
        self.flight_rotation=not recovery
        if bonus:
            self.elastic_count+=1
            self.tell('탄성 도약 성공')
        direction = -1 if view=='left' else 1
        power= .82 if recovery else 1.
        kick = 148 + (20 if bonus else 0) - aim*29
        self.vx=speed+direction*kick*power
        self.vy=-(ELASTIC_SPEED if bonus else JUMP_SPEED)*power-aim*21
        self.action='Jump'
        self.set_clip('elastic_release' if bonus else 'jump_release')
        self.flight_delay=self.duration(self.clip,'air_rise')

    def nearby(self,point,reach):
        return abs(self.y-point[1])<3 and abs(self.x-point[0])<=reach

    def in_reach(self,point,guide,reach):
        delta = point[0]-self.x
        return self.nearby(point,reach) and (abs(delta)<10 or (delta>0)==(guide=='right'))

    def socket(self,clip,seconds,marker):
        key=(clip,self.view,self.assets.tracks[clip,self.view].index(seconds))
        xy=self.assets.sample(key)[0][marker]['xy']
        px,py=self.assets.pivot
        return self.x+xy[0]-px,self.y+xy[1]-py

    def work_contact(self,clip,target,seconds):
        marker='mouth_marker' if clip=='feed_cycle' else 'interaction_work_socket_RF' if self.view=='right' else 'interaction_work_socket'
        return hypot(*(p-q for p,q in zip(self.socket(clip,seconds,marker),target)))<=3.5

    def stance_range(self):
        markers,legs=self.assets.sample(('idle',self.view,0))
        offsets=[markers['foot_contact_'+leg]['xy'][0]-self.assets.pivot[0] for leg in legs]
        return self.support.x0-min(offsets)+1,self.support.x1-max(offsets)-1

    def work_candidate(self,key):
        """Use the same admission check for input and the ready color."""
        suffix='_right' if self.view=='right' else ''
        activate,collect='interact_activate'+suffix,'interact_collect'+suffix
        target=None
        if key in ('f','e'):
            choices=(('food','feed_cycle','feed_pre',.22),) if key=='f' else (
                ('beacon',activate,activate,.20),('collect',collect,collect,.20))
            for kind,contact,clip,seconds in choices:
                target=next((e for e in self.world.targets(kind)
                             if (bool(self.world.states[e.key]) if kind=='food' else not self.world.states[e.key])
                             and self.work_contact(contact,e.touch,seconds)),None)
                if target is not None:
                    break
            if target is None:
                return None,None,'대상 가까이에서 방향과 지지를 확인하세요.'
            target=target.kind if self.world.legacy else target.key
            tracks=(self.assets.tracks[name,self.view] for name in ('feed_pre','feed_cycle')) if key=='f' else (self.assets.tracks[clip,self.view],)
        elif key=='g':
            if self.view!='left' or not self.stable_feet(self.assets.groom):
                return None,None,'넓은 발판에서 왼쪽을 향하면 손질할 수 있습니다.'
            return 'groom',None,None
        elif key=='x':
            clip='attack_demo'
            tracks=(self.assets.tracks[clip,self.view],)
        else:
            return None,None,'대상 가까이에서 방향과 지지를 확인하세요.'
        if not all(self.stable_feet(track) for track in tracks):
            return None,None,'작업 자세를 지지할 넓은 발판이 필요합니다.'
        return clip,target,None

    def ready_work(self):
        if (self.run!='Playing' or not self.support or self.prep or
                self.transition and self.transition_kind!='feed_return' or
                self.time<self.hurt_until or self.work and self.work['key']=='x'):
            return set()
        return {target for key in ('f','e') if (target:=self.work_candidate(key)[1])}

    def reject(self,text):
        self.tell(text)
        self.reject_until=self.time+.18

    def start_work(self,key):
        if not self.support or self.prep or self.time<self.hurt_until:
            self.reject('지지한 상태에서 작업할 수 있습니다.')
            return
        if self.work and self.work['key']=='x':
            self.reject('공격이 끝난 뒤 작업할 수 있습니다.')
            return
        if self.transition and (self.transition_kind!='feed_return' or key in ('q','z')):
            self.pending_jump=False
            self.pending_work=key
            return
        if key in ('q','z'):
            full=key=='z'
            if full and (self.work or self.clip not in ('idle','walk','recovery_walk') or self.edge_pose):
                self.reject('안정된 대기 또는 보행 자세에서 회전할 수 있습니다.')
                return
            if not self.try_turn(full=full):
                self.reject('회전 자세를 지지할 넓은 발판이 필요합니다.')
                return
            if full:
                self.vx=0.
                self.action='Idle'
            return
        clip,target,reason=self.work_candidate(key)
        if reason:
            self.reject(reason)
            return
        from_feed=(self.work and self.work['key']=='f' or
                   self.transition and self.transition_kind=='feed_return')
        attack_entry=self.motion.feed_to_attack(self.visual(),self.view) if key=='x' and from_feed else None
        source=self.visual()
        entry=self.motion.feed_to_work(source,self.view,clip) if key in ('f','g') and from_feed else None
        if entry and key=='f' and source[0] in ('feed_pre','feed_cycle'):
            clip='feed_cycle'
        self.transition=None
        self.turn_origin=None
        self.pending_work=None
        self.edge_pose=None
        self.work={'key':key,'stage':clip,'age':0.,'started_at':self.time,'position':(self.x,self.y),'committed':False,
                   'target':self.world.entity(target).key if target is not None else None}
        if attack_entry:
            self.work['attack_entry']=attack_entry
        if entry:
            self.work['entry']=entry
        if self.clip in ('walk','recovery_walk') and self.was_walking:
            self.work.update(stage=self.motion.walk_stop(self.view,self.gait),next=clip)
        self.was_walking=False
        self.action='Combat' if key=='x' else 'Interact'
        self.set_clip(self.work['stage'])

    def foot_offsets(self,track):
        return [markers['foot_contact_'+leg]['xy'][0]-self.assets.pivot[0]
                for cell in track.cells for markers,legs in (self.assets.sample(cell),) for leg in legs]

    def stable_feet(self,track):
        return all(self.support.x0<=self.x+offset<=self.support.x1 for offset in self.foot_offsets(track))

    def try_turn(self,*,full=False,entry=None):
        turn=self.motion.ground_turn(self.view,self.gait,self.was_walking,full=full,entry=entry,
                                     idle_time=self.visual_time if self.clip=='idle' else 0.)
        offsets=self.foot_offsets(turn[0])
        if not all(self.support.x0<=self.x+offset<=self.support.x1 for offset in offsets):
            return False
        self.cancel_work()
        self.transition=turn
        self.transition_kind='turn'
        self.turn_origin=self.view
        self.turn_path=turn[0]
        self.turn_foot_offsets=(min(offsets,default=0.),max(offsets,default=0.))
        self.transition_time=0.
        self.full_turn=full
        self.edge_pose=None
        return True

    def steer_yaw(self,dt):
        if not self.directional_yaw:return
        if (not self.support or self.prep or self.work or self.transition or self.time<self.hurt_until
                or self.clip not in ('idle','walk','walk_start','recovery_walk','aim_up','aim_down',
                                     'aim_return_up','aim_return_down') and not self.clip.startswith('brake')):
            self.yaw_angle=0. if self.view=='right' else 180.
            self.yaw_pose=None
            self.yaw_turning=False
            self.yaw_detent_until=0.
            self.yaw_detent_direction=0
            return
        self.yaw_turning=False
        if 'shift' in self.held:return
        if self.yaw_pose is None:
            self.yaw_angle=360*(self.yaw_angle//360)+(0. if self.view=='right' else 180.)
        x=int('right' in self.held)-int('left' in self.held)
        y=int('up' in self.held)-int('down' in self.held)
        step=dt*360/self.motion.track('ground_spin','left').duration
        horizontal='left' in self.held or 'right' in self.held
        if x!=self.yaw_detent_direction:self.yaw_detent_until=0.
        detent=False
        if horizontal:
            if not x:return
            if self.time+1e-9<self.yaw_detent_until:
                angle=self.yaw_angle
            else:
                angle=self.yaw_angle+x*step
                boundary=180*(floor((self.yaw_angle+1e-7)/180)+1 if x>0 else ceil((self.yaw_angle-1e-7)/180)-1)
                if x*(angle-boundary)>=-1e-7:
                    angle=boundary
                    detent=True
        else:
            if not y:return
            target=90. if y>0 else 270.
            delta=(target-self.yaw_angle+180)%360-180
            if delta==-180:delta=180
            angle=self.yaw_angle+copysign(min(abs(delta),step),delta)
        pose=self.motion.yaw_cell(angle)
        markers,legs=self.assets.sample(pose)
        if not all(self.support.x0<=self.x+markers['foot_contact_'+leg]['xy'][0]-self.assets.pivot[0]<=self.support.x1 for leg in legs):return
        if detent:
            self.yaw_detent_until=self.time+YAW_DETENT_SECONDS
            self.yaw_detent_direction=x
        self.yaw_turning=horizontal or abs((target-angle+180)%360-180)>1e-7
        self.yaw_angle=angle
        facing=cos(radians(angle))
        if abs(facing)>1e-7:self.view='right' if facing>0 else 'left'
        # The brief half-turn detent holds this pose; continued input resumes the same sequence.
        self.yaw_pose=pose

    def end_work(self):
        if self.work and self.work['key']=='f' and self.support:
            track=self.motion.feed_return(self.visual())
            self.cancel_work()
            self.transition=(track,self.view) if track else None
            self.transition_kind='feed_return'
            self.transition_time=0.
            self.turn_origin=None
        else:
            self.cancel_work()

    def work_tick(self,dt):
        task=self.work
        target=self.world.entity(task['target']) if task['target'] is not None else None
        key,stage=task['key'],task['stage']
        previous=task['age']
        old_position=task['position']
        task['position']=(self.x,self.y)
        task['age']=max(0.,self.time-task['started_at'])
        age=task['age']
        self.visual_time=age
        if entry:=task.get('entry'):
            if age+1e-9>=entry.duration:
                task.pop('entry')
                task.update(age=0.,started_at=self.time)
                self.set_clip(stage)
            return
        if task.get('next'):
            if age+1e-9>=self.duration(stage):
                task.update(stage=task.pop('next'),age=0.,started_at=self.time)
                self.set_clip(task['stage'])
            return
        if key=='f' and (not self.world.states[target.key] or not self.work_contact('feed_cycle',target.touch,.22)):
            self.end_work()
            return
        if stage=='feed_cycle':
            if age+1e-9>=.22 and not task['committed']:
                task['committed']=True
                self.world.states[target.key]-=1
                self.bites+=1
                self.tell(f'섭식 · 먹이 {self.world.states[target.key]}회분 남음')
            if age+1e-9>=self.duration(stage):
                task.update(age=max(0.,age-self.duration(stage)),started_at=task['started_at']+self.duration(stage),committed=False)
                self.visual_time=task['age']
        elif key=='e' and not task['committed'] and age+1e-9>=.20:
            task['committed']=True
            if stage.startswith('interact_activate') and self.work_contact(stage,target.touch,age):
                self.world.states[target.key]=True
                self.tell('중간 등불을 켰습니다.')
                if self.world.landed(self.support):self.checkpoint=True
            if stage.startswith('interact_collect') and self.work_contact(stage,target.touch,age):
                self.world.states[target.key]=True
                self.tell('잎 위의 씨앗을 수집했습니다.')
        elif key=='x' and not task['committed']:
            start,end=max(previous,ATTACK_ACTIVE[0]),min(age,ATTACK_ACTIVE[1])
            if start<end:
                # Fixed two-direction game trajectory; display view/scale does not set hits.
                direction=-1 if self.view=='left' else 1
                def point(t):
                    u=(t-ATTACK_ACTIVE[0])/(ATTACK_ACTIVE[1]-ATTACK_ACTIVE[0])
                    fraction=(t-previous)/(age-previous)
                    x=old_position[0]+(self.x-old_position[0])*fraction
                    y=old_position[1]+(self.y-old_position[1])*fraction
                    return x+direction*(29.55-.55*u),y-11.66-7.92*min(1,u*2)
                for target in self.world.targets('shell'):
                    x,y=target.point
                    box=(x-19,y-18,x+19,y+3)
                    if self.world.states[target.key] and segment_box(point(start),point(end),box,include_end=end<ATTACK_ACTIVE[1]):
                        task['committed']=True
                        task['target']=target.key
                        self.attack_hits+=1
                        self.world.states[target.key]=False
                        self.tell('가시 껍질을 부쉈습니다.')
                        break
                if not task['committed'] and self.pond and self.pond.counter(self,point(start),point(end)):
                    task['committed']=True
                    self.attack_hits+=1
                    self.tell('물고기를 물러나게 했습니다.')
        duration=self.assets.groom.duration if stage=='groom' else self.duration(stage,'feed_cycle' if stage=='feed_pre' else None)
        if age+1e-9>=duration and stage!='feed_cycle':
            if stage=='feed_pre':
                task.update(stage='feed_cycle',age=0.,started_at=self.time,committed=False)
                self.set_clip('feed_cycle')
            else:
                self.cancel_work()
                self.set_clip('idle')

    def hit(self,target=None):
        name='hit_ground' if self.support else 'hit_air'
        self.cancel_work()
        self.transition=None
        self.turn_origin=None
        self.pending_work=None
        self.pending_jump=False
        self.flight_rotation=False
        self.edge_pose=None
        self.prep=None
        self.offer=None
        self.hurt_until=self.time+.36
        self.hit_until=self.time+.85
        self.vx=-160 if self.x<(target.point[0] if target is not None else self.course.shell[0]) else 160
        self.vy=-165
        self.support=None
        self.set_clip(name)
        self.tell('가시에 부딪혔습니다. X로 껍질을 부술 수 있습니다.')

    def collide(self,dt):
        previous_x=self.x
        self.x,self.vx=sweep_x(self.course.platforms,self.x,self.y,self.vx,dt)
        before=self.support
        if before and not before.x0<=self.x<=before.x1:
            self.support=None
            earlier=self.prep is not None
            self.prep=None
            self.offer=None
            self.cancel_work()
            self.transition=None
            self.turn_origin=None
            self.pending_work=None
            self.pending_jump=False
            self.edge_pose=None
            self.launched=False
            self.action='Jump'
            self.set_clip('fall_unlaunched_charged' if earlier else 'fall_unlaunched')
        if self.support:
            return abs(self.x-previous_x)
        self.y,self.vy,contact=sweep_y(self.course.platforms,self.x,self.y,self.vy,dt)
        if contact:
            impact=self.vy
            if impact<0:
                self.vy=0.
                self.flight_rotation=False
            elif contact.x0<=self.x<=contact.x1:
                self.landing(contact,impact)
            else:
                # Rounded corner contact slides outward until the capsule clears the ledge.
                self.vx=copysign(max(40.,abs(self.vx)),self.x-(contact.x0+contact.x1)/2)
        return abs(self.x-previous_x)

    def landing(self,platform,impact):
        self.support=platform
        self.y=float(platform.y)
        self.vy=0.
        if self.action!='Idle':self.action='Jump'
        self.launched=False
        self.flight_rotation=False
        self.transition=None
        self.turn_origin=None
        self.pending_work=None
        self.edge_pose=None
        self.recovery=.27 if impact>370 else .19
        self.set_clip('land_hard' if impact>370 else 'land_soft')
        self.offer=(platform,self.time) if platform.kind=='elastic' else None
        if self.world.landed(platform):
            self.checkpoint=True
        if self.offer and self.elastic_at is not None and self.time-self.elastic_at<=PRE_WINDOW and self.time>=self.hurt_until:
            direction=int('right' in self.held)-int('left' in self.held)
            if direction:self.view='right' if direction>0 else 'left'
            self.aim=int('up' in self.held)-int('down' in self.held)
            self.request_prep(True)
        self.elastic_at=None

    def step(self,dt=STEP,on_input=None):
        previous=(self.x,self.y)
        epoch=self.world.run_epoch
        playing=self.run=='Playing'
        self._step(dt,on_input)
        if playing and self.run=='Playing' and self.world.run_epoch==epoch:
            self.world.advance(previous,(self.x,self.y))
            if self.pond:self.pond.step(self,dt)

    def _step(self,dt=STEP,on_input=None):
        if self.run=='Paused':
            return
        self.visual_time+=dt
        if self.run=='Playing':self.time+=dt
        if self.transition:
            self.transition_time+=dt
            if self.transition_time+1e-9>=self.transition[0].duration and not self.prep:
                self.view=self.transition[1]
                self.transition=None
                self.turn_origin=None
                self.was_walking=False
                self.set_clip('idle')
                if self.pending_jump:
                    self.pending_jump=False
                    self.jump_source=None
                    self.jump_request()
                key=self.pending_work
                self.pending_work=None
                if key and (key not in ('f','g') or key in self.held):
                    self.start_work(key)
        if self.edge_pose:self.edge_time+=dt
        if self.run!='Playing':
            return
        self.recovery=max(0.,self.recovery-dt)
        if self.offer and self.time-self.offer[1]>POST_WINDOW:
            self.offer=None
        direction=int('right' in self.held)-int('left' in self.held)
        if self.transition and self.turn_origin and direction and not self.full_turn:
            target='right' if direction>0 else 'left'
            if target!=self.transition[1]:
                track=self.transition[0]
                index=track.index(self.transition_time)
                current=track.cells[index]
                original=self.turn_path
                index=original.cells.index(current) if current in original.cells else 0
                if target==self.turn_origin:
                    cells=tuple(reversed(original.cells[:index+1]))+(('idle',target,0),)
                else:
                    cells=original.cells[index:]
                self.transition=(Track(cells,[.024]*len(cells),False),target)
                self.transition_time=0.
        aim=int('up' in self.held)-int('down' in self.held)
        old_aim=self.aim
        if self.support and not self.prep:
            self.aim=aim
        self.aim_time=self.aim_time+dt if self.aim==old_aim else 0.
        braking='shift' in self.held
        self.balancing=False
        if (self.support and not direction and not self.work and not self.prep and not self.held
                and not self.transition and self.time>=self.hurt_until):
            lo,hi=self.stance_range()
            if lo<=hi and (self.x<lo-.2 or self.x>hi+.2):
                direction=1 if self.x<lo else -1
                self.balancing=True
        self.steer_yaw(dt)
        if self.support and self.time>=self.hurt_until and not self.prep:
            landing_pose=self.clip in ('land_soft','land_hard','recovery_start','respawn') and self.visual_time<self.duration(self.clip)
            move_entry=None
            if direction and not braking and self.transition and self.transition_kind=='feed_return':
                move_entry=self.motion.feed_to_move(self.visual())
                self.transition=None
                self.set_clip('idle')
            if direction and not self.work and not self.transition and not landing_pose:
                target='right' if direction>0 else 'left'
                turned=not self.directional_yaw and target!=self.view and self.try_turn(entry=move_entry)
                if move_entry and not turned:
                    self.transition=(move_entry,self.view)
                    self.transition_kind='feed_move'
                    self.transition_time=0.
            spinning=self.transition and self.turn_origin and self.full_turn
            speed=direction*self.walk_speed*(2. if 'run' in self.held else 1.)*(.55 if self.recovery else 1.) if not self.work and not braking and not spinning else 0.
            if self.balancing:
                speed=direction*min(abs(speed),abs((lo if direction>0 else hi)-self.x)/dt)
            reversing=self.walk_speed!=WALK_SPEED and self.vx*speed<0
            self.vx=approach(self.vx,speed,dt*(1700 if braking or reversing else 760 if speed else 1200))
            if self.transition and self.turn_origin:
                lo,hi=self.turn_foot_offsets
                end=self.x+self.vx*dt
                if not (self.support.x0<=end+lo and end+hi<=self.support.x1):
                    self.vx=0.
        moved=self.collide(dt)
        left,right,bottom=self.course.fail_bounds
        if self.y>bottom or self.x<left or self.x>right:
            self.run='Failed'
            self.close_input()
            self.set_clip('failed')
            return
        if self.time>=self.hit_until:
            for target in self.world.targets('shell'):
                if self.world.states[target.key] and abs(self.x-target.point[0])<19 and abs(self.y-target.point[1])<10:
                    self.hit(target)
                    break
        if on_input is not None:
            on_input()
            requested=int('right' in self.held)-int('left' in self.held)
            if requested or not self.balancing or self.held:direction=requested
            braking='shift' in self.held
        if self.prep and self.time+1e-9>=self.prep[0]:
            self.launch()
        if self.support and self.work:
            if self.work['key']=='g' and not self.stable_feet(self.assets.groom):
                self.cancel_work()
            else:
                self.work_tick(dt)
        if (self.support and self.support.kind=='goal' and self.world.level_id==self.world.final_level_id
                and self.world.goal_ready() and abs(self.vx)<1 and self.course.goal_span[0]<self.x<self.course.goal_span[1]):
            self.goal_hold+=dt
            if self.goal_hold>=.20:
                self.run='Cleared'
                self.world.completed_stages.add(self.world.stage_id)
                self.close_input()
                self.set_clip('goal')
                return
        else:
            self.goal_hold=0.
        if self.prep or self.work:
            return
        if self.transition:
            self.was_walking=False
            spinning=self.turn_origin and self.full_turn
            self.action='Walk' if not spinning and (direction or 'left' in self.held and 'right' in self.held) else 'Idle'
            return
        if not self.support:
            if self.action!='Idle':self.action='Jump'
            if self.time<self.hurt_until:
                return
            if self.clip in ('jump_release','elastic_release') and self.visual_time<self.duration(self.clip,'air_rise'):
                return
            if self.clip in ('fall_unlaunched','fall_unlaunched_charged') and self.visual_time<self.duration(self.clip):
                return
            name='air_rise' if self.vy<-38 else 'air_apex' if self.vy<42 else 'air_fall'
            if self.clip!=name:
                self.set_clip(name)
            return
        if self.clip in ('land_soft','land_hard'):
            if self.visual_time<self.duration(self.clip,'recovery_start'):
                return
            self.set_clip('recovery_start')
        if self.clip in ('recovery_start','respawn') and self.visual_time<self.duration(self.clip):
            return
        if self.action=='Jump' and not direction:
            self.set_clip('recovery_start',self.duration('recovery_start'))
            return
        walking = moved>.015 and bool(direction) and not braking
        if walking and self.edge_pose and direction!=(-1 if self.view=='left' else 1):
            # Walk inward on the remaining stance until the turn is supported.
            self.action='Walk'
            return
        if not walking and not self.was_walking and self.clip in ('idle','aim_up','aim_down'):
            lo,hi=self.stance_range()
            name='edge_'+('left' if self.x<lo else 'right')+'_'+self.view if self.x<lo or self.x>hi else None
            if name and self.aim:name+='_aim_'+('up' if self.aim>0 else 'down')
            if name!=self.edge_pose:self.edge_pose=name;self.edge_time=0.
        else:self.edge_pose=None
        if walking:
            self.action='Walk'
            self.gait=(self.gait+moved*.48/self.stride)%.48
            if not self.was_walking and not self.recovery:
                self.set_clip('walk_start')
            elif self.clip!='walk_start' or self.visual_time>=self.duration('walk_start'):
                self.set_clip('recovery_walk' if self.recovery else 'walk',self.gait)
        elif self.was_walking:
            self.set_clip(self.motion.walk_stop(self.view,self.gait))
        elif self.clip.startswith('brake') and self.visual_time<self.duration(self.clip):
            pass
        else:
            self.action='Walk' if 'left' in self.held and 'right' in self.held else 'Idle'
            if self.recovery and self.clip in ('land_soft','land_hard','recovery_start'):
                name='recovery_start'
            elif self.aim:
                name='aim_up' if self.aim>0 else 'aim_down'
            elif old_aim:
                name='aim_return_up' if old_aim>0 else 'aim_return_down'
            elif self.clip.startswith('aim_return') and self.visual_time<self.duration(self.clip):
                name=self.clip
            else:
                name='idle'
            if self.clip!=name:
                self.set_clip(name)
        self.was_walking=walking
