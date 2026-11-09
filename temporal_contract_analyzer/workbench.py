"""Exploratory, local Codex experiments. Preparing inputs never calls a model."""
from difflib import unified_diff
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import threading
import uuid

from . import archive
from .core import EvidenceError, sha
from .layers import CONDITIONS, coverage_summary

EXCLUDED = {'node_modules', '__pycache__', 'dist', 'build', 'coverage', 'vendor'}
TERMINAL = {'completed', 'failed', 'cancelled', 'timed_out', 'interrupted'}
ARTIFACTS = {'prompt.md', 'report.md', 'events.jsonl', 'stderr.log', 'answer.md', 'result.json', 'changes.json'}
EVALUATION_ARTIFACTS = {'evaluation.json', 'oracle.json', 'oracle-stderr.log', 'calibration.json'}
LIMIT = 25 * 1024 * 1024
EXPERIMENT_CONDITIONS = (*CONDITIONS, 'learned_review')


def executable(value):
    if not isinstance(value, (str, Path)) or not str(value):
        return None
    expanded = os.path.expanduser(str(value))
    path = Path(shutil.which(expanded) or expanded).resolve()
    return str(path) if path.is_file() and os.access(path, os.X_OK) else None


def discover_codex():
    """Mirror bench discovery, including VS Code's bundled local CLI."""
    from .case_catalog import bench_root
    pinned = None
    try:
        pinned = json.loads((bench_root()/'.bench.local.json').read_text()).get('codex_binary')
    except (OSError, ValueError, AttributeError):
        pass
    for value in (os.environ.get('CODEX_BIN'), pinned, shutil.which('codex')):
        found = executable(value)
        if found:
            return found
    candidates = [Path('/Applications/Codex.app/Contents/Resources/codex')]
    for folder in (Path.home()/'.vscode/extensions', Path.home()/'.vscode-insiders/extensions'):
        candidates.extend(sorted(folder.glob('openai.chatgpt-*/bin/*/codex'),
                                 key=lambda p:p.stat().st_mtime, reverse=True))
    for path in candidates:
        found = executable(path)
        if not found:
            continue
        try:
            result = subprocess.run([found, '--version'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0 and 'codex' in result.stdout.lower():
                return found
        except (OSError, subprocess.SubprocessError):
            pass
    return None


def capture(root):
    """Copyable candidate-visible files, including tests and documentation."""
    files, skipped = {}, []
    total = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        base = Path(current)
        for name in list(dirs):
            path = base/name
            relative = path.relative_to(root).as_posix()
            if name.startswith('.') or name in EXCLUDED:
                dirs.remove(name)
                skipped.append(relative + '/')
            elif path.is_symlink():
                raise EvidenceError('候选目录不支持符号链接：' + relative)
        for name in sorted(names):
            path = base/name
            relative = path.relative_to(root).as_posix()
            if name.startswith('.'):
                skipped.append(relative)
                continue
            if path.is_symlink() or not path.is_file():
                raise EvidenceError('候选输入必须是普通文件：' + relative)
            if path.stat().st_size > LIMIT - total:
                raise EvidenceError('候选输入超过 25 MiB')
            raw = path.read_bytes()
            total += len(raw)
            files[relative] = raw
            if len(files) > 1000 or total > LIMIT:
                raise EvidenceError('候选输入超过 1000 文件或 25 MiB')
    return files, sorted(skipped)


def inventory(files):
    return {name: sha(raw) for name, raw in sorted(files.items())}


def file_modes(root, files):
    return {name: 0o755 if (root/name).stat().st_mode & 0o111 else 0o644 for name in files}


def write_files(root, files, modes=None):
    root.mkdir(parents=True)
    for name, raw in files.items():
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod((modes or {}).get(name, 0o644))


class Workbench:
    def __init__(self, store, node=None, codex=None):
        self.store = archive.store_path(store)
        self.root = self.store.with_name(self.store.name + '-experiments')
        self.node = node
        self.codex = codex or discover_codex()
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.thread = None
        self.active = None

    def execution_lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        handle = (self.root/'.execution.lock').open('a')
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            raise EvidenceError('已有实验正在运行')
        return handle

    def recover(self):
        """Only mark orphaned jobs when no runner owns the interprocess lock."""
        try:
            handle = self.execution_lock()
        except EvidenceError:
            return
        try:
            for row in self.list()['items']:
                if row['status'] != 'running':
                    continue
                manifest = self.read(row['id'])
                manifest['status'] = 'interrupted'
                for job in manifest['jobs']:
                    if job['status'] in ('running', 'prepared'):
                        job['status'] = 'interrupted'
                archive.atomic_json(self.folder(row['id'])/'manifest.json', manifest)
        finally:
            handle.close()

    def folder(self, experiment_id):
        if not isinstance(experiment_id, str) or not re.fullmatch(r'e-[0-9a-f]{16}', experiment_id):
            raise EvidenceError('Invalid experiment ID')
        path = self.root/experiment_id
        if path.is_symlink() or not (path/'manifest.json').is_file():
            raise EvidenceError('Experiment not found')
        return path

    def read(self, experiment_id):
        manifest = json.loads((self.folder(experiment_id)/'manifest.json').read_text())
        manifest.pop('learning_warning', None)
        latest = self.latest_evaluation(experiment_id)
        if latest:
            summary = json.loads(latest.read_text())
            manifest['evaluation_id'] = summary['id']
            manifest['evaluated_at'] = summary['completed_at']
            for job in manifest['jobs']:
                evaluation = dict(summary['jobs'].get(job['id'], {'status':'not_evaluated'}))
                # Older evaluations already preserve exact oracle output. Derive
                # the view without rewriting their manifest, summary or scores.
                if evaluation.get('status') in {'passed','failed'} and 'scenario_progress' not in evaluation:
                    from .case_evaluation import scenario_progress
                    if re.fullmatch(r'j-[0-9]+', str(job['id'])):
                        result = latest.parent/job['id']/'oracle'/'stdout.json'
                        try:
                            evaluation['scenario_progress'] = scenario_progress(json.loads(result.read_text()))
                        except (OSError, ValueError, TypeError, AttributeError):
                            evaluation['scenario_progress'] = None
                job['evaluation'] = evaluation
                job['recorded_task_success'] = job.get('task_success', 'unscored')
                job['task_success'] = {'passed':'passed', 'failed':'failed'}.get(job['evaluation']['status'], 'unverified')
        if manifest.get('case'):
            from .learning import inventory_key, list_lessons
            try:
                manifest['failure_lessons'] = list_lessons(self.store, manifest['case']['id'],inventory_key(manifest['input_files']),sha(manifest['task'].encode('utf-8')))
            except Exception as error:
                # Optional memory must not hide existing A/D records or turn a
                # completed evaluation into a failed request.
                manifest['failure_lessons'] = []
                manifest['learning_warning'] = str(error)
        return manifest

    def latest_evaluation(self, experiment_id):
        paths = list((self.folder(experiment_id)/'evaluations').glob('v-*/summary.json'))
        return max(paths, key=lambda p:p.stat().st_mtime_ns) if paths else None

    def list(self):
        if not executable(self.codex):
            self.codex = discover_codex()
        rows = []
        for path in sorted(self.root.glob('e-*/manifest.json'), reverse=True):
            try:
                item = self.read(path.parent.name)
                rows.append({k: item[k] for k in ('id', 'label', 'created_at', 'status', 'model', 'conditions', 'jobs')})
            except (OSError, ValueError, EvidenceError):
                continue
        return dict(items=sorted(rows, key=lambda r: r['created_at'], reverse=True), codex=self.codex,
                    root=str(self.root), active=self.active, conditions=list(EXPERIMENT_CONDITIONS))

    def case_options(self):
        from .case_catalog import catalog
        return catalog()

    def prepare_repair(self, experiment_id, job_id):
        from .repair import prepare_pair
        with self.lock:
            if self.active:
                raise EvidenceError('已有运行或验证正在进行，请稍后准备修复对照')
            return prepare_pair(self, experiment_id, job_id)

    def prepare_rag(self, experiment_id, job_id):
        from .repair import prepare_pair
        with self.lock:
            if self.active:
                raise EvidenceError('已有运行或验证正在进行，请稍后准备 RAG 实验')
            return prepare_pair(self,experiment_id,job_id,treatment='rag_only',paired=False)

    def prepare_selective_case(self, data):
        from .routing import prepare_selective
        with self.lock:
            if self.active:
                raise EvidenceError('已有运行或验证正在进行，请稍后准备门控实验')
            return prepare_selective(self,data)

    def prepare_case(self, data):
        from .case_catalog import case_input
        if not isinstance(data.get('case_id'),str):
            raise EvidenceError('请选择一个案例')
        inputs = case_input(data['case_id'])
        record = inputs.pop('case_record')
        config = {k:data[k] for k in ('model','effort','timeout','repeats','conditions') if k in data}
        local = not data.get('model')
        inherit = data.get('use_local_config', False)
        if type(inherit) is not bool:
            raise EvidenceError('Invalid local configuration option')
        model_metadata = None
        if inherit and not local:
            from .case_catalog import local_models
            model_metadata = local_models()
            choice = next((r for r in model_metadata['model_choices'] if r['id']==data['model']), None)
            if not choice:
                raise EvidenceError('该模型未列在本地 Codex 模型目录中，请刷新后选择')
            effort = config.get('effort') or ('medium' if 'medium' in choice['efforts'] else choice['default_effort'])
            if not effort or effort not in choice['efforts']:
                raise EvidenceError('所选模型不支持该推理强度')
            config['effort'] = effort
        if local:
            config['model'] = 'local-default'
        manifest = self.prepare(dict(inputs, **config, mode='workspace-write', learning_case_id=record['id']))
        if local:
            manifest.update(local_codex=True, config_source='local_codex_config', effort='local-default')
        elif inherit:
            manifest.update(local_codex=True, model_override=data['model'],
                            config_source='local_codex_config_with_model_override',
                            model_catalog=dict(source=model_metadata['model_source'], fetched_at=model_metadata['models_fetched_at']))
        manifest['case'] = record
        archive.atomic_json(self.folder(manifest['id'])/'manifest.json',manifest)
        return manifest

    def prepare(self, data):
        candidate = data.get('candidate')
        if not isinstance(candidate, str) or not Path(candidate).is_absolute():
            raise EvidenceError('请输入候选代码目录的绝对路径')
        source = Path(candidate).resolve()
        if not source.is_dir():
            raise EvidenceError('候选代码目录不存在')
        for other in (self.root, self.store):
            if source == other or source in other.parents or other in source.parents:
                raise EvidenceError('候选代码与报告库、实验目录必须分开放置')
        task, model = data.get('task'), data.get('model')
        if not isinstance(task, str) or not task.strip() or len(task) > 100000:
            raise EvidenceError('请输入任务（最多 100000 字符）')
        if not isinstance(model, str) or not model.strip() or len(model) > 200:
            raise EvidenceError('请明确填写 Codex 模型')
        conditions = data.get('conditions', ['none', 'review'])
        if (not isinstance(conditions, list) or not conditions or
                any(not isinstance(c, str) or c not in EXPERIMENT_CONDITIONS for c in conditions) or len(set(conditions)) != len(conditions)):
            raise EvidenceError('Invalid report conditions')
        repeats = data.get('repeats', 1)
        timeout = data.get('timeout', 600)
        if type(repeats) is not int or not 1 <= repeats <= 3 or type(timeout) is not int or not 10 <= timeout <= 3600:
            raise EvidenceError('重复次数为 1–3；超时为 10–3600 秒')
        effort, mode = data.get('effort', 'medium'), data.get('mode', 'read-only')
        if effort not in ('low', 'medium', 'high', 'xhigh', 'max', 'ultra') or mode not in ('read-only', 'workspace-write'):
            raise EvidenceError('Invalid effort or sandbox mode')
        label = data.get('label', '')
        if not isinstance(label, str) or len(label) > 200:
            raise EvidenceError('Invalid label')
        files, skipped = capture(source)
        modes = file_modes(source, files)
        if not files:
            raise EvidenceError('候选目录没有可复制的文件')
        learning = None
        lessons = []
        if 'learned_review' in conditions:
            from .learning import inventory_key, list_lessons
            case_id = data.get('learning_case_id')
            if not isinstance(case_id,str) or not case_id:
                raise EvidenceError('失败经验条件需要从已登记的同一案例启动')
            lessons = list_lessons(self.store,case_id,inventory_key(inventory(files)),sha(task.encode('utf-8')))[:3]
            if not lessons:
                raise EvidenceError('该案例当前输入没有匹配的失败经验；先从已评分失败生成经验')
            learning = dict(condition='learned_review', lesson_ids=[lesson['id'] for lesson in lessons],
                            status='feedback-informed-development', case_id=case_id,
                            input_inventory_sha256=inventory_key(inventory(files)),
                            qualification='同任务失败反馈已暴露；不作为独立或盲测结果')
        experiment_id = 'e-' + uuid.uuid4().hex[:16]
        folder = self.root/experiment_id
        folder.mkdir(parents=True)
        try:
            write_files(folder/'input', files, modes)
            meta = archive.scan_path(folder/'input', self.store, self.node, 'web',
                                     label='实验输入 · ' + (label or experiment_id), task_id=experiment_id)['archive']
            if meta['status'] != 'parsed':
                raise EvidenceError('实验输入未完整解析；请先检查报告 ' + meta['report_id'])
            self.require_report_content(meta['report_id'], conditions)
            learned_text = ''
            if learning:
                from .learning import review_material
                learned_packet, learned_text = review_material(meta['report_id'], lessons, self.store)
                archive.atomic_json(folder/'learned-context.json',learned_packet)
                learning['context_sha256'] = sha((folder/'learned-context.json').read_bytes())
            jobs = []
            for repeat in range(1, repeats + 1):
                for condition in conditions:
                    job_id = 'j-' + str(len(jobs) + 1).zfill(3)
                    job = folder/'jobs'/job_id
                    job.mkdir(parents=True)
                    report = archive.layer_text(meta['report_id'], 'review' if condition=='learned_review' else condition, self.store)
                    if condition=='learned_review':
                        report += '\n'+learned_text
                    common = ('Work only on the candidate-visible files in this workspace. '
                              'Do not inspect sibling experiment jobs, original repositories or report stores.\n\n'
                              + task.strip() + '\n')
                    prompt = common if condition == 'none' else common + '\n<temporal-review-material>\n' + report + '\n</temporal-review-material>\n'
                    (job/'prompt.md').write_text(prompt, encoding='utf-8')
                    (job/'report.md').write_text(report, encoding='utf-8')
                    jobs.append(dict(id=job_id, repeat=repeat, condition=condition, status='prepared',
                                     prompt_sha256=sha(prompt.encode()), report_sha256=sha(report.encode()),
                                     report_characters=len(report), delivery='not_started'))
            manifest = dict(schema_version='temporal-codex-experiment-1', id=experiment_id,
                            label=label or source.name, created_at=archive.now(), status='prepared',
                            original_candidate=str(source), model=model.strip(), effort=effort, mode=mode,
                            timeout=timeout, repeats=repeats, conditions=conditions, task=task,
                            report_id=meta['report_id'], input_files=inventory(files), file_modes=modes, skipped=skipped,
                            delivery='frozen_layer_in_initial_prompt', jobs=jobs, task_success='unscored',
                            limitations=['Exploratory local runs; no hermetic filesystem read isolation.',
                                         'Sequential configured order; no blinding or randomization.',
                                         'User chooses visible code and requirements; no hidden oracle is loaded.',
                                         'A completed turn is not task success or evidence that the report was used.'])
            if learning:
                manifest['learning'] = learning
            archive.atomic_json(folder/'manifest.json', manifest)
            return manifest
        except Exception:
            shutil.rmtree(folder)
            raise

    def require_report_content(self, report_id, conditions):
        source_conditions = {'locations', 'facts', 'review', 'audit_review', 'learned_review'}
        if not source_conditions.intersection(conditions):
            return
        report = json.loads(archive.artifact(report_id, 'report.json', self.store))
        if not coverage_summary(report)['has_substantive_report']:
            raise EvidenceError('所选源码报告为空：没有命中具体源码位置，只有范围说明或通用文字。'
                                '本次实验未启动，未调用模型。请取消 B/C/D/G 及失败经验辅助条件后单独运行 A（无报告），'
                                '或选择有具体发现的案例。扫描报告：' + report_id)

    def artifact(self, experiment_id, job_id, name):
        manifest = self.read(experiment_id)
        if job_id not in {j['id'] for j in manifest['jobs']} or name not in ARTIFACTS | EVALUATION_ARTIFACTS:
            raise EvidenceError('Unknown experiment artifact')
        if name in EVALUATION_ARTIFACTS:
            latest = self.latest_evaluation(experiment_id)
            if not latest:
                return dict(text='', exists=False, truncated=False)
            path = {'evaluation.json':latest, 'oracle.json':latest.parent/job_id/'oracle/stdout.json',
                    'oracle-stderr.log':latest.parent/job_id/'oracle/stderr.log',
                    'calibration.json':latest.parent/'calibration/stdout.json'}[name]
        else:
            path = self.folder(experiment_id)/'jobs'/job_id/name
        if not path.is_file():
            return dict(text='', exists=False, truncated=False)
        with path.open('rb') as handle:
            size = path.stat().st_size
            handle.seek(max(0, size - 100000))
            text = handle.read(100000).decode('utf-8', errors='replace')
        return dict(text=text, exists=True, truncated=size > 100000)

    def evaluate(self, experiment_id):
        with self.lock:
            if self.active:
                raise EvidenceError('已有运行或验证正在进行，请稍后重试')
            manifest = json.loads((self.folder(experiment_id)/'manifest.json').read_text())
            if manifest['status'] not in TERMINAL:
                raise EvidenceError('请等待 Codex 运行结束后验证')
            handle = self.execution_lock()
            self.active = experiment_id
            self.stop.clear()
            self.thread = threading.current_thread()
        try:
            self.evaluate_manifest(manifest)
            return self.read(experiment_id)
        finally:
            with self.lock:
                self.active = None
                handle.close()

    def evaluate_manifest(self, manifest):
        from .case_evaluation import evaluate
        summary = evaluate(manifest, self.folder(manifest['id']), self.node, self.stop, self.terminate)
        if manifest.get('retry'):
            from .repair import regression_summary
            summary = regression_summary(manifest, self.folder(manifest['id']), summary)
        # Failure learning is a separate sidecar; it must not change an outcome
        # or make an otherwise completed evaluation fail.
        if summary.get('calibration_verdict')=='PASS' and any(j.get('status')=='failed' for j in summary['jobs'].values()):
            from .learning import learn
            try:
                learn(self,manifest['id'])
            except Exception as error:
                try:
                    archive.atomic_json(self.folder(manifest['id'])/'learning-error.json',dict(error=type(error).__name__+': '+str(error)))
                except OSError:
                    pass
        return summary

    def start(self, experiment_id):
        with self.lock:
            if self.active:
                raise EvidenceError('已有实验正在运行')
            manifest = self.read(experiment_id)
            if manifest['status'] != 'prepared':
                raise EvidenceError('实验只能启动一次；请准备新的重复实验')
            if manifest.get('routing'):
                from .routing import validate_routing
                validate_routing(self,manifest)
            # A repaired snapshot may no longer trigger the original scan. Both
            # retry arms deliberately receive the same current D, even if empty.
            if manifest.get('retry'):
                from .repair import validate_pair
                validate_pair(self, manifest)
            else:
                self.require_report_content(manifest['report_id'], manifest['conditions'])
            if not executable(self.codex):
                self.codex = discover_codex()
            if not self.codex:
                raise EvidenceError('未找到本地 Codex：已检查 PATH、Codex.app 和 VS Code 扩展安装目录')
            handle = self.execution_lock()
            try:
                folder = self.folder(experiment_id)
                files, _ = capture(folder/'input')
                if inventory(files) != manifest['input_files']:
                    raise EvidenceError('冻结输入已改变，请重新准备实验')
                if file_modes(folder/'input', files) != manifest['file_modes']:
                    raise EvidenceError('冻结输入的可执行权限已改变')
                archive.verify(manifest['report_id'], self.store)
                if 'learned_review' in manifest['conditions']:
                    learning = manifest.get('learning') or {}
                    context_path = folder/'learned-context.json'
                    if not context_path.is_file() or sha(context_path.read_bytes())!=learning.get('context_sha256'):
                        raise EvidenceError('冻结失败经验上下文已改变或缺失')
                    packet = json.loads(context_path.read_text())
                    if packet.get('lesson_ids')!=learning.get('lesson_ids'):
                        raise EvidenceError('冻结失败经验 ID 与上下文不一致')
                for job in manifest['jobs']:
                    directory = folder/'jobs'/job['id']
                    for name in ('prompt', 'report'):
                        if sha((directory/(name+'.md')).read_bytes()) != job[name+'_sha256']:
                            raise EvidenceError('冻结提示词或报告已改变')
                version = subprocess.run([str(self.codex), '--version'], stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, timeout=5, check=True)
                manifest['codex_cli_version'] = version.stdout.decode('utf-8', errors='replace').strip()[:1000]
                self.active = experiment_id
                self.stop.clear()
                manifest['status'] = 'running'
                archive.atomic_json(folder/'manifest.json', manifest)
                self.thread = threading.Thread(target=self.run, args=(manifest, files, handle), daemon=True)
                self.thread.start()
            except Exception:
                self.active = None
                handle.close()
                raise
            return manifest

    def cancel(self, experiment_id):
        with self.lock:
            if self.active != experiment_id:
                raise EvidenceError('该实验当前未运行')
            self.stop.set()
        return dict(cancellation_requested=True)

    def close(self):
        self.stop.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(8)

    def command(self, manifest, workspace, answer):
        command = [str(self.codex), 'exec', '--ignore-rules', '--ephemeral',
                '--json', '--color', 'never', '--skip-git-repo-check',
                '--sandbox', manifest['mode'], '-c', 'approval_policy="never"']
        if not manifest.get('local_codex'):
            command += ['--ignore-user-config', '-c', 'model_reasoning_effort=' + json.dumps(manifest['effort']),
                        '-m', manifest['model']]
        elif manifest.get('model_override'):
            command += ['-m', manifest['model_override'], '-c', 'model_reasoning_effort=' + json.dumps(manifest['effort'])]
        if manifest.get('output_schema'):
            command += ['--output-schema', manifest['output_schema']]
        return command + ['-C', str(workspace), '-o', str(answer), '-']

    @staticmethod
    def terminate(process):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        finally:
            # The CLI may exit before descendants that ignore SIGTERM do.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=3)

    def run_job(self, manifest, job, files, folder, on_update=None):
        """One isolated subprocess; caller owns lifecycle, scoring and execution lock."""
        import time
        started = time.monotonic()
        directory = folder/'jobs'/job['id']
        workspace = directory/'workspace'
        def persist():
            archive.atomic_json(folder/'manifest.json', manifest)
            if on_update:
                on_update()
        job.update(status='running', started_at=archive.now())
        persist()
        try:
            write_files(workspace, files, manifest['file_modes'])
            command = self.command(manifest, workspace, directory/'answer.md')
            job['command'] = command
            job['delivery'] = 'process_input_pending'
            with (directory/'prompt.md').open('rb') as prompt, (directory/'events.jsonl').open('wb') as stdout, (directory/'stderr.log').open('wb') as stderr:
                process = subprocess.Popen(command, cwd=str(workspace), stdin=prompt, stdout=stdout,
                                           stderr=stderr, start_new_session=True)
                job['delivery'] = 'stdin_file_attached'
                persist()
                deadline = time.monotonic() + manifest['timeout']
                status = None
                while process.poll() is None:
                    if self.stop.is_set() or time.monotonic() >= deadline:
                        status = 'cancelled' if self.stop.is_set() else 'timed_out'
                        self.terminate(process)
                        break
                    self.stop.wait(0.1)
                job['exit_code'] = process.returncode
            completed, usage = False, None
            with (directory/'events.jsonl').open(encoding='utf-8', errors='replace') as events:
                for line in events:
                    try:
                        event = json.loads(line)
                        if isinstance(event, dict) and event.get('type') == 'turn.completed':
                            completed, usage = True, event.get('usage')
                    except ValueError:
                        pass
            job.update(status=status or ('completed' if process.returncode == 0 and completed else 'failed'),
                       turn_completed=completed, usage=usage, task_success='unscored')
            try:
                after, skipped = capture(workspace)
                modes = file_modes(workspace, after)
                changes = []
                for name in sorted(set(files) | set(after)):
                    before, updated = files.get(name), after.get(name)
                    if before == updated and manifest['file_modes'].get(name) == modes.get(name):
                        continue
                    change = dict(path=name, before_sha256=sha(before) if before is not None else None,
                                  after_sha256=sha(updated) if updated is not None else None,
                                  before_mode=manifest['file_modes'].get(name), after_mode=modes.get(name))
                    try:
                        diff = ''.join(unified_diff((before or b'').decode().splitlines(True),
                                                   (updated or b'').decode().splitlines(True),
                                                   fromfile='before/'+name, tofile='after/'+name))
                        change.update(diff=diff[:100000], truncated=len(diff) > 100000)
                    except UnicodeError:
                        change['binary'] = True
                    changes.append(change)
                archive.atomic_json(directory/'changes.json', dict(files=changes, excluded=skipped))
                job['changed_files'] = len(changes)
            except (OSError, EvidenceError) as error:
                job['changes_error'] = str(error)
        except Exception as error:
            job.update(status='failed', error=str(error), task_success='unscored')
        finally:
            job['session_seconds'] = time.monotonic() - started
            job['completed_at'] = archive.now()
            archive.atomic_json(directory/'result.json', job)
            persist()

    def run(self, manifest, files, handle):
        folder = self.folder(manifest['id'])
        try:
            for job in manifest['jobs']:
                if self.stop.is_set():
                    job.update(status='cancelled', completed_at=archive.now(), task_success='unscored')
                    archive.atomic_json(folder/'jobs'/job['id']/'result.json', job)
                    continue
                self.run_job(manifest, job, files, folder)
            statuses = {j['status'] for j in manifest['jobs']}
            manifest['status'] = 'cancelled' if self.stop.is_set() else ('completed' if statuses == {'completed'} else 'failed')
        except Exception as error:
            manifest.update(status='failed', error=str(error))
        finally:
            manifest['completed_at'] = archive.now()
            archive.atomic_json(folder/'manifest.json', manifest)
            try:
                if manifest.get('case') and not self.stop.is_set():
                    self.evaluate_manifest(manifest)
            finally:
                with self.lock:
                    self.active = None
                    handle.close()
