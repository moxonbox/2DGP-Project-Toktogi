"""Optional pond profile; reuses the game's input clock, player and collision code."""
import argparse,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from fish_bundle import FishBundle
from fish_sim import FishSim,Water
from fish_renderer import FishRenderer
from motion_spec import PIXELS_PER_BU as PX

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',type=Path,default=ROOT.parents[2]);parser.add_argument('--verify',action='store_true');parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args()
    if args.verify:
        from verify_runtime import run
        run();return
    sys.path.insert(0,str(args.project/'toktogi/prototype'))
    from app import App,pg
    from course import Course,Platform
    from play_view import FIELD
    pond=Course(platforms=(Platform(35,240,100,120),Platform(280,440,80,100),Platform(460,650,60,80,'elastic'),Platform(720,950,30,50,'goal')),
        checkpoint_platform=2,checkpoint=(530,60),food=(130,100),beacon=(360,80),collect=(570,60),shell=(780,30),goal_span=(820,930))

    class GambusiaApp(App):
        def __init__(self):
            super().__init__(course=pond)
            self.fish_bundle=FishBundle(ROOT/'2D/gambusia-r01/gambusia_holbrooki_r01.zip')
            self.fish_renderer=FishRenderer(self.fish_bundle);self.fish=FishSim(self.fish_bundle,water=Water(-6,6,0,-7),breach_enabled=True)
            self.fish.x=1.;self.effect_index=0;self.font=pg.font.SysFont('malgungothic',17);self.render_mode='relit'
            self.world=pg.Surface(self.screen.get_size())
            pg.display.set_caption('Gambusia pond · 1 표층 / 2 돌파 / 3 포획 / 4 회피 / M 암수 / L 조명')

        def origin(self):
            cell=self.fish.cell();pivot=self.fish_bundle.manifest['views'][self.fish.variant+'/'+self.fish.view]['pivot']
            return (FIELD.x+480+self.fish.x*PX-pivot[0],FIELD.y+100-self.fish.z*PX*.9304-pivot[1])

        def _event(self,event):
            if event.type==pg.KEYDOWN and self.scene=='game' and self.game.run=='Playing' and not getattr(event,'repeat',False):
                if event.key==pg.K_1:self.fish.start_sequence('surface');return
                if event.key==pg.K_2:self.fish.start_sequence('breach');return
                if event.key==pg.K_3:self.fish.start_sequence('feeding',target={'id':'toktogi','x':1000,'z':1000,'resource':False});return
                if event.key==pg.K_4:self.fish.cancel();self.fish.request('evade_or_dive');return
                if event.key==pg.K_m:
                    self.fish=FishSim(self.fish_bundle,'male' if self.fish.variant=='female' else 'female',self.fish.water,breach_enabled=True);self.effect_index=0;return
                if event.key==pg.K_l:self.render_mode='sprite' if self.render_mode=='relit' else 'relit';return
            super()._event(event)

        def step_scene(self,dt,on_input):
            super().step_scene(dt,on_input)
            if self.scene!='game' or self.game.run!='Playing':return
            target=None
            if self.fish.pending_target:
                origin=self.origin();xy=self.fish.cell()['markers']['mouth_tip']['xy']
                mx,my=origin[0]+xy[0]-FIELD.x,origin[1]+xy[1]-FIELD.y
                # Player capsule: 14px radius, 52px overall height, feet at g.y.
                nearest_y=max(self.game.y-38,min(self.game.y-14,my))
                contact=math.hypot(mx-self.game.x,my-nearest_y)<=14+.04*self.fish.sl*PX
                point=self.fish.mouth_point() if contact else (1000,1000)
                target={'id':'toktogi','x':point[0],'z':point[1],'radius':0,'resource':False}
            self.fish.step(dt,target=target)
            for effect in self.fish.effects[self.effect_index:]:
                if effect['kind']=='attack' and self.game.time>=self.game.hit_until:
                    self.game.hit();self.game.vx=-160 if self.game.x<480+self.fish.x*PX else 160
                    self.game.tell('물고기의 입에 닿았습니다.')
            self.effect_index=len(self.fish.effects)

        def draw(self):
            if self.scene!='game':super().draw();return
            camera_y=round(max(0,min(720,230-(100-self.fish.z*PX*.9304))))
            self.play_view.draw(self.world,self.game);self.screen.fill((99,108,112));self.screen.blit(self.world,(0,camera_y))
            clip=self.screen.get_clip();self.screen.set_clip(FIELD)
            water=pg.Surface((FIELD.width,FIELD.height),pg.SRCALPHA);water.fill((22,73,87,85))
            # Project the visible water-plane slice at the mouth depth; masks still use actual world Z.
            water_y=FIELD.y+100+camera_y-self.fish.mouth_depth_bias()*PX
            self.screen.blit(water,(FIELD.x,round(water_y)))
            origin=self.origin();light=self.play_view.light_at(self.game.x,self.game.y)
            image,offset=self.fish_renderer.render(self.fish.cell(),self.fish.variant,light=(light[0]-origin[0],origin[1]-light[1]),root_z=self.fish.z,mode=self.render_mode)
            self.screen.blit(pg.image.frombytes(image.tobytes(),image.size,'RGBA'),(round(origin[0]+offset[0]),round(origin[1]+offset[1]+camera_y)))
            for effect in self.fish.effects:
                age=self.fish.time-effect['time']
                if not 0<=age<=.65 or effect['kind'] not in ('ripple','exit_ripple','splash'):continue
                px=FIELD.x+480+effect['position'][0]*PX;py=FIELD.y+100+camera_y-effect['position'][2]*PX
                if effect['kind']=='splash':
                    for i in range(5):pg.draw.circle(self.screen,(190,224,227),(round(px+(i-2)*age*90),round(py-age*110+age*age*140)),2)
                else:pg.draw.ellipse(self.screen,(166,214,218),(round(px-10-age*45),round(py-3-age*8),round(20+age*90),round(6+age*16)),1)
            self.screen.blit(self.play_view.terrain,(FIELD.x,FIELD.y+camera_y))
            player_origin=(FIELD.x+round(self.game.x)-self.assets.pivot[0],FIELD.y+round(self.game.y)-self.assets.pivot[1])
            self.screen.blit(self.assets.render(self.game.visual(),'lit',player_origin,light,power=.82,ambient=.34),(player_origin[0],player_origin[1]+camera_y))
            self.screen.set_clip(clip)
            label=f'1 표층   2 돌파   3 포획   4 회피   M 암수   L 조명   P 일시정지   F2 톡토기 검사 | {self.fish.variant} · {self.fish.action}/{self.fish.phase}'
            self.screen.blit(self.font.render(label,True,(232,239,225)),(30,24));pg.display.flip()

        def run(self):
            try:super().run()
            finally:self.fish_bundle.close()

    load_start=time.perf_counter();instance=GambusiaApp();load_seconds=time.perf_counter()-load_start
    if args.smoke:
        import json
        import numpy as np
        from verify_runtime import memory_usage
        try:
            warm_start=time.perf_counter()
            for _ in range(240):instance.update(1/60);instance.draw()
            warm_seconds=time.perf_counter()-warm_start
            for i in range(12):instance.fish_renderer.render(instance.fish_bundle.cell('female','hover_or_school','mid',i/12),'female')
            timings=[]
            for _ in range(120):
                tick=time.perf_counter();instance.update(1/60);instance.draw();timings.append((time.perf_counter()-tick)*1000)
            instance._event(pg.event.Event(pg.KEYDOWN,key=pg.K_1));assert instance.fish.sequence
            for _ in range(30):instance.update(1/60)
            instance.game.pause();frozen=instance.fish.time;instance.update(.1);assert instance.fish.time==frozen
            instance.game.pause();instance.switch('viewer');frozen=instance.fish.time;instance.update(.1);assert instance.fish.time==frozen
            instance.switch('game');instance.fish.set_action('surface_snap','mid');instance.fish.age=.25
            instance.fish.pending_target={'id':'toktogi','x':1000,'z':1000,'resource':False}
            origin=instance.origin();marker=instance.fish.cell()['markers']['mouth_tip']['xy']
            instance.game.x=origin[0]+marker[0]-FIELD.x;instance.game.y=origin[1]+marker[1]-FIELD.y+26;instance.game.support=None
            before=instance.game.hit_until;instance.step_scene(1/120,lambda:None)
            assert instance.game.hit_until>before,'player capsule contact did not commit a hit'
            instance.game.reset();instance.fish=FishSim(instance.fish_bundle,water=Water(-6,6,0,-7),breach_enabled=True);instance.fish.set_action('surface_gape','mid');instance.fish.age=.6;instance.fish.z=-instance.fish.geometry()['mouth_tip'][2]+.006*instance.fish.sl
            instance.draw();pg.image.save(instance.screen,str(ROOT/'comparison/pond_game_preview.png'))
            result={'status':'PASS','driver':pg.display.get_driver(),'player_capsule_contact':True,'pause_and_F2_freeze':True,'default_game_source_modified':False,'actual_window_GPU':'NOT_RUN'}
            result['performance']={'frames':120,'p95_ms':float(np.percentile(timings,95)),'max_ms':max(timings),'mean_ms':float(np.mean(timings)),'scope':'full optional pond Game + C011 + fish + water + SDL dummy flip','meets_16_7_ms':max(timings)<=16.7}
            result['load_seconds']=load_seconds;result['warmup_seconds']=warm_seconds
            result['process_memory']=memory_usage()
            (ROOT/'document/gameplay_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
        finally:instance.assets.close();instance.fish_bundle.close();pg.quit()
    else:instance.run()

if __name__=='__main__':main()
