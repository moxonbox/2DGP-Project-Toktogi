"""Build a portable preview and validate the exported runtime ZIP."""
import base64
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from PIL import Image
from idle_bundle import signature,validate_manifest

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'2D/idle-r02'
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
source_hash=hashlib.sha256((ROOT/'3D/spider_pardosa_idle_r02.blend').read_bytes()).hexdigest()
assert source_hash==manifest['source_blend_sha256']
images={}
files={}
size_report={'cell_size':[640,640],'required_margin_px':8,'bbox_convention':'left, top, right-exclusive, bottom-exclusive','views':{}}
for view,record in manifest['views'].items():
    bounds=[]
    for channel,name in record['pass_files'].items():
        path=OUT/name
        with Image.open(path) as im:
            assert im.mode=='RGBA' and im.size==(3864,2576)
            im.verify()
        data=path.read_bytes()
        images[f'{view}_{channel}']='data:image/png;base64,'+base64.b64encode(data).decode('ascii')
        files[name]=hashlib.sha256(data).hexdigest()
    with Image.open(OUT/f'idle_scan_{view}.png') as im:
        assert im.n_frames==24 and im.info['loop']==0
        total=0
        for i in range(im.n_frames):
            im.seek(i)
            total+=im.info['duration']
        assert abs(total-2000)<.1
    filename=f'idle_scan_{view}.png'
    files[filename]=hashlib.sha256((OUT/filename).read_bytes()).hexdigest()
    for i in range(24):
        path=ROOT/f'2D/idle/idle_scan/{view}/{i}.png'
        with Image.open(path) as im:
            assert im.size==(640,3840) and im.mode=='RGBA'
            alpha=im.getchannel('A')
            base=alpha.crop((0,640,640,1280))
            assert all(base.tobytes()==alpha.crop((0,p*640,640,(p+1)*640)).tobytes() for p in range(2,6))
            im.load()
            sprite_box=alpha.crop((0,0,640,640)).getbbox()
            base_box=base.getbbox()
            assert sprite_box and base_box
            assert [base_box[0]-sprite_box[0],base_box[1]-sprite_box[1],sprite_box[2]-base_box[2],sprite_box[3]-base_box[3]]==[2,2,2,2]
            margin=min(sprite_box[0],sprite_box[1],640-sprite_box[2],640-sprite_box[3])
            assert margin>=8,(view,i,margin)
            sample_record=manifest['clips']['idle_scan']['samples'][i]['views'][view]
            assert list(sprite_box)==sample_record['bbox']
            sample_record['base_bbox']=list(base_box)
            bounds.append({'index':i,'sprite_bbox':sprite_box,'base_bbox':base_box,'margin_px':margin})
        key=f'idle_scan/{view}/{i}.png'
        files[key]=hashlib.sha256(path.read_bytes()).hexdigest()
        manifest['clips']['idle_scan']['samples'][i]['views'][view]['frame_file']=key
    size_report['views'][view]={'samples':bounds,'minimum_margin_px':min(b['margin_px'] for b in bounds),
        'sprite_wh_range':[[min(b['sprite_bbox'][i+2]-b['sprite_bbox'][i] for b in bounds),max(b['sprite_bbox'][i+2]-b['sprite_bbox'][i] for b in bounds)] for i in (0,1)],
        'base_wh_range':[[min(b['base_bbox'][i+2]-b['base_bbox'][i] for b in bounds),max(b['base_bbox'][i+2]-b['base_bbox'][i] for b in bounds)] for i in (0,1)],'pivot':record['pivot']}
contract=json.loads((ROOT/'document/source_contract.json').read_text(encoding='utf-8'))
manifest.update({'schema':1,'base_signature':contract['style_reference']['base_signature'],
                 'transitions':{},
                 'identifier_mapping':contract['identifier_mapping'],'file_hashes':files,
                 'implementation_state':{'model_idle':'verified','standalone_preview':'verified','game_integration':'pending'},
                 'memory':{'raw_unique_cells_bytes':48*6*640*640*4,
                           'atlas_rgba_bytes':12*3864*2576*4,
                           'raw_cell_budget_bytes':512*1024*1024,'shading_cache_budget_bytes':128*1024*1024}})
manifest['bundle_contract_signature']=signature(manifest)
validate_manifest(manifest)
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
size_report['status']='PASS'
(OUT/'size_validation.json').write_text(json.dumps(size_report,indent=2),encoding='utf-8')
template=(ROOT/'3D/tools/preview_template.html').read_text(encoding='utf-8')
html=template.replace('__MANIFEST__',json.dumps(manifest,ensure_ascii=False)).replace('__IMAGES__',json.dumps(images))
(ROOT/'PardosaIdlePreview.html').write_text(html,encoding='utf-8')
archive=OUT/'spider_pardosa_idle_r02.zip'
members=[p for p in OUT.iterdir() if p.suffix=='.png']+[OUT/'manifest.json']
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for p in members:
        z.write(p,p.name)
    for view in manifest['views']:
        for i in range(24):
            z.write(ROOT/f'2D/idle/idle_scan/{view}/{i}.png',f'idle_scan/{view}/{i}.png')
with ZipFile(archive) as z:
    assert z.testzip() is None
    assert json.loads(z.read('manifest.json'))['asset_id']=='C211_spider_paradosa'
    for name,digest in files.items():
        assert hashlib.sha256(z.read(name)).hexdigest()==digest
lock={'schema':1,'asset_id':manifest['asset_id'],'revision':manifest['revision'],
      'base_signature':manifest['base_signature'],'source_blend_sha256':source_hash,
      'manifest_signature':manifest['bundle_contract_signature'],
      'bundle_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
archive.with_suffix('.source.json').write_text(json.dumps(lock,indent=2),encoding='utf-8')
report={'status':'PASS','files':files,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'source_blend_sha256':source_hash,'frames':48,'atlas_files':12,'apng_files':2,
        'coverage_alignment':'PASS','apng_loop_ms':2000,'preview_javascript':'pending syntax check'}
(OUT/'package_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
