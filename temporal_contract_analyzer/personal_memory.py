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

DETAIL_FIELDS = ('context', 'mistake', 'applicability', 'exclusions', 'related_general_id',
                 'perspective', 'modification')


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
    'rule, update for a correction or extension of the same rule, or noop when an existing rule already '
    'fully covers the feedback. Similar vocabulary alone is not grounds to merge. If the new feedback '
    'clearly replaces an earlier rule, update that rule; otherwise clarify a material unresolved '
    'business conflict rather than silently overwriting it. For update, use the exact candidate '
    'experience_id and version as expected_version; inspect its history with read_experience '
    'when needed. Structure extracted experience as perspective (how to understand the problem, supported '
    'mechanism and important distinctions) and modification (concrete reusable repair/checking steps). '
    'Infer neither a root cause nor successful verification from a fix alone; leave unsupported explanations '
    'empty. Compare perspective and scope before reusing modification; similar edits can address different '
    'problems. Use perspective during diagnosis and modification during code changes and validation. '
    'Write cumulative perspective/modification that preserve still-valid old requirements and '
    'incorporate the new correction; keep the new verbatim user words in correction, never rewrite '
    'historical quotes. Omitted optional fields retain their previous values; replace or explicitly '
    'clear obsolete fields. For add, omit experience_id and expected_version. For noop, do not write '
    'or increment a version; identify the covering rule with its ID/current version when available. Leave unknown reasons '
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

    def read(self, project, experience_id):
        project = project_path(project)
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

    @staticmethod
    def check_version(row, expected_version):
        if type(expected_version) is not int or expected_version != row['version']:
            raise EvidenceError('Experience changed or expected_version missing; read current version first')

    def update(self, project, operation, correction=None, guidance=None, experience_id=None, expected_version=None,
               context=None, mistake=None, applicability=None, exclusions=None, related_general_id=None,
               perspective=None, modification=None):
        project = project_path(project)
        if operation not in ('add', 'update', 'delete', 'restore', 'noop'):
            raise EvidenceError('Unknown personal memory operation')
        details = dict(context=context, mistake=mistake, applicability=applicability,
                       exclusions=exclusions, related_general_id=related_general_id,
                       perspective=perspective, modification=modification)
        if operation in ('add', 'update'):
            if not isinstance(correction, str) or not correction.strip():
                raise EvidenceError('A verbatim user correction is required')
        elif correction is not None or guidance is not None or any(value is not None for value in details.values()):
            raise EvidenceError('Only add/update accept correction content')
        if operation == 'add':
            if experience_id is not None or expected_version is not None:
                raise EvidenceError('Add must not specify an existing ID or version')
        elif operation == 'noop' and experience_id is None and expected_version is None:
            return dict(operation='noop', changed=False, experience=None)
        elif (not isinstance(experience_id, str) or not re.fullmatch(r'[0-9a-f]{32}', experience_id)
              or type(expected_version) is not int or expected_version < 1):
            raise EvidenceError('Operation requires a personal experience_id and expected_version')
        if operation == 'noop':
            row = self.read(project, experience_id)
            self.check_version(row, expected_version)
            if row['deleted']:
                raise EvidenceError('Deleted experience cannot cover current feedback')
            return dict(operation='noop', changed=False, experience=row)
        with self.locked():
            if operation == 'add':
                row = dict(experience_id=uuid.uuid4().hex, project=project, version=0,
                           deleted=False, history=[])
            else:
                row = self.read(project, experience_id)
                self.check_version(row, expected_version)
            previous = row['history'][-1] if row['history'] else {}
            if operation in ('delete', 'restore'):
                deleted = operation == 'delete'
                if row['deleted'] == deleted:
                    return dict(operation='noop', changed=False, experience=row)
                row['deleted'] = deleted
                content = {key: previous.get(key, '') for key in ('correction', 'guidance')+DETAIL_FIELDS}
                action = operation
            else:
                if row['deleted']:
                    raise EvidenceError('Restore deleted experience before updating')
                content = dict(correction=correction,
                               guidance=previous.get('guidance', '') if guidance is None else guidance)
                content.update({key: previous.get(key, '') if value is None else value
                                for key, value in details.items()})
                if operation == 'update':
                    if all(previous.get(key, '') == value for key, value in content.items()):
                        return dict(operation='noop', changed=False, experience=row)
                else:
                    # Exact repeats need no new entry; semantic similarity stays with the agent.
                    for path in sorted(self.root.glob('*.json')):
                        existing = json.loads(path.read_text(encoding='utf-8'))
                        if existing['project'] == project and not existing['deleted']:
                            current = existing['history'][-1]
                            if all(current.get(key, '') == value for key, value in content.items()):
                                return dict(operation='noop', changed=False, experience=existing)
                action = 'record' if operation == 'add' else 'revise'
            row['version'] += 1
            row['history'].append(dict(version=row['version'], action=action, **content,
                                       recorded_at=datetime.now(timezone.utc).isoformat()))
            archive.atomic_json(self.root/(row['experience_id']+'.json'), row)
            return dict(operation=operation, changed=True, experience=row)
