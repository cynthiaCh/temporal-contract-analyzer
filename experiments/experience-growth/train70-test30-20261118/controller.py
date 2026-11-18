"""Windows launcher for this experiment's trusted Linux controller only."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
IMAGE='sha256:82bd3e64ed648daf26ae426433b5d9c1db1e0af9d45ec79c0722c23d082a0f12'
VOLUME='tca-growth-adapter-v4-20261118'
OWNER='growth-v12-ds-adapter-v4-20261118-01'


def host_path(path):
    path=Path(path).resolve()
    if os.name!='nt':return str(path)
    return '/run/desktop/mnt/host/'+path.drive[0].lower()+'/'+path.as_posix()[3:]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials',action='store_true')
    parser.add_argument('--build-context',type=Path)
    parser.add_argument('script',help='Repository-relative Python script')
    parser.add_argument('arguments',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    script=(REPO/args.script).resolve()
    if not script.is_file() or not script.is_relative_to(REPO):raise ValueError('Script must belong to repository')
    actual=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',IMAGE],text=True).strip()
    if actual!=IMAGE:raise ValueError('Controller image changed')
    inspect=subprocess.run(['docker','volume','inspect',VOLUME],capture_output=True,text=True)
    if inspect.returncode:
        subprocess.run(['docker','volume','create','--label','tempoevo.owner='+OWNER,VOLUME],check=True,capture_output=True)
        inspect=subprocess.run(['docker','volume','inspect',VOLUME],capture_output=True,text=True,check=True)
    volume=json.loads(inspect.stdout)[0]
    if volume.get('Labels',{}).get('tempoevo.owner')!=OWNER:raise ValueError('Volume belongs to another task')
    base=volume['Mountpoint'];repo=host_path(REPO)
    command=['docker','run','--rm','-i','--pull=never','--name','tca-growth-'+uuid.uuid4().hex,
        '--label','tempoevo.owner='+OWNER,'--network','host','--read-only',
        '--mount','type=bind,src='+str(REPO)+',dst='+repo,
        '--mount','type=volume,src='+VOLUME+',dst='+base,
        '--mount','type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock',
        '--tmpfs','/tmp:rw,exec,mode=1777','--workdir',repo,
        '--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH='+repo,
        '--env','TMPDIR='+base+'/tmp','--env','TCA_GROWTH_VOLUME='+base,
        '--env','TCA_PUBLIC_CLI='+base+'/public-cli']
    if args.build_context:
        command+=['--mount','type=bind,src='+str(args.build_context.resolve())+',dst=/growth-build,readonly']
    environment=dict(os.environ)
    if args.credentials:
        sys.path.insert(0,str(REPO/'tools'))
        from configure_deepseek import load_key
        environment['DEEPSEEK_API_KEY']=load_key()
        command+=['--env','DEEPSEEK_API_KEY']
    # TMPDIR and public executable paths must also be visible to sibling containers.
    bootstrap="import fcntl,hashlib,os,pathlib,runpy,shutil,sys\nb=pathlib.Path(os.environ['TCA_GROWTH_VOLUME']);(b/'tmp').mkdir(exist_ok=True)\nsource=pathlib.Path('/opt/public-cli');target=b/'public-cli'\nwith (b/'public-cli.lock').open('a') as lock:\n    fcntl.flock(lock,fcntl.LOCK_EX)\n    if not target.exists():shutil.copytree(source,target)\n    expected={p.relative_to(source):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}\n    actual={p.relative_to(target):hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}\n    if actual!=expected:raise RuntimeError('Public CLI identity differs; refuse overwrite or model dispatch')\nsys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
    command+=['--entrypoint','python3',IMAGE,'-B','-c',bootstrap,repo+'/'+script.relative_to(REPO).as_posix(),*args.arguments]
    try:
        return subprocess.run(command,env=environment).returncode
    finally:
        environment.pop('DEEPSEEK_API_KEY',None)


if __name__=='__main__':raise SystemExit(main())
