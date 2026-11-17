"""Native render boards, replay evidence and a local-file motion inspector."""
import json,math,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runtime'))
from fish_bundle import FishBundle
from fish_sim import FishSim
from fish_renderer import FishRenderer
from motion_spec import VARIANTS,DESIGNS,PIXELS_PER_BU as PX
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
SMALL=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)

def write_board():
    for sex in VARIANTS:
        board=Image.new('RGB',(1280,1040),(63,72,79));draw=ImageDraw.Draw(board)
        draw.text((24,16),f'GAMBUSIA HOLBROOKI | {sex.upper()} | FINAL BLENDER GEOMETRY',font=FONT,fill='white')
        for i,view in enumerate(('front','left','right','rear','top','bottom')):
            pic=Image.open(ROOT/f'sheet/blender_{sex}/{view}.png').convert('RGBA');pic.thumbnail((420,450))
            x=(i%3)*426;y=65+(i//3)*480
            board.paste(pic,(x,y+40),pic);draw.text((x+22,y),view.upper(),font=FONT,fill='white')
        board.save(ROOT/f'sheet/blender_{sex}_sheet.png')

def main():
    write_board();bundle=FishBundle(ROOT/'2D/gambusia-r03/gambusia_holbrooki_r03.zip');renderer=FishRenderer(bundle)
    project=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parents[2]
    tok=Image.open(project/'asset/C/C011_toktogi/2D/idle/idle/left/0.png').convert('RGBA').crop((0,0,128,128))
    board=Image.new('RGBA',(1100,950),(62,73,79,255));draw=ImageDraw.Draw(board)
    for row,sex in enumerate(VARIANTS):
        cell=bundle.cell(sex,'hover_or_school','mid',0,'left');pic,offset=renderer.render(cell,sex,mode='sprite')
        y=40+row*440;board.alpha_composite(pic,(260+offset[0],y+offset[1]-120));board.alpha_composite(tok,(80,y+240))
        draw.text((24,y),f'{sex.upper()} | SL {6 if sex=="female" else 3.5} x C011 | same 71.910112 px/BU | 1x',font=FONT,fill='white')
    board.convert('RGB').save(ROOT/'comparison/c011_scale_color.png')
    ImageOps.grayscale(board).save(ROOT/'comparison/c011_scale_gray.png')
    previews=ROOT/'previews';previews.mkdir(exist_ok=True);traces={}
    for sex in VARIANTS:
        for name,seconds in (('surface',12),('breach',8),('feeding',10),('missed_water',8)):
            sim=FishSim(bundle,sex,breach_enabled=True)
            sim.start_sequence('breach' if name=='missed_water' else name,target={'id':'food','x':0,'z':0,'radius':.01*sim.sl,'resource':True} if name=='feeding' else None)
            folder=previews/'traces'/f'{sex}_{name}';folder.mkdir(parents=True,exist_ok=True)
            records=[];frames=[];missed=False
            for index in range(seconds*20):
                for tick in range(6):
                    if name=='feeding':sim.pending_target['x'],sim.pending_target['z']=sim.mouth_point()
                    if name=='missed_water' and sim.mode=='airborne' and not missed:
                        sim.vx=16*sim.sl;missed=True
                    sim.step()
                cell=sim.cell();pivot=bundle.manifest['views'][sex+'/'+sim.view]['pivot'];origin=(480-pivot[0],380-pivot[1])
                water_y=380+sim.z*PX*.9304-sim.mouth_depth_bias()*PX
                picture=Image.new('RGBA',(960,760),(58,72,76,255));d=ImageDraw.Draw(picture)
                if water_y<760:d.rectangle((0,max(0,water_y),960,760),fill=(30,66,78,255))
                if 0<water_y<760:d.line((0,water_y,960,water_y),fill=(109,166,174),width=2)
                for plant in range(-12,13,3):
                    x=480+(plant-sim.x)*PX
                    if 0<x<960:d.line((x,water_y+260,x-24,water_y+120),fill=(46,105,88),width=7)
                image,offset=renderer.render(cell,sex,root_z=sim.z,mode='sprite')
                picture.alpha_composite(image,(round(origin[0]+offset[0]),round(origin[1]+offset[1])))
                tx=round(480-sim.x*PX-64);ty=round(water_y-128)
                if -128<tx<960 and -128<ty<760:picture.alpha_composite(tok,(tx,ty))
                for e in sim.effects:
                    age=sim.time-e['time']
                    if not 0<=age<=.65 or e['kind'] not in ('ripple','exit_ripple','splash'):continue
                    x=480+(e['position'][0]-sim.x)*PX;y=380+sim.z*PX*.9304-e['position'][2]*PX
                    if e['kind']=='splash':
                        for k in range(5):
                            px=x+(k-2)*age*90;py=y-age*120+age*age*150;d.ellipse((px-2,py-2,px+2,py+2),fill=(207,233,235))
                    else:d.ellipse((x-8-age*50,y-2-age*9,x+8+age*50,y+2+age*9),outline=(166,214,218),width=2)
                label=f'{sex} / {name} | {sim.time:.2f}s | {sim.action}.{sim.phase} | {sim.mode}'
                d.rectangle((0,0,960,58),fill=(24,34,39));d.text((16,12),label,font=SMALL,fill='white')
                d.text((16,36),'1x native pixels / camera follows fish / surface mask from deformed height / recorded 120Hz physics',font=SMALL,fill=(175,203,205))
                path=folder/f'{index:03}.png';picture.save(path)
                records.append({'time':sim.time,'frame':path.relative_to(ROOT).as_posix(),'cell':cell['file'],'action':sim.action,'phase':sim.phase,'u':sim.u,'mode':sim.mode,'x':sim.x,'z':sim.z,'effects':len(sim.effects)})
                if index%2==0:frames.append(picture)
            frames[0].save(previews/f'{sex}_{name}.png',save_all=True,append_images=frames[1:],duration=100,loop=0)
            traces[f'{sex}/{name}']={'fps':20,'duration':seconds,'frames':records,'effects':sim.effects,'final':{'action':sim.action,'mode':sim.mode,'failed':sim.failed}}
            print('REVIEW',sex,name,flush=True)
    (previews/'replay_traces.json').write_text(json.dumps(traces,indent=2),encoding='utf-8')
    data={'variants':bundle.manifest['variants'],'actions':list(DESIGNS),'clips':bundle.manifest['clips'],'views':bundle.manifest['views'],'passes':bundle.manifest['passes'],'traces':traces}
    template=(ROOT/'runtime/preview_template.html').read_text(encoding='utf-8')
    (ROOT/'GambusiaMotionPreview.html').write_text(template.replace('/*REVIEW_DATA*/',json.dumps(data,separators=(',',':'))),encoding='utf-8')
    bundle.close()

if __name__=='__main__':main()
