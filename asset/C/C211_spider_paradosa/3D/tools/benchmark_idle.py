"""120-frame software display costs, with real 640px payload decoding."""
import ctypes
import json
import math
import os
import platform
import time
import winreg
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from idle_bundle import IdleBundle
import shared_lighting

ROOT=Path(__file__).resolve().parents[2]
clock=time.perf_counter
start=clock()
bundle=IdleBundle(ROOT/'2D/idle-r02/spider_pardosa_idle_r02.zip')
load_ms=(clock()-start)*1000
table=[c/255/12.92 if c/255<=.04045 else ((c/255+.055)/1.055)**2.4 for c in range(256)]
cached=[]
start=clock()
for index in range(24):
    maps=bundle.maps('left',index)
    fields=shared_lighting.fields(maps,(),table)
    cached.append(shared_lighting.shade(fields,320,-200,None,None,.82,True,.34,1.))
warm_ms=(clock()-start)*1000
pygame.init()
screen=pygame.display.set_mode((960,640))


def display(image):
    surface=pygame.image.frombytes(image.tobytes(),image.size,'RGBA').convert_alpha()
    screen.fill((114,126,135))
    screen.blit(surface,(260,-36))
    pygame.display.flip()


def summary(values):
    ordered=sorted(values)
    return {'p95_ms':ordered[math.ceil(.95*len(ordered))-1],'max_ms':max(ordered),
            'mean_ms':sum(ordered)/len(ordered),'frames':len(ordered)}


fixed=[]
for frame in range(120):
    start=clock()
    display(cached[bundle.sample_at(frame/60)['index']])
    fixed.append((clock()-start)*1000)
moving=[]
last_index=None
for frame in range(120):
    start=clock()
    index=bundle.sample_at(frame/60)['index']
    if index!=last_index:
        fields=shared_lighting.fields(bundle.maps('left',index),(),table)
        last_index=index
    image=shared_lighting.shade(fields,320+160*math.sin(frame/60*math.pi),-200,None,None,.82,True,.34,1.)
    display(image)
    moving.append((clock()-start)*1000)
pygame.quit()
bundle.close()
class ProcessMemory(ctypes.Structure):
    _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in
              ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
               'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
memory=ProcessMemory();memory.cb=ctypes.sizeof(memory)
ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(ProcessMemory),ctypes.c_ulong]
assert ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(memory),memory.cb)
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
    cpu=winreg.QueryValueEx(key,'ProcessorNameString')[0].strip()
report={'device':{'system':platform.platform(),'processor':cpu,'python':platform.python_version(),'pygame':pygame.version.ver},
        'scope':'left view, one C211 actor, 640px, 120 frames at 60fps timeline; timings are measured, not paced',
        'load_verify_ms':load_ms,'warm_24_frames_ms':warm_ms,'fixed_light_cached':summary(fixed),
        'moving_light_cpu':summary(moving),'target_display_ms':16.7,'display_backend':'SDL dummy software display',
        'includes':['CPU decode when sample changes','CPU shading for moving light','RGBA transfer to SDL surface','software blit/flip'],
        'not_measured':['GPU upload','real window compositor','game physics/AI'],
        'memory':{'raw_unique_cells_bytes':48*6*640*640*4,'atlas_rgba_bytes':12*3864*2576*4,
                  'cached_fixed_rgba_bytes':24*640*640*4,'peak_working_set_bytes':memory.PeakWorkingSetSize,
                  'browser_overhead':'embedded base64/decoded atlases/canvas copies additional, not measured'},
        'cache_key_contract':['asset_id','revision','clip','view','sample','light parameters','material parameters','flat_normal','emission'],
        'fixed_light_cpu_budget_pass':summary(fixed)['p95_ms']<=16.7,
        'moving_light_cpu_budget_pass':summary(moving)['p95_ms']<=16.7,'game_ready':False}
(ROOT/'2D/idle-r02/performance_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
