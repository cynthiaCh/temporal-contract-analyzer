"""Project-scoped personal corrections; independent of research memory and models."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import uuid

from . import archive
from .core import EvidenceError

DETAIL_FIELDS = ('context', 'mistake', 'applicability', 'exclusions', 'related_general_id')


def store_path(store=None):
    return Path(store or os.environ.get('TCA_PERSONAL_MEMORY') or
                Path.home()/'.temporal-contract-analyzer'/'personal-memory').expanduser().resolve()


def project_path(project):
    path = Path(project).expanduser()
    if not path.is_absolute() or not path.is_dir():
        raise EvidenceError('project must be an existing absolute project directory')
    return str(path.resolve())


def terms(text):
    tokens = set(re.findall(r'[a-z0-9_]+', text.lower()))
    for run in re.findall(r'[\u3400-\u9fff]+', text):
        tokens.update(run[i:i+2] for i in range(max(1, len(run)-1)))
    return tokens


CORRECTION_INSTRUCTIONS = (
    'Compare the user correction and current task context with each candidate, considering the same '
    'object/API, scenario, requirement and scope, not just shared words. Choose add for an independent '
    'rule, revise for a correction or extension of the same rule, or noop when an existing rule already '
    'fully covers the feedback. Similar vocabulary alone is not grounds to merge. If the new feedback '
    'clearly replaces an earlier rule, revise that rule; otherwise clarify a material unresolved '
    'business conflict rather than silently overwriting it. For revise, use the exact candidate '
    'experience_id and version as expected_version; inspect its history with manage_experience '
    'when needed. Write cumulative guidance that preserves still-valid old requirements and '
    'incorporates the new correction; keep the new verbatim user words in correction, never rewrite '
    'historical quotes. Omitted optional fields retain their previous values; replace or explicitly '
    'clear obsolete fields. For add, omit experience_id and expected_version. For noop, do not write '
    'or increment a version; explain which existing rule covers the feedback. Leave unknown reasons '
    'and boundaries empty. This tool uses lexical matching only: a zero-match or top-5 result is '
    'not proof that no related rule exists. Broaden the query or list personal entries if needed. '
    'This is personal memory on any coding topic, without research approval or general-pack writes. '
    'The host coding agent makes the semantic decision; the server neither calls an LLM nor certifies it.'
)


class PersonalMemory:
    def __init__(self, store=None):
        self.root = store_path(store)

    @contextmanager
    def locked(self):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.root/'.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def read(self, experience_id, project):
        if not re.fullmatch(r'[0-9a-f]{32}', experience_id):
            raise EvidenceError('Invalid experience_id')
        path = self.root/(experience_id+'.json')
        if not path.is_file():
            raise EvidenceError('Unknown personal experience')
        row = json.loads(path.read_text(encoding='utf-8'))
        if row['project'] != project:
            raise EvidenceError('Experience belongs to another project')
        return row

    def recall(self, project, query, limit=5, offset=0):
        project = project_path(project)
        needles = terms(query)
        matches = []
        if self.root.exists():
            for path in self.root.glob('*.json'):
                row = json.loads(path.read_text(encoding='utf-8'))
                if row['project'] != project or row['deleted']:
                    continue
                current = row['history'][-1]
                text = ' '.join(current.get(key, '') for key in ('correction', 'guidance')+DETAIL_FIELDS)
                score = len(needles & terms(text))
                if needles and not score:
                    continue
                matches.append(dict(experience_id=row['experience_id'],
                                    project=project, source='personal', scope='project', read_only=False, score=score, **current))
        matches.sort(key=lambda row: (-row['score'], row['experience_id']))
        end = len(matches) if limit is None else offset+limit
        return dict(items=matches[offset:end], total=len(matches),
                    next_offset=end if end < len(matches) else None,
                    qualification='Lexical candidates, not verified applicability. Check current task/source; user corrections are not test results.')

    def prepare_correction(self, project, correction, context='', query=''):
        project = project_path(project)
        if not correction.strip():
            raise EvidenceError('A verbatim user correction is required')
        search_query = query.strip() or '\n'.join(part for part in (correction, context) if part)
        recalled = self.recall(project, search_query, limit=5)
        return dict(project=project, correction=correction, context=context, query=search_query,
                    source='personal', candidates=recalled['items'],
                    total_matches=recalled['total'], candidate_limit=5,
                    next_offset=recalled['next_offset'],
                    instructions=CORRECTION_INSTRUCTIONS,
                    write_tool='remember_correction',
                    write_defaults=dict(project=project, correction=correction,
                                        **({'context': context} if context else {})))

    def remember(self, project, correction, guidance=None, experience_id=None, expected_version=None,
                 context=None, mistake=None, applicability=None, exclusions=None, related_general_id=None):
        project = project_path(project)
        if not correction.strip():
            raise EvidenceError('A verbatim user correction is required')
        details = dict(context=context, mistake=mistake, applicability=applicability,
                       exclusions=exclusions, related_general_id=related_general_id)
        with self.locked():
            if experience_id:
                row = self.read(experience_id, project)
                self.check_version(row, expected_version)
                if row['deleted']:
                    raise EvidenceError('Restore deleted experience before revising')
            else:
                if expected_version is not None:
                    raise EvidenceError('expected_version requires experience_id')
                row = dict(experience_id=uuid.uuid4().hex, project=project, version=0,
                           deleted=False, history=[])
            previous = row['history'][-1] if row['history'] else {}
            content = dict(correction=correction,
                           guidance=previous.get('guidance', '') if guidance is None else guidance)
            content.update({key: previous.get(key, '') if value is None else value
                            for key, value in details.items()})
            if experience_id:
                if all(previous.get(key, '') == value for key, value in content.items()):
                    return row
            else:
                # Exact repeats need no new entry; semantic similarity stays with the agent.
                for path in sorted(self.root.glob('*.json')):
                    existing = json.loads(path.read_text(encoding='utf-8'))
                    if existing['project'] == project and not existing['deleted']:
                        current = existing['history'][-1]
                        if all(current.get(key, '') == value for key, value in content.items()):
                            return existing
            row['version'] += 1
            row['history'].append(dict(version=row['version'], action='record' if not experience_id else 'revise',
                                       **content, recorded_at=datetime.now(timezone.utc).isoformat()))
            archive.atomic_json(self.root/(row['experience_id']+'.json'), row)
            return row

    @staticmethod
    def check_version(row, expected_version):
        if expected_version != row['version']:
            raise EvidenceError('Experience changed or expected_version missing; read current version first')

    def manage(self, project, experience_id, action='show', expected_version=None):
        project = project_path(project)
        if action == 'show':
            return self.read(experience_id, project)
        if action not in ('delete', 'restore'):
            raise EvidenceError('Unknown personal memory action')
        with self.locked():
            row = self.read(experience_id, project)
            self.check_version(row, expected_version)
            row['version'] += 1
            previous = row['history'][-1]
            row['deleted'] = action == 'delete'
            row['history'].append(dict(version=row['version'], action=action,
                                       **{key: previous.get(key, '') for key in ('correction', 'guidance')+DETAIL_FIELDS},
                                       recorded_at=datetime.now(timezone.utc).isoformat()))
            archive.atomic_json(self.root/(row['experience_id']+'.json'), row)
            return row
