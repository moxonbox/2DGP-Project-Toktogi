"""Pack each r5 sprite cell and its four material passes for bounded runtime loading."""
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile
from PIL import Image
PASSES = ('sprite', 'base', 'normal', 'rm', 'emissive')

def pack(source, target):
    source = source.resolve()
    target = target.resolve()
    raw = (source / 'playable_manifest.json').read_bytes()
    data = json.loads(raw)
    signature = data.pop('bundle_contract_signature')
    if not signature == hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest():
        raise ValueError('Invalid source bundle metadata or image')
    if not data['asset_revision'] == 'integrated-r5':
        raise ValueError('Invalid source bundle metadata or image')
    staging = target.with_suffix('.tmp')
    count = 0
    try:
        with ZipFile(staging, 'w') as bundle:
            bundle.writestr('playable_manifest.json', raw, compress_type=ZIP_DEFLATED)
            for view, entries in data['pass_files'].items():
                images = []
                for name in PASSES:
                    asset = entries[name]
                    path = (source / asset['file']).resolve()
                    if not path.is_relative_to(source):
                        raise ValueError('Asset path leaves source directory')
                    blob = path.read_bytes()
                    if not hashlib.sha256(blob).hexdigest() == asset['sha256']:
                        raise ValueError((view, name))
                    with Image.open(BytesIO(blob)) as image:
                        if not (image.mode == 'RGBA' and list(image.size) == asset['size']):
                            raise ValueError('Invalid source bundle metadata or image')
                        images.append(image.copy())
                for name, clip in data['clips'].items():
                    for index, sample in enumerate(clip['samples']):
                        if view not in sample['views']:
                            continue
                        x, y, width, height = sample['views'][view]['rect']
                        if not ((width, height) == (128, 128) and all((0 <= x <= image.width - width and 0 <= y <= image.height - height for image in images))):
                            raise ValueError('Invalid source bundle metadata or image')
                        packed = Image.new('RGBA', (128, 128 * len(PASSES)))
                        for band, image in enumerate(images):
                            packed.paste(image.crop((x, y, x + 128, y + 128)), (0, band * 128))
                        stream = BytesIO()
                        packed.save(stream, format='PNG', compress_level=4)
                        bundle.writestr(f'{name}/{view}/{index}.png', stream.getvalue())
                        count += 1
        with ZipFile(staging) as bundle:
            if not (bundle.testzip() is None and len(bundle.namelist()) == count + 1):
                raise ValueError('Invalid source bundle metadata or image')
        staging.replace(target)
        with target.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        lock = {'schema': 1, 'asset_revision': data['asset_revision'], 'bundle_sha256': digest, 'manifest_signature': signature, 'source_blend_sha256': data['source_blend_sha256'], 'authoring_directory': os.path.relpath(source.resolve(), target.resolve().parent).replace('\\', '/')}
        lock_file = target.with_suffix('.source.json')
        temporary_lock = lock_file.with_suffix('.tmp')
        temporary_lock.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporary_lock.replace(lock_file)
    finally:
        staging.unlink(missing_ok=True)
    print(f'{count} sprite cells, {target.stat().st_size:,} bytes')
if __name__ == '__main__':
    pack(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'asset/C/C011_toktogi/2D/integrated-r5', Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name('toktogi_assets.zip'))
