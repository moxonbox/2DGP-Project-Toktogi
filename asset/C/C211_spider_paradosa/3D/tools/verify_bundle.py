"""Regression checks for malformed manifests and corrupted bundles."""
import copy
import json
import tempfile
from pathlib import Path
from idle_bundle import IdleBundle,signature,validate_manifest

ROOT=Path(__file__).resolve().parents[2]
archive=ROOT/'2D/idle-r02/spider_pardosa_idle_r02.zip'
bundle=IdleBundle(archive)
assert bundle.sample_at(0)['index']==0
assert bundle.sample_at(2)['index']==0
assert bundle.sample_at(-1/12)['index']==23
for view in ('left','right'):
    for index in range(24):
        maps=bundle.maps(view,index)
        assert len(maps)==6 and maps['sprite'].size==(640,640)


def reject(change,expected):
    manifest=copy.deepcopy(bundle.manifest)
    change(manifest)
    manifest['bundle_contract_signature']=signature(manifest)
    try:
        validate_manifest(manifest)
    except ValueError as error:
        assert expected in str(error),(expected,str(error))
    else:
        raise AssertionError('Invalid manifest accepted: '+expected)


reject(lambda m:m.update(schema=999),'unsupported schema')
reject(lambda m:m['clips']['idle_scan']['samples'][1].update(index=0),'duplicate')
reject(lambda m:m['clips']['idle_scan']['samples'][0].update(duration_s=0),'invalid sample time')
reject(lambda m:m['clips']['idle_scan']['samples'][0]['views'].pop('right'),'missing view')
reject(lambda m:m['views']['left']['pass_files'].pop('normal'),'missing material pass')
reject(lambda m:m['clips']['idle_scan']['samples'][0]['views']['left'].update(rect=[9999,2,640,640]),'outside bounds')
reject(lambda m:m['clips']['idle_scan']['samples'][0]['views']['left']['markers']['foot_L1'].update(xy=[float('nan'),1]),'invalid marker')
reject(lambda m:m['clips']['idle_scan']['samples'][0]['views']['left']['markers'].pop('foot_L1'),'missing marker')
reject(lambda m:m.update(transitions={'idle_scan':'absent_clip'}),'unsupported clip or transition')
with tempfile.TemporaryDirectory(dir=ROOT) as temp:
    bad=Path(temp)/archive.name
    data=bytearray(archive.read_bytes())
    data[len(data)//2]^=1
    bad.write_bytes(data)
    bad.with_suffix('.source.json').write_bytes(archive.with_suffix('.source.json').read_bytes())
    try:
        IdleBundle(bad)
    except ValueError as error:
        assert archive.name in str(error) and 'checksum' in str(error)
    else:
        raise AssertionError('Corrupt bundle accepted')
bundle.close()
report={'status':'PASS','decoded_cells':48,'negative_cases':['schema','duplicate sample','zero duration','missing view',
    'missing pass','out-of-bounds rect','nonfinite marker','missing marker','invalid transition','corrupt ZIP checksum'],
    'timeline_boundaries':'0, 2 seconds and negative seek','errors':'bundle filename and cell/field context'}
(ROOT/'2D/idle-r02/bundle_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PASS 48 decoded cells and 10 malformed-input regressions')
