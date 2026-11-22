#!/usr/bin/env python3
"""Provision a pinned Qoder CLI and a dedicated Credits account for Linux solvers."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
from urllib.request import urlopen

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO/'.tempoevo/qoder'
VERSION = '1.1.94'
BASE = 'https://qoder-ide.oss-accelerate.aliyuncs.com/qodercli'


def provision():
    ROOT.mkdir(parents=True, exist_ok=True)
    with urlopen(BASE+'/channels/'+VERSION+'/manifest.json', timeout=30) as response:
        manifest = json.load(response)
    if manifest['latest'] != VERSION:
        raise ValueError('Qoder manifest version mismatch')
    targets = [('linux', 'amd64')]
    if platform.system() == 'Darwin':
        targets.append(('darwin', 'arm64' if platform.machine() == 'arm64' else 'amd64'))
    installed = {}
    for system, arch in targets:
        record = next(f for f in manifest['files'] if f['os'] == system and f['arch'] == arch)
        package = ROOT/(system+'.tgz')
        if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != record['sha256']:
            print('Downloading Qoder '+VERSION+' for '+system+'/'+arch, flush=True)
            with urlopen(record['url'], timeout=120) as response, package.open('wb') as output:
                shutil.copyfileobj(response, output)
        if hashlib.sha256(package.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Qoder archive checksum mismatch')
        directory = ROOT/system
        directory.mkdir(exist_ok=True)
        with tarfile.open(package) as archive:
            members = [m for m in archive if m.isfile() and Path(m.name).name in ('qodercli', 'qoder')]
            if len(members) != 1:
                raise ValueError('Unexpected Qoder archive layout')
            binary = directory/'qoder'
            binary.write_bytes(archive.extractfile(members[0]).read())
            binary.chmod(0o755)
        installed[system] = dict(path=str(binary), sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    (ROOT/'installation.json').write_text(json.dumps(dict(version=VERSION, binaries=installed), indent=2)+'\n')


def copy_account():
    source = Path.home()/'.qoder/.auth'
    if not (source/'user').is_file():
        raise ValueError('Qoder CLI is not signed in. Run this script with --login.')
    destination = ROOT/'account/.auth'
    destination.mkdir(parents=True, exist_ok=True)
    destination.chmod(0o700)
    for name in ('user', 'machine_id', '.credential-transaction'):
        if (source/name).is_file():
            shutil.copyfile(source/name, destination/name)
            (destination/name).chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--login', action='store_true', help='Sign in with the official Qoder browser flow')
    args = parser.parse_args()
    provision()
    if args.login:
        binary = ROOT/('darwin' if platform.system() == 'Darwin' else 'linux')/'qoder'
        subprocess.run([str(binary), 'login'], check=True)
    if args.login or not (ROOT/'account/.auth/user').is_file():
        copy_account()
    print('Qoder '+VERSION+' provisioned. Built-in DeepSeek profiles use Qoder Credits; no DeepSeek API key is required.')


if __name__ == '__main__':
    main()
