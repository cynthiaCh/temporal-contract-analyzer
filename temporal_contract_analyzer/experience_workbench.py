"""Explicit seven-label research campaigns; never import historical executors."""
import json
from pathlib import Path
import re
import subprocess
import threading
import uuid

from . import archive, taxonomy, reminders, experience_routing as routing
from .case_catalog import case_input, case_root, inside, read
from .core import EvidenceError, canonical, sha
from .workbench import capture, executable, file_modes, inventory, write_files

RUNNING = {'analyzing', 'training', 'revalidating', 'testing'}


def implementation_inputs():
    return {name: sha(Path(__file__).with_name(name).read_bytes()) for name in
            ('experience_workbench.py', 'experience_routing.py', 'taxonomy.py', 'reminders.py',
             'case_evaluation.py', 'case_catalog.py', 'workbench.py')}


def scoring_inputs(record):
    manifest = inside(case_root(record), record['manifest'])
    case = read(manifest)
    root = manifest.parent
    reference = case['reference'] if record['adapter'] == 'python' else case['references']['bounded']
    files = {str(manifest): sha(manifest.read_bytes())}
    for path in (inside(root, 'base'), inside(root, reference), inside(root, case['oracle']['probe']).parent):
        content, _ = capture(path)
        files.update({str(path/name): sha(raw) for name, raw in content.items()})
    return files


def relation_states(outcome):
    effects = outcome.get('observed_effects')
    if not isinstance(effects, dict) or not effects:
        raise EvidenceError('评分器未提供完整 observed_effects，不能判定经验改善门槛')
    failed = set(outcome.get('missing_required_effects', [])) | set(outcome.get('observed_forbidden_effects', []))
    return {key: (key not in failed if type(value) is bool else None) for key, value in effects.items()}


def delta(before, after):
    left, right = relation_states(before), relation_states(after)
    if set(left) != set(right):
        raise EvidenceError('行为向量不一致，拒绝比较')
    return dict(gained=[k for k in left if left[k] is False and right[k] is True],
                lost=[k for k in left if left[k] is True and right[k] is False],
                retained=[k for k in left if left[k] is True and right[k] is True],
                unknown=[k for k in left if left[k] is None or right[k] is None])


def reflection_schema(evidence_ids):
    strings = dict(type='array', items=dict(type='string'), minItems=1, maxItems=12)
    predicates = list(taxonomy.definition()['mechanism_predicates'])
    return dict(type='object', properties=dict(
        requires=dict(type='array', minItems=1, items=dict(type='string', enum=predicates)),
        excludes=dict(type='array', items=dict(type='string', enum=predicates)),
        rules=dict(type='array', minItems=1, maxItems=7, items=dict(type='object', properties=dict(
            body=dict(type='string', minLength=1, maxLength=1600),
            evidence_ids=dict(strings, items=dict(type='string', enum=evidence_ids)),
            preservation=dict(type='string', minLength=1, maxLength=1000),
            verification=dict(type='string', minLength=1, maxLength=1000),
            causal_status=dict(type='string', enum=['observed', 'hypothesis', 'unknown'])),
            required=['body', 'evidence_ids', 'preservation', 'verification', 'causal_status'], additionalProperties=False))),
        required=['requires', 'excludes', 'rules'], additionalProperties=False)


def render_candidate(candidate, evidence):
    if not isinstance(candidate, dict) or set(candidate) != {'requires', 'excludes', 'rules'}:
        raise EvidenceError('反思输出字段不符合 schema')
    rules = candidate['rules']
    if not isinstance(rules, list) or not 1 <= len(rules) <= 7:
        raise EvidenceError('反思须输出 1–7 条有据规则')
    text = []
    for index, rule in enumerate(rules, 1):
        if not isinstance(rule, dict) or set(rule) != {'body', 'evidence_ids', 'preservation', 'verification', 'causal_status'}:
            raise EvidenceError('规则字段不符合 schema')
        ids = rule['evidence_ids']
        if not isinstance(ids, list) or not ids or any(not isinstance(x, str) or x not in evidence for x in ids):
            raise EvidenceError('规则缺少合法开发证据')
        if rule['causal_status'] not in ('observed', 'hypothesis', 'unknown'):
            raise EvidenceError('因果状态不合法')
        for field, limit in (('body', 1600), ('preservation', 1000), ('verification', 1000)):
            if not isinstance(rule[field], str) or not rule[field].strip() or len(rule[field]) > limit:
                raise EvidenceError('规则正文、保留义务与验证要求不能为空或超限')
        text.append(f"R{index:02d} {rule['body']}\n需保留：{rule['preservation']}\n验证：{rule['verification']}\n因果状态：{rule['causal_status']}")
    return '\n\n'.join(text)


class ExperienceWorkbench:
    def __init__(self, workbench):
        self.runner = workbench
        self.root = workbench.store.with_name(workbench.store.name + '-experience-v2')

    def folder(self, identifier):
        if not isinstance(identifier, str) or not re.fullmatch(r'x-[0-9a-f]{16}', identifier):
            raise EvidenceError('Invalid experience campaign ID')
        path = self.root/identifier
        if path.is_symlink() or not (path/'manifest.json').is_file():
            raise EvidenceError('Experience campaign not found')
        return path

    def read(self, identifier):
        folder = self.folder(identifier)
        item = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        if item['status'] == 'stopped' and (folder/'analysis-raw.json').is_file():
            try:
                routing.validate_analysis(read(folder/'analysis-raw.json'), item['task'], item['sources'])
            except routing.CitationError as error:
                # Derived display only: do not migrate or resume frozen history.
                item['citation_issues'] = error.issues
            except (EvidenceError, ValueError, KeyError, TypeError):
                pass
        return item

    def save(self, item):
        archive.atomic_json(self.root/item['id']/'manifest.json', item)
        return item

    def list(self):
        items = [self.read(p.parent.name) for p in self.root.glob('x-*/manifest.json')]
        return dict(items=sorted(items, key=lambda x:x['created_at'], reverse=True),
                    root=str(self.root), active=self.runner.active)

    def recover(self):
        try:
            handle = self.runner.execution_lock()
        except EvidenceError:
            return
        try:
            for item in self.list()['items']:
                if item['status'] in RUNNING:
                    item.update(status='interrupted', error='服务中断；不自动续跑，请新建批次')
                    for job in item['jobs']:
                        if job['status'] == 'running':
                            job['status'] = 'interrupted'
                    self.save(item)
        finally:
            handle.close()

    def create(self, data):
        inputs = case_input(data.get('case_id'))
        model = data.get('model')
        if not isinstance(model, str) or not model.strip() or len(model) > 200:
            raise EvidenceError('请明确选择模型')
        effort = data.get('effort', 'low')
        reflection_effort = data.get('reflection_effort', 'medium')
        if any(x not in ('low', 'medium', 'high', 'xhigh', 'max', 'ultra') for x in (effort, reflection_effort)):
            raise EvidenceError('Invalid effort')
        timeout = data.get('timeout', 600)
        if type(timeout) is not int or not 10 <= timeout <= 3600:
            raise EvidenceError('每会话超时为 10–3600 秒')
        kind = data.get('kind', 'development')
        if kind not in ('development', 'test'):
            raise EvidenceError('Invalid campaign kind')
        relationship = data.get('source_relationship', '')
        if not isinstance(relationship, str) or not relationship.strip() or len(relationship) > 2000:
            raise EvidenceError('请说明来源关系及历史暴露；不同案例 ID 不代表独立留出')
        parent = None
        if kind == 'test':
            parent = self.read(data.get('parent_id'))
            if parent['kind'] != 'development' or parent['status'] != 'frozen':
                raise EvidenceError('测试必须选择已冻结的开发经验')
            self.verify(parent)
        identifier = 'x-' + uuid.uuid4().hex[:16]
        files, skipped = capture(Path(inputs['candidate']))
        if not files:
            raise EvidenceError('候选输入为空')
        if parent and (parent['case']['id'] == inputs['case_record']['id'] or
                       (parent['input_files'] == inventory(files) and parent['task'] == inputs['task'])):
            raise EvidenceError('同一开发案例不能作为迁移测试，请选择其他案例并注明来源关系')
        # Decode all candidate files, with no silent truncation or omitted source.
        try:
            sources = {name: raw.decode('utf-8') for name, raw in files.items()}
        except UnicodeError:
            raise EvidenceError('当前 v2 预分析仅支持 UTF-8 文本候选；未启动模型')
        scoring = scoring_inputs(inputs['case_record'])
        folder = self.root/identifier
        write_files(folder/'input', files, file_modes(Path(inputs['candidate']), files))
        item = dict(id=identifier, schema_version='experience-web-v2', kind=kind, status='prepared',
                    created_at=archive.now(), case=inputs['case_record'], task=inputs['task'],
                    model=model.strip(), effort=effort, reflection_effort=reflection_effort,
                    timeout=timeout, mode='workspace-write', input_files=inventory(files),
                    file_modes=file_modes(Path(inputs['candidate']), files), skipped=skipped,
                    taxonomy_version=taxonomy.VERSION, jobs=[], reviews=[],
                    sources=sources, source_relationship=relationship, scoring_inputs=scoring,
                    implementation_inputs=implementation_inputs(),
                    taxonomy_sha256=taxonomy.fingerprint(), reminders_sha256=reminders.material([])['reminders_sha256'],
                    limitations=['Exploratory local Codex runs; no hermetic filesystem read isolation.',
                                 'Fixed order and two repetitions; no sampling or generalization claim.'])
        if parent:
            item.update(parent_id=parent['id'], library=[parent['entry']])
        else:
            item['library'] = []
        protocol = {key: item[key] for key in ('kind', 'case', 'task', 'model', 'effort', 'reflection_effort',
                    'timeout', 'input_files', 'file_modes', 'sources', 'source_relationship', 'scoring_inputs',
                    'taxonomy_sha256', 'reminders_sha256', 'library', 'implementation_inputs')}
        archive.atomic_json(folder/'protocol.json', protocol)
        item['protocol_sha256'] = sha((folder/'protocol.json').read_bytes())
        return self.save(item)

    def pin(self, item, name, value):
        path = self.folder(item['id'])/name
        if path.exists():
            raise EvidenceError('冻结材料已存在，拒绝覆盖：' + name)
        archive.atomic_json(path, value)
        item.setdefault('pinned', {})[name] = sha(path.read_bytes())
        self.save(item)

    def verify(self, item):
        folder = self.folder(item['id'])
        if sha((folder/'protocol.json').read_bytes()) != item['protocol_sha256']:
            raise EvidenceError('冻结协议已改变')
        protocol = read(folder/'protocol.json')
        if any(item[key] != value for key, value in protocol.items()):
            raise EvidenceError('运行配置偏离冻结协议')
        files, _ = capture(folder/'input')
        if inventory(files) != item['input_files'] or file_modes(folder/'input', files) != item['file_modes']:
            raise EvidenceError('冻结源码或权限已改变')
        if taxonomy.fingerprint() != item['taxonomy_sha256'] or reminders.material([])['reminders_sha256'] != item['reminders_sha256']:
            raise EvidenceError('分类或提醒版本已改变，请新建批次')
        if scoring_inputs(item['case']) != item['scoring_inputs']:
            raise EvidenceError('案例或评分版本已改变，请新建批次')
        if implementation_inputs() != item['implementation_inputs']:
            raise EvidenceError('工作流或评分实现已改变，请新建批次')
        for name, digest in item.get('pinned', {}).items():
            if sha((folder/name).read_bytes()) != digest:
                raise EvidenceError('冻结阶段材料已改变：' + name)
        if 'approved-analysis.json' in item.get('pinned', {}):
            if read(folder/'approved-analysis.json') != dict(analysis=item['analysis'], review=item['analysis_review']):
                raise EvidenceError('已审核分析发生漂移')
        if 'frozen-entry.json' in item.get('pinned', {}) and read(folder/'frozen-entry.json') != item['entry']:
            raise EvidenceError('冻结经验发生漂移')
        if 'original-score.json' in item.get('pinned', {}) and read(folder/'original-score.json')['outcome'] != item['original']:
            raise EvidenceError('原始评分发生漂移')
        for job in item['jobs']:
            name = 'score-'+job['id']+'.json'
            if name in item.get('pinned', {}) and read(folder/name)['outcome'] != job['outcome']:
                raise EvidenceError('已评分行为发生漂移')

    def action(self, identifier, action, data):
        with self.runner.lock:
            if self.runner.active:
                raise EvidenceError('已有实验正在运行，请等待结束')
            handle = self.runner.execution_lock()
            try:
                item = self.read(identifier)
                try:
                    self.verify(item)
                except (EvidenceError, OSError, ValueError, KeyError) as error:
                    item.update(stopped_from=item['status'], status='stopped', error=str(error))
                    self.save(item)
                    raise
                expected = {'analyze':'prepared', 'train':'analysis_approved',
                            'revalidate':'candidate_approved', 'test':'analysis_approved'}
                if action in ('correct-citations', 'review-analysis', 'review-candidate', 'freeze'):
                    return self.decide(item, action, data)
                if action not in expected or item['status'] != expected[action]:
                    raise EvidenceError('当前阶段不能执行此操作')
                if (action == 'test') != (item['kind'] == 'test') and action != 'analyze':
                    raise EvidenceError('开发与测试阶段不可混用')
                try:
                    if not executable(self.runner.codex):
                        raise EvidenceError('未找到本地 Codex，请检查安装与登录')
                    version = subprocess.run([str(self.runner.codex), '--version'], capture_output=True,
                                             text=True, timeout=5, check=True)
                    observed = version.stdout.strip()[:1000]
                    if item.get('codex_cli_version') and item['codex_cli_version'] != observed:
                        raise EvidenceError('Codex CLI 版本已改变，请新建批次')
                except (EvidenceError, OSError, subprocess.SubprocessError) as error:
                    item.update(stopped_from=item['status'], status='stopped', error=str(error))
                    self.save(item)
                    raise
                item['codex_cli_version'] = observed
                item['status'] = {'analyze':'analyzing', 'train':'training',
                                  'revalidate':'revalidating', 'test':'testing'}[action]
                self.save(item)
                self.runner.active = identifier
                self.runner.stop.clear()
                self.runner.thread = threading.Thread(target=self.run, args=(item, action, handle), daemon=True)
                self.runner.thread.start()
                handle = None
                return item
            finally:
                if handle:
                    handle.close()

    def decide(self, item, action, data):
        expected = {'correct-citations':'analysis_citation_review', 'review-analysis':'analysis_review',
                    'review-candidate':'candidate_review', 'freeze':'ready_to_freeze'}
        if item['status'] != expected[action]:
            raise EvidenceError('当前阶段不能审核或冻结')
        if action == 'freeze':
            entry = read(self.folder(item['id'])/'candidate-entry.json')
            self.pin(item, 'frozen-entry.json', entry)
            item.update(entry=entry, status='frozen', frozen_at=archive.now())
            return self.save(item)
        if action == 'correct-citations':
            corrected, reason = data.get('analysis'), data.get('reason')
            if not isinstance(reason, str) or not reason.strip() or len(reason)>4000:
                raise EvidenceError('请填写引用修正依据')
            raw = read(self.folder(item['id'])/'analysis-raw.json')
            routing.validate_citation_correction(raw, corrected, item['task'], item['sources'])
            correction = dict(action=action, actor='human_operator', reason=reason, at=archive.now(),
                              original_issues=item['citation_issues'])
            item['analysis'] = corrected
            self.pin(item, 'corrected-analysis.json', dict(analysis=corrected, correction=correction))
            item['reviews'].append(correction)
            item.update(status='analysis_review', citation_issues=[])
            return self.save(item)
        reason, approved = data.get('reason'), data.get('approved')
        if type(approved) is not bool or not isinstance(reason, str) or not reason.strip() or len(reason) > 4000:
            raise EvidenceError('请填写明确的审核结论和依据')
        record = dict(action=action, approved=approved, reason=reason, actor='human_operator', at=archive.now())
        if approved and action == 'review-analysis':
            analysis = data.get('analysis', item['analysis'])
            routing.validate_analysis(analysis, item['task'], item['sources'])
            review = routing.review_template(analysis, item['task'], item['sources'])
            anchors = [anchor for label in analysis['obligation_labels'] for anchor in label['evidence']]
            if not anchors:
                anchors = [dict(file='TASK', line=1, quote=item['task'].splitlines()[0][:160])]
            review.update(reviewer='human_visible_input_only', approved=True, reason=reason, evidence=anchors)
            item.update(analysis=analysis, analysis_review=review)
            record['edited_from_model'] = analysis != read(self.folder(item['id'])/'analysis-raw.json')
            self.pin(item, 'approved-analysis.json', dict(analysis=analysis, review=review))
        if approved and action == 'review-candidate':
            record['candidate_sha256'] = sha((self.folder(item['id'])/'candidate-entry.json').read_bytes())
            self.pin(item, 'candidate-review.json', record)
        item['reviews'].append(record)
        item['status'] = ('analysis_approved' if action == 'review-analysis' else 'candidate_approved') if approved else 'rejected'
        return self.save(item)

    def session(self, item, role, prompt, schema=None):
        if self.runner.stop.is_set():
            raise EvidenceError('运行已取消；后续槽位未启动')
        self.verify(item)
        folder = self.folder(item['id'])
        job = dict(id='j-' + str(len(item['jobs'])+1).zfill(3), role=role, status='prepared')
        directory = folder/'jobs'/job['id']
        directory.mkdir(parents=True)
        (directory/'prompt.md').write_text(prompt, encoding='utf-8')
        job['prompt_sha256'] = sha(prompt.encode())
        if schema:
            archive.atomic_json(directory/'schema.json', schema)
        item['jobs'].append(job)
        self.save(item)
        execution = dict(item, jobs=[job], mode='read-only' if schema else 'workspace-write',
                         effort=item['reflection_effort'] if role == 'reflection' else item['effort'])
        if schema:
            execution['output_schema'] = str(directory/'schema.json')
        # run_job persists its execution manifest: use a per-session folder, so
        # its mutable manifest never overwrites the campaign or frozen protocol.
        run_folder = directory/'execution'
        run_folder.mkdir()
        (run_folder/'jobs').mkdir()
        shutil_target = run_folder/'jobs'/job['id']
        # Keep one canonical job folder for artifacts and evaluator compatibility.
        from shutil import copyfile
        shutil_target.mkdir()
        copyfile(directory/'prompt.md', shutil_target/'prompt.md')
        files, _ = capture(folder/'input')
        self.runner.run_job(execution, job, files, run_folder, on_update=lambda:self.save(item))
        job['artifact_root'] = str(shutil_target.relative_to(folder))
        self.save(item)
        self.verify(item)
        if job['status'] != 'completed' or job.get('changes_error'):
            raise EvidenceError('模型未完整完成或候选归档失败；不重试，后续槽位未启动')
        if schema and job.get('changed_files'):
            raise EvidenceError('只读分析修改了候选文件，停止')
        answer = (shutil_target/'answer.md').read_text(encoding='utf-8')
        if schema:
            return json.loads(answer)
        self.score(item, job, execution, run_folder)
        return job

    def score(self, item, job, execution, run_folder):
        from .case_evaluation import evaluate
        self.verify(item)
        result = evaluate(execution, run_folder, self.runner.node, self.runner.stop, self.runner.terminate)
        job['evaluation'] = result
        self.save(item)
        row = result['jobs'][job['id']]
        if row['status'] not in ('passed', 'failed'):
            raise EvidenceError('行为评分无效：' + row.get('reason', 'unknown'))
        outcome = read(run_folder/row['result_path'])
        relation_states(outcome)
        job.update(outcome=outcome, task_success=row['status'], original_delta=delta(item['original'], outcome))
        self.pin(item, 'score-'+job['id']+'.json', dict(outcome=outcome, evaluation=result))
        self.verify(item)
        self.save(item)

    def original_score(self, item):
        from .case_evaluation import evaluate
        folder = self.folder(item['id'])/'original'
        files, _ = capture(self.folder(item['id'])/'input')
        write_files(folder/'jobs/j-000/workspace', files, item['file_modes'])
        execution = dict(item, jobs=[dict(id='j-000', status='completed')])
        result = evaluate(execution, folder, self.runner.node, self.runner.stop, self.runner.terminate)
        row = result['jobs']['j-000']
        if row['status'] not in ('passed', 'failed'):
            raise EvidenceError('原始版本评分无效：' + row.get('reason', 'unknown'))
        item['original'] = read(folder/row['result_path'])
        relation_states(item['original'])
        self.pin(item, 'original-score.json', dict(outcome=item['original'], evaluation=result))
        self.verify(item)

    def run(self, item, action, handle):
        try:
            if action == 'analyze':
                analysis = self.session(item, 'analysis', routing.analysis_prompt(item['task'], item['sources']), taxonomy.analysis_schema())
                self.pin(item, 'analysis-raw.json', analysis)
                try:
                    routing.validate_analysis(analysis, item['task'], item['sources'])
                except routing.CitationError as error:
                    item.update(analysis=analysis, citation_issues=error.issues, status='analysis_citation_review')
                else:
                    item.update(analysis=analysis, status='analysis_review')
            elif action == 'train':
                self.train(item)
            elif action == 'revalidate':
                self.revalidate(item)
            elif action == 'test':
                self.test(item)
            if self.runner.stop.is_set():
                item['status'] = 'cancelled'
        except Exception as error:
            item.update(status='cancelled' if self.runner.stop.is_set() else 'stopped', error=str(error))
        finally:
            self.save(item)
            with self.runner.lock:
                self.runner.active = None
                handle.close()

    def maintenance(self, item, experience=None):
        return ('Work only on candidate-visible files. Do not read sibling campaigns, original repositories, '
                'report stores, oracle or reference implementations.\n\n' +
                routing.maintenance_prompt(item['task'], item['analysis']['contract'], experience,
                    obligation_labels=[x['code'] for x in item['analysis']['obligation_labels']]))

    def train(self, item):
        self.original_score(item)
        for repeat in (1, 2):
            self.session(item, 'AUTO-'+str(repeat), self.maintenance(item))
        baselines = [j for j in item['jobs'] if j['role'].startswith('AUTO-')]
        if all(j['task_success'] == 'passed' for j in baselines):
            item.update(status='auto_passed', admission=dict(eligible=False, reason='两次 AUTO 已通过；本批不搜索经验'))
            return
        evidence = {'task':item['task'], 'sources':item['sources'], 'original':item['original']}
        folder = self.folder(item['id'])
        for job in baselines:
            artifacts = folder/job['artifact_root']
            evidence[job['role']] = dict(outcome=job['outcome'], delta=job['original_delta'],
                changes=read(artifacts/'changes.json'), answer=(artifacts/'answer.md').read_text(encoding='utf-8'))
        self.pin(item, 'reflection-evidence.json', evidence)
        prompt = ('根据以下开发证据生成通用经验规则，按 schema 输出 JSON。\n'
                  '区分文档要求、源码事实、观测结果和原因假设；没有独立因果证据不要宣称已验证原因。\n'
                  '明确适用/排除条件，每条规则引用 evidence_ids，保留原有成功，处理反例，写出可证伪的事件顺序验证。\n'
                  '不能把源码缺陷当作应保留政策，不从资源归属推导另一记录的业务归属。\n'
                  '经验正文、保留义务及验证要求不得含案例 ID、专用字段、断言名、源码路径、参考补丁或标准答案。\n'
                  '关注同步回调和清理尚不可用的窗口；区分事件接纳、延迟处理、审计与显示。\n'
                  '这些材料仅属于开发侧，模型公开回答是待核查声称。\n' + canonical(evidence))
        candidate = self.session(item, 'reflection', prompt, reflection_schema(list(evidence)))
        self.pin(item, 'candidate-object.json', candidate)
        text = render_candidate(candidate, evidence)
        entry = routing.freeze_entry(text, [x['code'] for x in item['analysis']['obligation_labels']],
                                    candidate['requires'], candidate['excludes'], item['id'])
        self.pin(item, 'candidate-entry.json', entry)
        item.update(candidate=candidate, candidate_text=text, status='candidate_review')

    def revalidate(self, item):
        entry = read(self.folder(item['id'])/'candidate-entry.json')
        for repeat in (1, 2):
            self.session(item, 'REVALIDATE-'+str(repeat), self.maintenance(item, entry['text']))
        autos = [j for j in item['jobs'] if j['role'].startswith('AUTO-')]
        repairs = [j for j in item['jobs'] if j['role'].startswith('REVALIDATE-')]
        comparisons = [dict(revalidation=r['id'], baseline=b['id'], **delta(b['outcome'], r['outcome']))
                       for r in repairs for b in autos]
        eligible = any(row['gained'] for row in comparisons)
        item.update(comparisons=comparisons, admission=dict(eligible=eligible,
                    reason='有开发行为改善；仍须查看全部退步' if eligible else '两次回验均未观察到相对 AUTO 的新增通过，测试未启动'),
                    status='ready_to_freeze' if eligible else 'no_improvement')
        self.pin(item, 'development-admission.json', dict(comparisons=comparisons, admission=item['admission']))

    def test(self, item):
        decision = routing.route(item['analysis'], item['sources'], item['library'],
                                 task=item['task'], review=item['analysis_review'])
        experience = item['library'][0]['text'] if decision['selected'] else None
        a, b = self.maintenance(item), self.maintenance(item, experience)
        item.update(route=decision, prompts_identical=a == b)
        self.pin(item, 'test-inputs.json', dict(route=decision, A=a, B=b,
                    analysis=item['analysis'], review=item['analysis_review'], library=item['library']))
        self.original_score(item)
        for role, prompt in [('B1', b), ('A1', a), ('A2', a), ('B2', b)]:
            self.session(item, role, prompt)
        jobs = {job['role']: job for job in item['jobs']}
        item['test_comparisons'] = [dict(repeat=repeat,
            **delta(jobs['A'+str(repeat)]['outcome'], jobs['B'+str(repeat)]['outcome'])) for repeat in (1, 2)]
        item['test_summary'] = {arm: dict(valid=2, whole_passes=sum(jobs[arm+str(n)]['task_success']=='passed' for n in (1, 2)))
                                for arm in ('A', 'B')}
        self.pin(item, 'test-summary.json', dict(groups=item['test_summary'], comparisons=item['test_comparisons'],
                  prompts_identical=item['prompts_identical'], route=item['route']))
        item['status'] = 'completed'

    def artifact(self, identifier, name):
        folder = self.folder(identifier)
        item = self.read(identifier)
        allowed = {'protocol.json', *item.get('pinned', {})}
        for job in item['jobs']:
            allowed.add('jobs/'+job['id']+'/prompt.md')
            base = job.get('artifact_root', 'jobs/'+job['id']+'/execution/jobs/'+job['id'])
            allowed.update(base+'/'+file for file in ('prompt.md', 'answer.md', 'events.jsonl', 'stderr.log', 'changes.json', 'result.json'))
        if name not in allowed:
            raise EvidenceError('Unknown experience artifact')
        path = folder/name
        if not path.is_file() or path.is_symlink():
            return dict(text='', exists=False, truncated=False)
        with path.open('rb') as stream:
            raw = stream.read(120001)
        return dict(text=raw[:120000].decode('utf-8', errors='replace'), exists=True, truncated=len(raw)>120000)
