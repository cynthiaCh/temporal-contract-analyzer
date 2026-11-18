"""Keep Windows awake while the owned experiment container runs; leave display alone."""
import argparse
import ctypes
import re
import subprocess
import time
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('container');parser.add_argument('--log',type=Path)
    parser.add_argument('--wait-start-seconds',type=int,default=0,help='Keep awake through preparation while waiting for the owned controller')
    args=parser.parse_args()
    if not re.fullmatch(r'tca-(?:full-[a-f0-9]{16}|growth-[a-f0-9]{32})',args.container):raise SystemExit('Expected this experiment controller name')
    if not 0<=args.wait_start_seconds<=3600:raise SystemExit('Bounded controller preparation wait required')
    docker=Path('D:/Docker/resources/bin/docker.exe')
    if args.container.startswith('tca-growth-'):
        owner=subprocess.check_output([str(docker),'inspect','--format','{{index .Config.Labels "tempoevo.owner"}}',args.container],text=True).strip()
        if owner!='growth-v12-ds-adapter-v4-20261118-01':raise SystemExit('Growth controller ownership mismatch')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.SetThreadExecutionState.argtypes=[ctypes.c_uint32];kernel.SetThreadExecutionState.restype=ctypes.c_uint32
    if not kernel.SetThreadExecutionState(0x80000001):raise ctypes.WinError(ctypes.get_last_error())
    try:
        seen=False;deadline=time.monotonic()+args.wait_start_seconds
        while True:
            observed=subprocess.run([str(docker),'inspect','--format','{{.State.Running}}',args.container],capture_output=True,text=True,timeout=20)
            if observed.returncode or observed.stdout.strip()!='true':
                if not seen and time.monotonic()<deadline:time.sleep(15);continue
                break
            seen=True
            time.sleep(30)
    finally:
        kernel.SetThreadExecutionState(0x80000000)
        if args.log:args.log.write_text('Experiment controller stopped; automatic sleep prevention released.\n',encoding='utf-8')


if __name__=='__main__':main()
