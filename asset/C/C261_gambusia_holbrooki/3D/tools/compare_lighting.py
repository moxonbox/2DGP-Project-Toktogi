"""Shared C011 point light, material negatives and native-pixel directional boards."""
import sys,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runtime'))
from fish_bundle import FishBundle
from fish_renderer import FishRenderer,linear
import shared_lighting
project=Path(sys.argv[1]);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
bundle=FishBundle(ROOT/'2D/gambusia-r03/gambusia_holbrooki_r03.zip');renderer=FishRenderer(bundle)
board=Image.new('RGBA',(1440,1440),(62,73,79,255));draw=ImageDraw.Draw(board)
source=Image.open(project/'asset/C/C011_toktogi/2D/idle/idle/left/0.png').convert('RGBA')
tok={name:source.crop((0,i*128,128,(i+1)*128)) for i,name in enumerate(('sprite','base','normal','rm','emissive'))}
fields=shared_lighting.fields(tok,[],linear(np.arange(256)).tolist())
for row,(sex,action,phase,u) in enumerate((('female','hover_or_school','mid',0),('male','hover_or_school','mid',0),('female','surface_gape','mid',.5))):
    cell=bundle.cell(sex,action,phase,u);pivot=bundle.manifest['views'][sex+'/left']['pivot']
    for col,mode in enumerate(('sprite','relit')):
        origin=(col*720+365-pivot[0],row*400+215-pivot[1]);light=(col*720+340,row*400+40)
        image,offset=renderer.render(cell,sex,light=(light[0]-origin[0],origin[1]-light[1]),mode=mode)
        board.alpha_composite(image,(round(origin[0]+offset[0]),round(origin[1]+offset[1])))
        torigin=(col*720+70,row*400+200)
        tim=tok['sprite'] if mode=='sprite' else shared_lighting.shade(fields,light[0]-torigin[0],torigin[1]-light[1],None,None,.82,True,.34,1)
        board.alpha_composite(tim,torigin);draw.text((col*720+20,row*400+14),f'{sex} {action} | {mode} | 1x',font=font,fill='white')
board.convert('RGB').save(ROOT/'comparison/c011_shared_light_color.png');ImageOps.grayscale(board).save(ROOT/'comparison/c011_shared_light_gray.png')
board=Image.new('RGBA',(1600,1040),(62,73,79,255));draw=ImageDraw.Draw(board)
for row,sex in enumerate(('female','male')):
    for col,(view,action,u) in enumerate((('left','cruise',.25),('right','cruise',.75),('front','surface_gape',.5),('top','turn',.5))):
        cell=bundle.cell(sex,action,'mid',u,view);pic,offset=renderer.render(cell,sex,mode='sprite')
        # Board only: uniform nearest 1/2 scale fits four native-view inspections.
        pic=pic.resize((pic.width//2,pic.height//2),Image.Resampling.NEAREST)
        board.alpha_composite(pic,(col*400+(400-pic.width)//2,row*500+75));draw.text((col*400+12,row*500+12),f'{sex} / {view} / {action}',font=font,fill='white')
board.convert('RGB').save(ROOT/'comparison/directions_extremes.png')
cell=bundle.cell('female','surface_gape','mid',.5);board=Image.new('RGBA',(1440,560),(62,73,79,255));draw=ImageDraw.Draw(board)
for col,(label,flat,emission) in enumerate((('Normal + Emissive',False,True),('Flat Normal',True,True),('No Emissive',False,False))):
    pic,off=renderer.render(cell,'female',light=(180,-120),flat=flat,emission=emission);board.alpha_composite(pic,(col*480+(480-pic.width)//2,70));draw.text((col*480+14,18),label,font=font,fill='white')
board.convert('RGB').save(ROOT/'comparison/material_negative_controls.png');bundle.close()
