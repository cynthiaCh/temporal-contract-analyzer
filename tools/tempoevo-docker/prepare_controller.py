"""Stage fixed public Codex downloads for the trusted Linux controller."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

REPO=Path(__file__).resolve().parents[2]


def prepare(directory):
    directory=Path(directory).resolve()
    meta=json.loads((directory/'codex-metadata.json').read_text(encoding='utf-8-sig'))
    archive=directory/'codex-linux-x64.tgz'
    digest='sha512-'+base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
    if digest!=meta['dist']['integrity']:raise ValueError('Official npm integrity mismatch')
    public=directory/'public-cli'
    if public.exists():raise ValueError('Use a new public-cli directory')
    public.mkdir()
    names={'bin/codex':'codex','bin/codex-code-mode-host':'codex-code-mode-host',
           'codex-path/rg':'rg','codex-resources/bwrap':'codex-resources/bwrap'}
    with tarfile.open(archive) as packed:
        for source,dest in names.items():
            item=packed.getmember('package/vendor/x86_64-unknown-linux-musl/'+source)
            if not item.isfile():raise ValueError('Expected a regular public CLI file')
            target=public/dest;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(packed.extractfile(item).read());target.chmod(0o755)
    shutil.copyfile(REPO/'containers/tempoevo/Dockerfile.controller',directory/'Dockerfile')
    (directory/'.dockerignore').write_text('**\n!Dockerfile\n!codex-linux-x64.tgz\n!codex-metadata.json\n',encoding='utf8')
    proof=dict(version=meta['version'],npm_integrity=digest,model_calls=0,
        files={str(p.relative_to(public)):hashlib.sha256(p.read_bytes()).hexdigest() for p in public.rglob('*') if p.is_file()})
    (directory/'public-cli-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path,required=True)
    prepare(parser.parse_args().directory)
