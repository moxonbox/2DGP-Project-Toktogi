"""Executable acceptance evidence; no browser or GPU approval is implied."""
import copy,json,math,os,sys,time
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
from fish_bundle import FishBundle,validate,signature,strict_json
from fish_sim import FishSim,Water,STEP
from fish_renderer import FishRenderer,prepare,shade,linear
from motion_spec import VARIANTS,DESIGNS

ROOT=Path(__file__).resolve().parents[1]

def memory_usage():
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(k,ctypes.c_size_t) for k in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
    counters=Counters();counters.cb=ctypes.sizeof(counters)
    api=ctypes.WinDLL('psapi');api.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if not api.GetProcessMemoryInfo(wintypes.HANDLE(-1),ctypes.byref(counters),counters.cb):raise ctypes.WinError()
    return {'working_set_bytes':counters.WorkingSetSize,'peak_working_set_bytes':counters.PeakWorkingSetSize,'private_bytes':counters.PrivateUsage}

def run():
    start=time.perf_counter();bundle=FishBundle(ROOT/'2D/gambusia-r01/gambusia_holbrooki_r01.zip')
    report={'status':'PASS','bundle_load_seconds':time.perf_counter()-start,'physics':{},'manifest_negative':[]}
    for variant in VARIANTS:
        results={}
        for fps in (10,15,20,30,60):
            sim=FishSim(bundle,variant,breach_enabled=True);sim.start_sequence('breach');seen=set();last=None
            for _ in range(fps*8):
                sim.advance(1/fps);seen.add(sim.action)
                if sim.mode=='airborne':
                    assert not sim.propulsion
                    if last and last[0]=='airborne':assert abs((sim.vz-last[1])*fps+3*sim.sl)<1e-6
                last=(sim.mode,sim.vz)
            counts=Counter(e['kind'] for e in sim.effects)
            assert counts=={'exit_ripple':1,'splash':1,'ripple':1},counts
            assert {'airborne_arc','surface_fall','water_reentry','cruise'}<=seen
            results[str(fps)]={'effects':dict(counts),'end':[sim.action,sim.phase,sim.x,sim.z]}
        assert all(np.allclose(v['end'][2:],results['60']['end'][2:]) for v in results.values())
        surface=FishSim(bundle,variant);surface.start_sequence('surface');gape_ticks=0;body_fraction=[]
        for _ in range(12*120):
            surface.step()
            if surface.action=='surface_gape' and surface.phase=='mid':
                gape_ticks+=1;g=surface.geometry()
                assert surface.mouth_point()[1]>surface.water.surface
                assert surface.mode=='surface_boundary' and surface.z+g['body_ref'][2]<surface.water.surface
                fraction=np.mean(g['vertices'][:g['body_count'],2]+surface.z>0);body_fraction.append(float(fraction))
                assert fraction<.03,fraction
        assert gape_ticks>=280 and not surface.effects
        food=FishSim(bundle,variant);food.start_sequence('feeding',target={'id':'food','x':0,'z':0,'radius':.015*food.sl,'resource':True})
        for _ in range(10*120):
            food.pending_target['x'],food.pending_target['z']=food.mouth_point()
            food.step()
        assert Counter(e['kind'] for e in food.effects)=={'attack':1,'feed':1}
        far=FishSim(bundle,variant);far.start_sequence('feeding',target={'id':'far','x':1000,'z':0,'resource':True})
        for _ in range(10*120):far.step()
        assert not far.effects
        guard=FishSim(bundle,variant);assert not guard.start_sequence('breach');assert not guard.request('out_of_water')
        guard.breach_enabled=True;assert not guard.start_sequence('breach',airspace_clear=False)
        # Cancellation must invalidate an active attack before contact resolution.
        cancelled=FishSim(bundle,variant);cancelled.request('surface_snap',target={'id':'near','x':0,'z':0,'radius':100})
        cancelled.cancel()
        for _ in range(240):cancelled.step()
        assert not cancelled.effects
        air=FishSim(bundle,variant,breach_enabled=True);air.start_sequence('breach')
        while air.mode!='airborne':air.step()
        snapshot=air.snapshot();air.paused=True;frozen=air.snapshot();air.advance(1)
        assert air.snapshot()==frozen;air.paused=False
        before=copy.deepcopy(air.effects);air.seek('surface_snap','mid',.5);assert air.effects==before
        restored=FishSim.restore(bundle,json.loads(json.dumps(snapshot)))
        for _ in range(720):air.step();restored.step()
        assert air.snapshot()==restored.snapshot()
        missed=FishSim.restore(bundle,snapshot);missed.x=missed.water.right+missed.sl;missed.vx=missed.sl
        for _ in range(720):missed.step()
        assert missed.failed and missed.action=='out_of_water' and missed.x>missed.water.right
        assert not missed.propulsion and not any(e['kind']=='splash' for e in missed.effects)
        cancel_air=FishSim.restore(bundle,snapshot);cancel_air.cancel();v=cancel_air.vz;z=cancel_air.z;cancel_air.step()
        assert cancel_air.vz<v and cancel_air.z!=z and not cancel_air.propulsion
        try:FishSim.restore(bundle,{**snapshot,'bundle':'bad'})
        except ValueError:pass
        else:raise AssertionError('snapshot accepted unknown field')
        school=FishSim(bundle,variant);school.request('cruise')
        for _ in range(120):school.step(neighbors=({'x':school.x+.2*school.sl},))
        assert school.x<0 and abs(school.vx)>0
        school.request('turn')
        for _ in range(180):school.step()
        assert school.view=='right'
        external=FishSim(bundle,variant);external.x=100;external.step();assert external.action=='out_of_water' and not external.propulsion
        report['physics'][variant]={'fps':results,'gape_body_fraction_above_max':max(body_fraction),
            'attack_feed_once':True,'no_far_contact':True,'pause_seek_restore_cancel':True,'missed_water_no_teleport':True}
    original=bundle.manifest;key='female/cruise/mid'
    def reject(name,mutate,resign=True):
        value=copy.deepcopy(original);mutate(value)
        if resign:value['signature']=signature(value)
        try:validate(value)
        except (ValueError,KeyError,TypeError) as error:report['manifest_negative'].append({'case':name,'error':str(error)})
        else:raise AssertionError('accepted '+name)
    sample=lambda m:m['clips'][key]['views']['left']['samples'][0]
    reject('schema',lambda m:m.update(schema=999));reject('signature',lambda m:m.update(signature='bad'),False)
    reject('missing_clip',lambda m:m['clips'].pop(key));reject('missing_view',lambda m:m['clips'][key]['views'].pop('left'))
    reject('missing_pass',lambda m:m['clips'][key]['views']['left']['pass_files'].pop('normal'))
    reject('missing_sample',lambda m:m['clips'][key]['views']['left']['samples'].pop())
    reject('bad_rect',lambda m:sample(m).update(rect=[-1,0,640,640]))
    reject('zero_duration',lambda m:sample(m).update(duration=0));reject('nan_marker',lambda m:sample(m)['markers']['mouth_tip'].update(xy=[float('nan'),0]))
    reject('duplicate_cell',lambda m:sample(m).update(file=m['clips'][key]['views']['left']['samples'][1]['file']))
    reject('bad_transition',lambda m:m['sequences']['surface'].append('missing'))
    reject('missing_marker',lambda m:sample(m)['markers'].pop('mouth_tip'))
    reject('nan_pivot',lambda m:m['views']['female/left'].update(pivot=[0,float('nan')]))
    reject('bad_sample_time',lambda m:sample(m).update(u=.5))
    try:strict_json('{"cell":1,"cell":2}')
    except ValueError as error:report['manifest_negative'].append({'case':'duplicate_json_key','error':str(error)})
    else:raise AssertionError('duplicate JSON accepted')
    import tempfile
    with tempfile.TemporaryDirectory(prefix='gambusia_verify_') as tmp:
        broken=Path(tmp)/'broken.zip';broken.write_bytes(b'corrupted')
        broken.with_suffix('.source.json').write_bytes(bundle.path.with_suffix('.source.json').read_bytes())
        try:FishBundle(broken)
        except ValueError as error:report['corrupted_bundle_rejected']=str(error)
        else:raise AssertionError('corrupt archive accepted')
    path=next(iter(bundle.manifest['files']));digest=bundle.manifest['files'][path];bundle.manifest['files'][path]='0'*64
    try:bundle.read(path)
    except ValueError as error:report['corrupted_payload_rejected']=str(error)
    else:raise AssertionError('corrupt payload accepted')
    finally:bundle.manifest['files'][path]=digest
    # Compare the vectorized implementation with the unmodified C011 BRDF.
    sys.path.insert(0,str(ROOT/'3D/tools'));import shared_lighting
    renderer=FishRenderer(bundle);cell=bundle.cell('female','cruise','mid',.5);maps=bundle.maps(cell)
    adapted=dict(maps);orm=maps['orm'];adapted['rm']=Image.merge('RGBA',(orm.getchannel('G'),orm.getchannel('B'),Image.new('L',orm.size),Image.new('L',orm.size,255)))
    table=linear(np.arange(256)).tolist();reference=shared_lighting.shade(shared_lighting.fields(adapted,[],table),180,-120,None,None,.82,True,.34,1)
    fields=prepare(maps,box=(0,0,maps['sprite'].width,maps['sprite'].height))
    calculated=shade(fields,180,-120);error=np.abs(calculated.astype(int)-np.asarray(reference).astype(int))
    assert error.max()<=1,error.max();report['C011_BRDF_max_channel_error']=int(error.max())
    normal=shade(fields,180,-120);flat=shade(fields,180,-120,flat=True);no_emit=shade(fields,180,-120,emission=False)
    assert np.any(normal!=flat) and np.any(normal!=no_emit)
    dry,_=renderer.render(cell,'female',mode='sprite');wet,_=renderer.render(cell,'female',mode='sprite',root_z=-3)
    assert np.any(np.asarray(dry)!=np.asarray(wet))
    # Actual CPU conversion and SDL software upload/blit; explicitly not a GPU measurement.
    os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy';os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
    import pygame as pg
    pg.init();screen=pg.display.set_mode((960,560));warm=time.perf_counter()
    for i in range(12):renderer.render(bundle.cell('female','cruise','mid',i/12),'female')
    report['warmup_seconds']=time.perf_counter()-warm;costs=[]
    for i in range(120):
        cell=bundle.cell('female','cruise','mid',(i%12)/12);t=time.perf_counter()
        picture,offset=renderer.render(cell,'female',light=(180+80*math.sin(i/30),-120),root_z=-2)
        surface=pg.image.frombytes(picture.tobytes(),picture.size,'RGBA');screen.fill((24,44,49));screen.blit(surface,offset);pg.display.flip()
        costs.append((time.perf_counter()-t)*1000)
    pg.quit()
    report['performance']={'frames':120,'mode':'female 640 cell, moving light + water + RGBA transfer + SDL dummy blit',
        'p95_ms':float(np.percentile(costs,95)),'max_ms':max(costs),'mean_ms':float(np.mean(costs)),
        'meets_16_7_ms':bool(max(costs)<=16.7),'renderer_cache_bytes':renderer.cache_bytes(),
        'raw_bundle_bytes':original['memory']['raw_rgba_bytes'] if 'memory' in original else 20535312384,
        'actual_GPU':'NOT_RUN','browser':'NOT_RUN','Pico2D':'NOT_IMPLEMENTED'}
    report['process_memory']=memory_usage();report['elapsed_seconds']=time.perf_counter()-start
    report['status']='FUNCTIONAL_PASS' if report['performance']['meets_16_7_ms'] else 'FUNCTIONAL_PASS_PERFORMANCE_REVIEW'
    (ROOT/'document/runtime_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));bundle.close();return report

if __name__=='__main__':run()
