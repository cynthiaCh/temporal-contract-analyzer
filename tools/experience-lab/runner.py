"""Thin local web controller; all model execution stays in the public TempoEvo CLI."""
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import threading
import uuid

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.tempoevo_v4 import Trajectory

DEFAULT_SOLVER = 'sha256:06e8aefa92fe3b031af8d52938059ce3f4b99db0489c445cb1d5095f2487d50c'
DEFAULT_GRADER = 'sha256:00b97937eb4e3c9db1ef6f071dde20629034910bbbfdd9a8b4a34b1ecf102da7'
PUBLIC_DOCS = 'experiments/training-replays/tempoevo-gpt56-sol-medium-train70-twoarms-worker1-20261118_002327/public-checks-docs.json'


def default_images():
    path = REPO / '.tempoevo/docker-images.json'
    return read(path) if path.is_file() else dict(solver_image=DEFAULT_SOLVER, grader_image=DEFAULT_GRADER)


def read(path):
    return json.loads(Path(path).read_text())


def now():
    return datetime.now(timezone.utc).isoformat()


def public_profiles(path):
    return {name: dict({key: profile.get(key) for key in ('model', 'reasoning_effort', 'service_tier')},
                       **({'request_unit':'model turns'} if profile.get('provider',{}).get('wire_api')=='qoder_cli' else {}))
            for name, profile in read(path)['profiles'].items()}


def checked_path(value, label, directory=False):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' is required')
    path = Path(value).expanduser()
    path = (REPO / path).resolve() if not path.is_absolute() else path.resolve()
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError(label + ' was not found: ' + str(path))
    return path


def command_output(command, timeout=6):
    try:
        result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=timeout)
        return dict(ok=result.returncode == 0, detail=(result.stdout or result.stderr).strip()[:900])
    except (OSError, subprocess.TimeoutExpired) as error:
        return dict(ok=False, detail=str(error))


def environment():
    codex = configure_codex_path()
    docker = shutil.which('docker')
    probe = command_output([docker, 'info', '--format', '{{.ServerVersion}}']) if docker else dict(ok=False, detail='Docker is not installed')
    qoder = REPO/'.tempoevo/qoder/linux/qoder'
    login = REPO/'.tempoevo/qoder/account/.auth/user'
    return dict(docker=probe, qoder=dict(ok=qoder.is_file() and login.is_file(), detail='Qoder CLI and account files are provisioned' if qoder.is_file() and login.is_file() else 'Provision the Linux Qoder CLI and sign in'),
                codex=dict(ok=bool(codex), detail=codex or 'Codex executable was not found. Add Codex to the workbench PATH.'),
                python=sys.version.split()[0], host=sys.platform)


def configure_codex_path():
    """Finder launches may lack the Codex executable bundled with VS Code."""
    existing = shutil.which('codex')
    if existing or sys.platform != 'darwin':
        return existing
    architectures = {'x86_64': ('x86_64',), 'arm64': ('arm64', 'aarch64')}.get(platform.machine(), ())
    candidates = []
    for architecture in architectures:
        candidates.extend(p for p in (Path.home()/'.vscode/extensions').glob(
            'openai.chatgpt-*/bin/macos-'+architecture+'/codex') if p.is_file() and os.access(p, os.X_OK))
    if not candidates:
        return None
    binary = max(candidates, key=lambda p: (p.stat().st_mtime_ns, str(p)))
    os.environ['PATH'] = str(binary.parent)+os.pathsep+os.environ.get('PATH', '')
    return str(binary)


def prepare_command(config, batch):
    configure_codex_path()
    mode = config.get('mode')
    if mode not in ('learning', 'testing'):
        raise ValueError('Select training or testing')
    if type(config.get('workers')) is not int or not 1 <= config['workers'] <= 8:
        raise ValueError('Concurrent cases must be between 1 and 8')
    total = 70 if mode == 'learning' else 30
    start, count = config.get('start'), config.get('count')
    if type(start) is not int or type(count) is not int or start < 1 or count < 1 or start + count - 1 > total:
        raise ValueError('Selected case range is outside this dataset')
    condition = config.get('condition')
    if condition not in ('structured', 'contract', 'baseline'):
        raise ValueError('Unknown repair condition')
    bench = checked_path(config.get('benchmark'), 'Benchmark directory', True)
    store = checked_path(config.get('store'), 'Experience library', True)
    model_file = checked_path(config.get('model_config'), 'Model profiles file')
    profiles = read(model_file)['profiles']
    if config.get('model_profile') not in profiles:
        raise ValueError('Selected model profile does not exist in this profile file')
    for key in ('solver_image', 'grader_image'):
        value = config.get(key, '')
        if not isinstance(value, str) or len(value) != 71 or not value.startswith('sha256:') or any(c not in '0123456789abcdef' for c in value[7:]):
            raise ValueError('Use an immutable sha256 image ID for ' + key)
    selection = REPO / 'cases' / ('train70.csv' if mode == 'learning' else 'test30.csv')
    command = [sys.executable, '-B', str(REPO/'tools/tempoevo-docker/prepare_selected.py'), '--root', str(batch),
               '--selection-file', str(selection), '--start-rank', str(start), '--limit', str(count),
               '--evaluation-split', str(REPO/'experiments/evaluation-splits.json'), '--mode', mode,
               '--condition', condition, '--solver-image', config['solver_image'], '--grader-image', config['grader_image'],
               '--store', str(store), '--model-config', str(model_file), '--model-profile', config['model_profile']]
    container_codex = REPO / '.tempoevo/bin/linux-x64/codex'
    if profiles[config['model_profile']].get('provider',{}).get('wire_api')=='qoder_cli':
        binary = checked_path('.tempoevo/qoder/linux/qoder', 'Linux Qoder CLI')
        checked_path('.tempoevo/qoder/account/.auth/user', 'Qoder CLI login')
        command += ['--binary', str(binary)]
    elif sys.platform == 'darwin' and container_codex.is_file():
        command += ['--binary', str(container_codex)]
    if mode == 'learning':
        docs = checked_path(config.get('public_checks'), 'Public check descriptions')
        with selection.open(encoding='utf-8-sig', newline='') as handle:
            selected = [r['case_id'] for r in csv.DictReader(handle) if start <= int(r['rank']) < start + count]
        descriptions = read(docs)
        if any(not isinstance(descriptions.get(cid), str) or not descriptions[cid].strip() for cid in selected):
            raise ValueError('Public check descriptions do not cover every selected training case')
        command += ['--training-recipe', 'v8-compatible-v1', '--public-checks-docs', str(docs)]
    return command, dict(os.environ, TCA_BENCH_ROOT=str(bench)), public_profiles(model_file)[config['model_profile']]


def run_command(root):
    return [sys.executable, '-B', '-m', 'temporal_contract_analyzer', 'tempoevo', 'run', '--root', str(root), '--execute']


class Controller:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.active = None
        self.stopping = threading.Event()

    def directory(self, ident):
        if not isinstance(ident, str) or not ident.startswith('run-') or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in ident):
            raise ValueError('Invalid run ID')
        path = self.root / ident
        if not (path / 'lab.json').is_file():
            raise ValueError('Run not found')
        return path

    def event(self, path, kind, message):
        with self.lock:
            with (path/'events.jsonl').open('a') as handle:
                handle.write(json.dumps(dict(at=now(), kind=kind, message=message))+'\n')

    def update(self, path, **fields):
        with self.lock:
            value = read(path/'lab.json')
            value.update(fields, updated_at=now())
            archive.atomic_json(path/'lab.json', value)

    def prepare(self, config):
        with self.lock:
            if self.active:
                raise ValueError('Another preparation or execution is active')
            ident = 'run-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
            path = self.root / ident
            command, env, model = prepare_command(config, path/'batch')
            check = environment()
            if not check['docker']['ok']:
                raise ValueError('Execution host is not ready: Docker is unavailable. '+check['docker']['detail'])
            if model.get('request_unit')!='model turns' and not check['codex']['ok']:
                raise ValueError('Execution host is not ready: '+check['codex']['detail'])
            for image in (config['solver_image'], config['grader_image']):
                probe = command_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', image])
                if not probe['ok']:
                    raise ValueError('Required image is unavailable: ' + image + '. Provision the pinned images on this host first.')
            path.mkdir()
            archive.atomic_json(path/'lab.json', dict(id=ident, status='preparing', created_at=now(), config=config, model=model, prepare_command=command))
            self.active = ident
            self.stopping.clear()
            threading.Thread(target=self._prepare, args=(path, command, env), daemon=True).start()
            return ident

    def _prepare(self, path, command, env):
        try:
            self.event(path, 'PREPARE', 'Preparing source snapshots and evaluator controls. No model requests.')
            with (path/'prepare.log').open('w') as log:
                process = subprocess.run(command, cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT)
            if process.returncode:
                raise ValueError('Preparation failed. Inspect the preparation log; no models were launched.')
            rows = read(path/'batch/progress.json')
            if not rows or any(r['status'] != 'prepared' for r in rows):
                raise ValueError('Some selected cases failed preparation')
            for row in rows:
                Trajectory(Path(row['root'])/'trajectory').verify()
            self.update(path, status='prepared', prepared_cases=len(rows))
            self.event(path, 'READY', f'{len(rows)} cases prepared. Start execution explicitly to call the model.')
        except Exception as error:
            self.update(path, status='preparation_failed', error=str(error))
            self.event(path, 'ERROR', str(error))
        finally:
            with self.lock:
                self.active = None

    def start(self, ident):
        with self.lock:
            path = self.directory(ident)
            if self.active or read(path/'lab.json')['status'] != 'prepared':
                raise ValueError('Only a fully prepared, idle batch can start')
            meta = read(path/'lab.json')
            rows = read(path/'batch/progress.json')
            for row in rows:
                trajectory = Path(row['root'])/'trajectory'
                p = Trajectory(trajectory).verify()
                state = read(trajectory/'state.json')
                if p['mode'] != meta['config']['mode'] or state['stages'] or state['attempts']:
                    raise ValueError('Only fresh, mode-matching trajectories can start; create a new run for retries')
                if p['mode'] == 'testing' and (p['max_attempts'] != 1 or p['learning_policy'] != 'frozen'):
                    raise ValueError('Testing must use one Action and frozen memory')
            self.active = ident
            self.stopping.clear()
            self.update(path, status='running', started_at=now())
            threading.Thread(target=self._execute, args=(path, rows), daemon=True).start()
            return ident

    def _execute(self, path, rows):
        meta = read(path/'lab.json')
        def one(row):
            trajectory = Path(row['root'])/'trajectory'
            if self.stopping.is_set():
                return
            self.event(path, 'START', row['case_id'])
            with (trajectory.parent/'execution.log').open('w') as log:
                code = subprocess.run(run_command(trajectory), cwd=REPO, stdout=log, stderr=subprocess.STDOUT).returncode
            self.event(path, 'FINISH', row['case_id']+' · '+read(trajectory/'state.json')['status']+' · exit '+str(code))
        try:
            with ThreadPoolExecutor(max_workers=meta['config']['workers']) as pool:
                futures = [pool.submit(one, row) for row in rows]
                for future in as_completed(futures):
                    future.result()
            self.update(path, status='stopped' if self.stopping.is_set() else 'finished', finished_at=now())
            self.event(path, 'COMPLETE', 'Batch ended. Read individual case verdicts; a completed queue does not imply every repair passed.')
        except Exception as error:
            self.update(path, status='execution_error', error=str(error))
            self.event(path, 'ERROR', str(error))
        finally:
            with self.lock:
                self.active = None

    def stop(self, ident):
        with self.lock:
            path = self.directory(ident)
            if self.active != ident or read(path/'lab.json')['status'] != 'running':
                raise ValueError('This run is not executing')
            self.stopping.set()
            self.update(path, status='stopping')
            for row in read(path/'batch/progress.json'):
                trajectory = Path(row['root'])/'trajectory'
                state = read(trajectory/'state.json')
                if not state.get('finalized'):
                    subprocess.run([sys.executable, '-B', '-m', 'temporal_contract_analyzer', 'tempoevo', 'cancel', '--root', str(trajectory)],
                                   cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.event(path, 'STOP', 'Cancellation requested. Active requests may need to return before stopping; no automatic replay.')
