"""Read-only projections of archived experience development; never imports runners."""
import difflib
import json
import os
from pathlib import Path
import re

from .core import EvidenceError, ROOT

MAX_JSON = 4 * 1024 * 1024
MAX_TEXT = 120000
STAGES = [
    ('case', '开发案例', '核对任务、源码与 Contract 的依据。'),
    ('baseline', '修复与反馈来源', '查看用于开发反馈的实际运行，不与后续对照合并。'),
    ('feedback', '差异反馈', '区分要求、实际行为、保留项、退步及原因假设。'),
    ('reflection', '反思经验', '查看反思输入、经验原文与版本变化。'),
    ('validation', '回验与对照', '查看完整行为得失；每个批次保留自己的分母。'),
    ('freeze', '冻结决定', '冻结表示版本固定，不表示修复正确或经验有效。'),
]
TOP_ARTIFACTS = {
    'case': ['cohort.json', 'automatic-contract.md', 'automatic-contract-full.md', 'PLAN.md',
             'materials/task.md', 'materials/candidate/README.md', 'policy-review.md'],
    'baseline': ['behavior-vectors.json', 'actual-schedule.json'],
    'feedback': ['training-feedback.json', 'DIAGNOSIS.md', 'diagnosis.json',
                 'SEMANTIC_AUDIT.md', 'SEMANTIC_AUDIT_ADDENDUM.md'],
    'reflection': ['reflection-input.md', 'E1.md', 'NEW_EXPERIENCE.md',
                   'reflection-receipt.json', 'experience-review.json'],
    'validation': ['summary.json', 'REPORT.md', 'scope-review.json', 'tool-diagnostics.json'],
    'freeze': ['experience-freeze.json', 'acceptance.json', 'frozen-library.json',
               'experience-evidence.json', 'stop.json'],
}
DEV_ARTIFACTS = {
    'baseline': ['baseline-receipts.json'],
    'feedback': ['feedback.json'],
    'reflection': ['reflection-prompt.md', 'experience-original.md', 'experience-candidate.json'],
    'validation': ['revalidation-comparison.json'],
    'freeze': ['admission.json', 'state.json'],
}


class DevelopmentArchive:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get('TCA_DEVELOPMENT_ROOT') or ROOT/'research').expanduser().resolve()

    def path(self, batch, name='summary.json'):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,199}', batch):
            raise EvidenceError('Invalid development archive ID')
        rel = Path(batch)/name
        if rel.is_absolute() or '..' in rel.parts:
            raise EvidenceError('Invalid development artifact path')
        current = self.root
        for part in rel.parts:
            current = current/part
            if current.is_symlink():
                raise EvidenceError('Development archive symlinks are not supported')
        return current

    def json(self, batch, name, default=None):
        path = self.path(batch, name)
        if not path.is_file():
            return default
        if path.stat().st_size > MAX_JSON:
            raise EvidenceError('Development JSON exceeds read limit: ' + name)
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError) as error:
            raise EvidenceError('Cannot read development JSON: ' + name) from error

    def profile(self, batch, summary):
        if not isinstance(summary, dict):
            return None
        if 'development' in summary and 'tests' in summary:
            return 'pilot'
        if isinstance(summary.get('groups'), dict) and isinstance(summary.get('per_slot'), list) \
                and self.path(batch, 'NEW_EXPERIENCE.md').is_file():
            return 'comparison'
        if isinstance(summary.get('stages'), dict) and isinstance(summary.get('acceptance'), dict):
            return 'development'
        return None

    def list(self):
        items, warnings = [], []
        if self.root.is_dir():
            for folder in sorted(self.root.iterdir(), reverse=True):
                if not folder.is_dir() or folder.is_symlink() or folder.name.startswith('.'):
                    continue
                try:
                    summary = self.json(folder.name, 'summary.json')
                    profile = self.profile(folder.name, summary)
                    if profile:
                        items.append(self.header(folder.name, summary, profile))
                except (EvidenceError, OSError) as error:
                    warnings.append(dict(id=folder.name, error=str(error)))
        return dict(root=str(self.root), mode='archive-read-only', items=items, warnings=warnings)

    def header(self, batch, summary, profile):
        reused = summary.get('experience_frozen_no_revision') is True or \
                 (profile == 'comparison' and (summary.get('other_model_roles') or {}).get('reflection') == 0)
        title = {'pilot': '分类经验开发', 'comparison': '冻结经验对照', 'development': '经验开发与回验'}[profile]
        if profile == 'comparison' and not reused and self.path(batch, 'reflection-receipt.json').is_file():
            title = '经验修订与同题对照'
        return dict(id=batch, profile=profile, title=title,
                    case=summary.get('case'), status=summary.get('status'),
                    stop=summary.get('stop'), scope=summary.get('scope'),
                    reused=reused,
                    experience=summary.get('experience') if isinstance(summary.get('experience'), str) else None)

    def read(self, batch):
        summary = self.json(batch, 'summary.json')
        profile = self.profile(batch, summary)
        if not profile:
            raise EvidenceError('Unsupported or missing experience development archive')
        result = self.header(batch, summary, profile)
        result.update(source=str(self.path(batch).parent), mode='archive-read-only',
                      notices=['历史归档浏览；本页不启动模型、不重跑评分、不修改经验。',
                               '开发、同题对照与同源迁移分别解释；没有评分时通过率不可计算。',
                               '下列导航按材料类别组织；实际执行顺序以原始调度为准。记录存在不代表语义正确。'],
                      stages=[dict(id=key, title=title, description=description,
                                   status='unknown', rows=[], notes=[], artifacts=[]) for key, title, description in STAGES])
        stages = {stage['id']: stage for stage in result['stages']}
        artifacts = {}

        def add(stage, name, label=None):
            path = self.path(batch, name)
            if path.is_file() and not any(item['name'] == name for item in stages[stage]['artifacts']):
                item = dict(name=name, label=label or name, bytes=path.stat().st_size)
                artifacts[name] = item
                stages[stage]['artifacts'].append(item)

        for stage, names in TOP_ARTIFACTS.items():
            for name in names:
                add(stage, name)
        cohort = self.json(batch, 'cohort.json', {})
        if not isinstance(cohort, (dict, list)) or (isinstance(cohort, list) and any(not isinstance(row, dict) for row in cohort)):
            raise EvidenceError('Invalid development cohort structure')
        result['cases'] = ([{key: row.get(key) for key in ('alias', 'case', 'role', 'independent_unit_id')}
                            for row in cohort if isinstance(row, dict)] if isinstance(cohort, list)
                           else [dict(case=cohort.get('case') or summary.get('case'), role='development')])
        for row in cohort if isinstance(cohort, list) else [cohort]:
            alias = row.get('alias')
            prefix = 'materials/' + alias + '/candidate/' if isinstance(alias, str) and re.fullmatch(r'[A-Za-z0-9_-]+', alias) else 'materials/candidate/'
            files = row.get('candidate_files')
            for name in sorted(files)[:40] if isinstance(files, dict) else []:
                if isinstance(name, str) and Path(name).suffix.lower() in {'.py', '.js', '.ts', '.tsx', '.jsx', '.vue', '.md'} \
                        and not Path(name).is_absolute() and all(not part.startswith('.') for part in Path(name).parts):
                    add('case', prefix + name)
        stages['case']['status'] = 'recorded' if stages['case']['artifacts'] else 'unknown'
        if profile == 'pilot':
            self.pilot(batch, summary, result, stages, add)
        elif profile == 'comparison':
            self.comparison(batch, summary, result, stages)
        else:
            vectors = self.json(batch, 'behavior-vectors.json', [])
            for stage, condition in [('baseline', 'AUTO'), ('validation', 'AUTO_EXP')]:
                stages[stage]['rows'] = [self.run(row) for row in vectors if row.get('condition') == condition]
                stages[stage]['status'] = 'recorded' if stages[stage]['rows'] else 'unknown'
            stages['feedback']['status'] = 'recorded' if self.path(batch, 'training-feedback.json').is_file() else 'unknown'
            stages['reflection']['status'] = 'recorded' if summary.get('experience_generated') is True else 'unknown'
            acceptance = summary['acceptance']
            stages['freeze']['status'] = 'rejected' if acceptance.get('accepted') is False else 'unknown'
            stages['freeze']['notes'].append('开发接纳依据：' + str(acceptance.get('criteria', '见原始记录')))
            result['decision'] = acceptance
        if profile != 'pilot':
            result['feedback'] = self.feedback(self.json(batch, 'training-feedback.json', {}))
        for stage in ('baseline', 'validation'):
            # Only saved patches, not commands, auth/config files or executable research scripts.
            for path in sorted(self.path(batch).parent.glob('runs/*/archive/patch.diff'))[:80]:
                add(stage, path.relative_to(self.path(batch).parent).as_posix())
        result['cost'] = summary.get('all_roles_cost') or summary.get('cost_total') or summary.get('total_cost') or summary.get('costs')
        result['roles'] = self.json(batch, 'frozen-config.json', {}).get('roles') or \
                          self.json(batch, 'protocol.json', {}).get('roles')
        result['artifacts'] = list(artifacts.values())
        result['experience_diff'] = self.experience_diff(batch)
        result['experience_text'] = self.text(batch, 'NEW_EXPERIENCE.md') if 'NEW_EXPERIENCE.md' in artifacts else None
        result['links'] = self.links(batch, summary)
        return result

    @staticmethod
    def run(row, expected=None):
        score = row.get('score_result') or {}
        valid = row.get('valid_score', row.get('scoring_valid', row.get('valid', score.get('score_valid'))))
        if row.get('infrastructure_valid') is False:
            valid = False
        effects = score.get('effects') or row.get('effects') or {}
        passed, total = row.get('passed_items'), row.get('total_items')
        if expected and effects:
            total = len(expected)
            passed = sum(type(effects.get(key)) is bool and effects[key] == value for key, value in expected.items())
        verdict = score.get('verdict') or row.get('verdict')
        return dict(slot=row.get('slot'), condition=row.get('condition'), valid=valid,
                    verdict=verdict if valid is True else None, passed=passed, total=total,
                    status=row.get('execution_status') or row.get('status') or 'unknown',
                    losses=row.get('original_correct_losses') or row.get('regressions_vs_original') or
                           row.get('required_losses_vs_original') or [],
                    missing=row.get('missing') or score.get('missing') or [],
                    unknown=sum(type(effects.get(key)) is not bool for key in expected) if expected else None,
                    seconds=row.get('seconds'))

    def comparison(self, batch, summary, result, stages):
        reused = result['reused']
        feedback = self.json(batch, 'training-feedback.json', {})
        stages['baseline']['rows'] = [self.run(row) for row in feedback.get('runs', [])]
        stages['baseline']['status'] = 'not_performed' if reused else ('recorded' if feedback.get('runs') else 'unknown')
        stages['baseline']['notes'].append('这里展示反馈来源；本批 AUTO／经验组对照在第⑤步，不能冒充反思前的开发基线。')
        stages['feedback']['status'] = 'not_performed' if reused else ('recorded' if feedback else 'unknown')
        receipt = self.json(batch, 'reflection-receipt.json', {})
        stages['reflection']['status'] = ('not_performed' if reused else
                                         'recorded' if receipt.get('infrastructure_valid') is True and receipt.get('output_format_valid') is True else 'unknown')
        if reused:
            stages['reflection']['notes'].append('本批复用冻结经验，没有新增反思或训练；经验生成见来源批次。')
        stages['validation']['status'] = 'recorded'
        stages['validation']['rows'] = [self.run(row) for row in summary['per_slot']]
        stages['validation']['notes'].append('本批同题对照；保留原分母，不与来源批次或开发回验合并。')
        result['groups'] = [{key: group.get(key) for key in ('condition', 'started', 'valid_denominator', 'complete_passed', 'complete_pass_rate')}
                            for group in summary['groups'].values()]
        freeze = self.json(batch, 'experience-freeze.json', {})
        stages['freeze']['status'] = 'frozen' if freeze else 'unknown'
        stages['freeze']['notes'].append('经验版本：' + str(summary.get('experience', '见冻结记录')))
        if freeze.get('before_any_maintenance') is True:
            stages['freeze']['notes'].append('原记录声明在本批维护对照前冻结；本页面不重新裁决经验有效性。')
        result['decision'] = dict(frozen=bool(freeze), accepted=None, production_enabled=False)

    def pilot(self, batch, summary, result, stages, add):
        development = summary.get('development')
        development = development if isinstance(development, dict) else {}
        schedule = self.json(batch, 'actual-schedule.json', [])
        schedule = schedule if isinstance(schedule, list) else []
        stages['case']['notes'].append('开发案例与测试案例保留各自角色；测试标准不会从这个浏览页交付给 Agent。')
        for stage in ('baseline', 'feedback', 'reflection', 'validation', 'freeze'):
            stages[stage]['status'] = 'not_started'
        decisions, experiences, comparisons, feedback_records, contracts = [], [], [], [], []
        for alias, item in development.items():
            if not re.fullmatch(r'[A-Za-z0-9_-]+', alias):
                continue
            state = item.get('state') or {}
            analysis = item.get('preanalysis') or {}
            if analysis.get('contract'):
                contracts.append(dict(case=alias, text=analysis['contract'], primary_class=analysis.get('primary_class'),
                                      taxonomy_version=analysis.get('taxonomy_version'),
                                      obligation_labels=analysis.get('obligation_labels')))
            feedback = self.json(batch, 'development/' + alias + '/feedback.json', {})
            feedback_records.append(dict(case=alias, **self.feedback(feedback)))
            expected = {row['effect']: row['expected'] for row in feedback.get('standards', [])
                        if isinstance(row, dict) and 'effect' in row and type(row.get('expected')) is bool}
            for stage, names in DEV_ARTIFACTS.items():
                for name in names:
                    add(stage, 'development/' + alias + '/' + name)
            stages['baseline']['rows'].extend(self.run(row, expected) for row in schedule
                                               if row.get('slot') in state.get('baseline_slots', []))
            stages['validation']['rows'].extend(self.run(row, expected) for row in schedule
                                                 if row.get('slot') == state.get('revalidation_slot'))
            comparisons.append(dict(case=alias, comparison=item.get('revalidation_comparison')))
            admission = item.get('admission') or {}
            decisions.append(dict(case=alias, generated=state.get('candidate_generated'),
                                  reason=state.get('reason'), admission=admission))
            if state.get('candidate_generated') is True:
                text = self.text(batch, 'development/' + alias + '/experience-original.md')
                candidate = self.json(batch, 'development/' + alias + '/experience-candidate.json', {})
                experiences.append(dict(case=alias, text=text, version=candidate.get('version'),
                                        requires=candidate.get('requires'), excludes=candidate.get('excludes')))
            stages['feedback']['status'] = 'recorded' if stages['feedback']['artifacts'] else 'not_started'
            stages['reflection']['notes'].append(alias + '：' + ('已生成候选经验' if state.get('candidate_generated') is True else
                                                   '未生成经验；原因见开发决定，不能当作训练失败。'))
        if stages['baseline']['rows']:
            stages['baseline']['status'] = 'recorded'
        if any(row['generated'] is True for row in decisions):
            stages['reflection']['status'] = 'recorded'
        elif decisions and all(row['generated'] is False for row in decisions):
            stages['reflection']['status'] = 'not_performed'
        if stages['validation']['rows']:
            stages['validation']['status'] = 'recorded'
        freeze = self.json(batch, 'experience-freeze.json', {})
        library = summary.get('frozen_library')
        # A plan or a candidate file alone does not establish a frozen library.
        frozen = bool(freeze) and isinstance(library, list)
        stages['freeze']['status'] = 'frozen' if frozen else 'not_started'
        result.update(decision=dict(frozen=frozen, decisions=decisions, production_enabled=False),
                      experiences=experiences, comparisons=comparisons,
                      feedback_records=feedback_records,
                      contracts=contracts,
                      preparation=summary.get('preparation_failure') or summary.get('preparation_outcome'))
        if summary.get('preparation_failure'):
            stages['case']['status'] = 'blocked'
            stages['case']['notes'].append('预分析材料未通过准入；后续开发和测试未启动。')
        result['test_runs'] = [dict(case=alias, runs=[self.run(row) for row in item.get('runs', [])],
                                    route=item.get('route')) for alias, item in (summary.get('tests') or {}).items()]
        for alias in development:
            add('case', 'materials/' + alias + '/task.md')
            add('case', 'materials/' + alias + '/candidate/README.md')
        if decisions:
            stages['freeze']['notes'].append('查看每例的接纳依据及退步；冻结不等于整题通过。')

    def links(self, batch, summary):
        feedback = self.json(batch, 'training-feedback.json', {})
        freeze = self.json(batch, 'experience-freeze.json', {})
        links = []
        for source in (summary.get('source_batch'), feedback.get('source_batch'), freeze.get('source')):
            if not isinstance(source, str):
                continue
            parts = source.replace('\\', '/').split('/')
            if 'research' not in parts:
                continue
            tail = parts[parts.index('research') + 1:]
            if not tail or tail[0] == batch:
                continue
            candidate = tail[0]
            if not any(item['id'] == candidate for item in links):
                try:
                    if self.profile(candidate, self.json(candidate, 'summary.json')):
                        links.append(dict(id=candidate, label='来源批次 · ' + candidate))
                except (EvidenceError, OSError):
                    pass
        return links

    @staticmethod
    def feedback(data):
        """Expose recorded differences; boolean polarity is never inferred from names."""
        rows = []
        for index, run in enumerate(data.get('runs', [])):
            seen = set()
            for category in ('differences', 'improvements', 'regressions', 'existing_successes'):
                for item in run.get(category, []):
                    effect = item.get('effect') or item.get('relation')
                    if effect in seen:
                        continue
                    seen.add(effect)
                    expected, actual, before = item.get('expected'), item.get('actual'), item.get('original')
                    if type(expected) is not bool or type(actual) is not bool:
                        state = '未知'
                    elif actual == expected:
                        state = '改善' if type(before) is bool and before != expected else '当前符合要求'
                    else:
                        state = '退步' if type(before) is bool and before == expected else '当前不满足'
                    rows.append(dict(run=run.get('slot') or '来源运行 ' + str(index + 1),
                                     relation=item.get('relation') or effect,
                                     expected=expected, actual=actual, before=before, state=state))
            for effect in run.get('failures', []):
                if effect not in seen:
                    rows.append(dict(run=run.get('slot'), relation=effect, expected=None,
                                     actual=(run.get('effects') or {}).get(effect), before=None,
                                     state='反馈记录失败；期望值见标准'))
        standard = (data.get('standard') or {}).get('obligation') or {}
        return dict(rows=rows, standard=standard.get('statement'),
                    explanations=data.get('explanations') or data.get('E1_instruction_assessment'),
                    unknown_causes=data.get('unknown_causes'),
                    preserve_success=data.get('preserve_success'))

    def text(self, batch, name):
        path = self.path(batch, name)
        if not path.is_file():
            return None
        with path.open('r', encoding='utf-8', errors='replace') as stream:
            text = stream.read(MAX_TEXT + 1)
        return dict(text=text[:MAX_TEXT], truncated=len(text) > MAX_TEXT, name=name)

    def experience_diff(self, batch):
        if not self.path(batch, 'E1.md').is_file() or not self.path(batch, 'NEW_EXPERIENCE.md').is_file():
            return None
        before, after = self.text(batch, 'E1.md'), self.text(batch, 'NEW_EXPERIENCE.md')
        return dict(text='\n'.join(difflib.unified_diff(before['text'].splitlines(), after['text'].splitlines(),
                                                     fromfile='归档 E1', tofile='本批经验', lineterm='')),
                    truncated=before['truncated'] or after['truncated'])

    def artifact(self, batch, name):
        detail = self.read(batch)
        if name not in {item['name'] for item in detail['artifacts']}:
            raise EvidenceError('Artifact is not part of this development view')
        result = self.text(batch, name)
        if result is None:
            raise EvidenceError('Development artifact is missing')
        return result
