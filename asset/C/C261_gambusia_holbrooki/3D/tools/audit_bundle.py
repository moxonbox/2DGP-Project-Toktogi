"""Verify every packaged payload after ZIP serialization."""
import json,sys,time
from pathlib import Path
from io import BytesIO
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runtime'))
from fish_bundle import FishBundle
t=time.perf_counter();bundle=FishBundle(ROOT/'2D/gambusia-r01/gambusia_holbrooki_r01.zip')
count=0;size=0
for path in bundle.manifest['files']:
    data=bundle.read(path);size+=len(data);count+=1
    if path.endswith('.png'):
        with Image.open(BytesIO(data)) as image:
            assert image.mode=='RGBA',(path,image.mode)
            if path.startswith(('2D/swim/','2D/air/','2D/surface/')):assert image.height==image.width*8
result={'status':'PASS','payload_files':count,'payload_bytes':size,'elapsed_seconds':time.perf_counter()-t,'bundle_signature':bundle.manifest['signature']}
(ROOT/'document/bundle_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));bundle.close()
