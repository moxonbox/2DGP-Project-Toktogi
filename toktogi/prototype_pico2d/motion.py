"""Timed sprite tracks and the playable pose policy."""
from bisect import bisect_right
from itertools import accumulate
from math import isfinite, degrees

class Track:
    def __init__(self, cells, durations, loop):
        self.cells = tuple(cells)
        self.durations = tuple(durations)
        if not self.cells or len(self.cells)!=len(self.durations) or any(
                not isfinite(d) or d<=0 for d in self.durations):
            raise ValueError('A motion track needs a positive finite duration for every cell.')
        self.ends = tuple(accumulate(self.durations))
        self.duration = self.ends[-1]
        if not isfinite(self.duration):
            raise ValueError('Motion track duration overflowed.')
        self.loop = loop

    @classmethod
    def from_clip(cls,name,view,clip):
        return cls(((name,view,i) for i in range(len(clip['samples']))),
                   (s['duration_s'] for s in clip['samples']),clip['loop'])

    def index(self, seconds):
        t = max(0., seconds)+1e-9
        if self.loop:
            t %= self.duration
        return min(len(self.cells)-1,bisect_right(self.ends,t))

    def start(self, index):
        return self.ends[index-1] if index else 0.


def validate_playable(assets):
    if assets.groom is None:
        raise ValueError('Required 06–07 groom sequence is missing.')
    bindings=assets.manifest['visual_bindings']
    phases=bindings['walk_stop_by_sample'],bindings['recovery_jump_by_sample']
    dual=('idle walk walk_start aim_up aim_down aim_return_up aim_return_down jump_pre '
          'jump_release elastic_release air_rise air_apex air_fall fall_unlaunched '
          'fall_unlaunched_charged land_soft land_hard recovery_walk recovery_start '
          'feed_pre feed_cycle attack_demo hit_ground hit_air goal failed respawn').split()
    for view,other in (('left','right'),('right','left')):
        required=[(clip,view) for clip in dual]
        required.extend((clip,view) for clips in phases for clip in clips)
        suffix='_right' if view=='right' else ''
        required.extend((clip+suffix,view) for clip in ('interact_activate','interact_collect'))
        required.append((f'turn_{view}_{other}',view))
        if view=='left' and assets.poses.get('revision')=='framework-r1':
            required.append((bindings['full_turn']['ccw'],view))
        for key in required:
            if key not in assets.tracks:
                raise ValueError(f'Required motion is missing: {key}')
        if any(len(clips)!=len(assets.tracks['walk',view].cells) for clips in phases):
            raise ValueError(f'Incomplete walk phase bindings: {view}')
        profiles=['flight_roll_'+view]
        if view!='left' or assets.poses.get('revision')!='framework-r1':profiles.append('ground_spin_'+view)
        profiles.extend(f'cancel_{clip}_{i}_{view}' for clip,_,i in assets.groom.cells)
        for clip in ('land_soft','land_hard'):
            for i in range(len(assets.tracks[clip,view].cells)):
                name=f'jump_{clip}_{view}_{i}'
                profiles.extend((name,name+'_'+other))
        for edge in ('left','right'):
            profiles.extend(f'edge_{edge}_{view}{aim}' for aim in ('','_aim_up','_aim_down'))
        for name in profiles:
            if name not in assets.pose_tracks:
                raise ValueError(f'Required pose profile is missing: {name}')


class MotionSet:
    def __init__(self,assets):
        self.assets=assets
        self.bindings=assets.manifest['visual_bindings']
        self.playback={}
        for view in ('left','right'):
            for clip in ('jump_release','elastic_release'):
                track=assets.tracks[clip,view]
                if len(track.cells)<3:
                    raise ValueError(f'{clip}/{view} needs at least three cells.')
                durations=list(track.durations)
                durations[2]=.1
                self.playback[clip,view]=Track(track.cells,durations,False)
            spin=assets.pose_tracks.get('ground_spin_'+view)
            if spin is None:
                spin=assets.tracks[self.bindings['full_turn']['ccw'],view]
            self.playback['ground_spin',view]=Track(spin.cells,[.025]*len(spin.cells),False)
            roll=assets.pose_tracks['flight_roll_'+view]
            if len(roll.cells)!=17:
                raise ValueError(f'flight_roll_{view} needs 17 cells for its pose timing.')
            # Each side and the inverted pose get one complete 10 Hz interval.
            durations=[.003]*4+[.025]*4+[.105]+[.003]*3+[.025]*4+[.004]
            self.playback['flight_roll',view]=Track(roll.cells,durations,False)
            attack=assets.tracks['attack_demo',view]
            if len(attack.cells)<6:
                raise ValueError(f'attack_demo/{view} needs a windup and recovery around cell 4.')
            intro,recovery=attack.durations[:4],attack.durations[5:]
            durations=[.075*d/sum(intro) for d in intro]+[.1]+[(attack.duration-.175)*d/sum(recovery) for d in recovery]
            self.playback['attack_demo',view]=Track(attack.cells,durations,False)
            other='right' if view=='left' else 'left'
            name=f'turn_{view}_{other}'
            turn=assets.tracks[name,view]
            if len(turn.cells)!=20:
                raise ValueError(f'{name} needs 20 cells for its pose timing.')
            # Hold opposite support sets for one complete 10 Hz display interval.
            durations=[(.48-.20)/18]*20
            durations[9]=durations[14]=.10
            self.playback[name,view]=Track(turn.cells,durations,False)

    def track(self,clip,view):
        return self.playback.get((clip,view)) or self.assets.tracks[clip,view]

    def game_previews(self):
        for (clip,view),track in self.playback.items():
            if clip in ('jump_release','elastic_release'):
                count=len(track.cells)-int('air_rise' in self.bindings['shared_pose_transition']['destinations_by_source'].get(clip,()))
                track=Track(track.cells[:count],track.durations[:count],False)
            yield f'game_{clip}_{view}',track

    def walk_stop(self,view,gait):
        phase=self.assets.tracks['walk',view].index(gait)
        return self.bindings['walk_stop_by_sample'][phase]

    def recovery_prep(self,view,gait):
        phase=self.assets.tracks['walk',view].index(gait)
        return self.bindings['recovery_jump_by_sample'][phase]

    def groom_return(self,seconds,target):
        source=self.assets.groom.cells[self.assets.groom.index(seconds)]
        return self.assets.pose_tracks[f'cancel_{source[0]}_{source[2]}_{target}']

    def landing_prep(self,source,target):
        clip,view,sample=source
        suffix='' if view==target else '_'+target
        return self.assets.pose_tracks[f'jump_{clip}_{view}_{sample}{suffix}']

    def feed_return(self,source):
        clip,view,index=source
        warmup=self.assets.tracks['feed_pre',view].cells
        idle=('idle',view,0)
        if clip=='feed_pre':
            cells=tuple(reversed(warmup[:index+1]))
        elif clip=='feed_cycle':
            cycle=self.assets.tracks['feed_cycle',view].cells
            first=tuple(reversed(cycle[:index+1]))
            wrap=cycle[index:]+cycle[:1]
            cells=(first if len(first)<=len(wrap) else wrap)+tuple(reversed(warmup[:-1]))
        elif clip.startswith('brake'):
            cells=self.assets.tracks[clip,view].cells[index:]
        else:
            return None
        if len(cells)==1:
            return None
        return Track(cells+(idle,),[.02]*(len(cells)+1),False)

    def feed_to_attack(self,source,view):
        returning=self.feed_return(source)
        if not returning:
            return None
        feed=returning.cells
        if len(feed)>6:
            feed=feed[:1]+feed[-5:]
        attack=self.track('attack_demo',view)
        cells=feed+attack.cells[1:4]
        return Track(cells,[.075/len(cells)]*len(cells),False)

    def feed_to_work(self,source,view,clip):
        returning=self.feed_return(source)
        if not returning:
            return None
        cells=returning.cells
        if clip=='feed_pre':
            # Return to the shared pre/cycle boundary, then resume a new attempt.
            warmup=self.assets.tracks['feed_pre',view]
            if source[0]=='feed_pre':
                cells=warmup.cells[source[2]:]
            elif source[0]=='feed_cycle':
                cells=cells[:len(cells)-len(warmup.cells)]
        return Track(cells,[.02]*len(cells),False)

    def ground_turn(self,view,gait,walking,*,full=False,idle_time=0.,entry=None):
        target=view if full else 'right' if view=='left' else 'left'
        if full:
            track=self.track('ground_spin',view)
        else:
            clip='turn_left_right' if view=='left' else 'turn_right_left'
            track=self.track(clip,view)
        cells=track.cells
        durations=track.durations
        if entry:
            cells=entry.cells+cells
            durations=entry.durations+durations
        elif walking:
            stop=self.assets.tracks[self.walk_stop(view,gait),view].cells
            if full:
                # The first turn cell owns the shared neutral boundary.
                stop=stop[:-1]
            cells=stop+cells
            durations=(.024,)*len(stop)+durations
        else:
            idle=self.assets.tracks['idle',view]
            index=idle.index(idle_time)
            if index:
                back=tuple(reversed(idle.cells[1:index+1]))
                forward=idle.cells[index:]
                entry=back if len(back)<=len(forward) else forward
                cells=entry+cells
                durations=(.025,)*len(entry)+durations
        return Track(cells,durations,False),target

    def yaw_heading(self,angle):
        # Match screen left/right to the authored camera headings, then traverse Z's baked poses.
        angle=angle%360
        right=degrees(self.assets.manifest['views']['right'])
        yaw=right*(1-angle/180) if angle<=180 else -(360-right)*(angle-180)/180
        return yaw%360

    def yaw_cell(self,angle):
        track=self.track('ground_spin','left')
        return track.cells[track.index(self.yaw_heading(angle)/360*track.duration)]

    def feed_to_move(self,source):
        returning=self.feed_return(source)
        if not returning:
            return Track((source,),(.016,),False)
        # Retain an intermediate pose before locomotion without dragging the full return.
        cells=returning.cells[:-1]
        if len(cells)>3:
            cells=(cells[0],cells[len(cells)//2],cells[-1])
        return Track(cells,(.016,)*len(cells),False)

    def duration(self,clip,view,to=None):
        data=self.assets.clips[clip]
        shared=self.bindings['shared_pose_transition']['destinations_by_source']
        track=self.track(clip,view if view in data['supported_views'] else data['supported_views'][0])
        return track.duration-(track.durations[-1] if to in shared.get(clip,()) else 0.)

    def cell(self, player):
        if player.run=='Paused' and player.paused_cell is not None:
            return player.paused_cell
        if player.transition:
            track,target=player.transition
            return track.cells[track.index(player.transition_time)]
        if player.edge_pose:
            track=self.assets.pose_tracks[player.edge_pose]
            return track.cells[track.index(player.edge_time)]
        if player.flight_rotation and not player.support and player.action=='Jump':
            age=player.time-player.flight_started-player.flight_delay
            track=self.track('flight_roll',player.view)
            if 0<=age<track.duration:
                return track.cells[track.index(age)]
            if age>=track.duration and -60<=player.vy<=80:
                return ('air_apex',player.view,1)
        if player.work and (entry:=player.work.get('attack_entry')) and player.work['age']<entry.duration:
            return entry.cells[entry.index(player.work['age'])]
        if player.work and (entry:=player.work.get('entry')):
            return entry.cells[entry.index(player.work['age'])]
        if player.yaw_pose is not None and player.support and not player.prep and not player.work and player.run=='Playing':
            if not player.yaw_turning and player.was_walking and player.clip in ('walk','walk_start','recovery_walk'):
                yaw=self.yaw_heading(player.yaw_angle)
                view=min(self.assets.clips[player.clip]['supported_views'],
                         key=lambda v:abs((degrees(self.assets.manifest['views'][v])-yaw+180)%360-180))
                track=self.track(player.clip,view)
                return track.cells[track.index(player.visual_time)]
            return player.yaw_pose
        if player.clip=='groom':
            track=self.assets.groom
            return track.cells[track.index(player.visual_time)]
        views=self.assets.clips[player.clip]['supported_views']
        track=self.track(player.clip,player.view if player.view in views else views[0])
        return track.cells[track.index(player.visual_time)]

