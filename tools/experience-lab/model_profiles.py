"""Editable workspace profiles, separate from frozen runtime configuration."""
from copy import deepcopy
import hashlib
from pathlib import Path
import re
import threading

from runner import REPO, archive, checked_path, public_profiles, read
from temporal_contract_analyzer._session_runtime.model_settings import resolve_profile, validate_settings


def revision(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Profiles:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        if not self.path.exists():
            data = read(REPO/'temporal_contract_analyzer/_session_runtime/model-profiles.json')
            template = deepcopy(data['profiles'][data['default_profile']])
            for short, model in [('56', 'gpt-5.6-sol'), ('61', 'gpt-6.1-sol')]:
                for effort in ('low', 'medium', 'high'):
                    data['profiles'].setdefault('sol'+short+'-'+effort,
                        dict(deepcopy(template), model=model, reasoning_effort=effort))
            archive.atomic_json(self.path, data)

    def snapshot(self, path=None):
        with self.lock:
            source = self.path if path is None else checked_path(path, 'Model profiles file')
            data = read(source)
            for name in data['profiles']:
                resolve_profile(name, source)
            return dict(path=str(source), profiles=public_profiles(source), default_profile=data['default_profile'],
                        revision=revision(source), workspace_revision=revision(self.path))

    def save(self, body):
        with self.lock:
            source = checked_path(body.get('path'), 'Model profiles file')
            if body.get('revision') != revision(source) or body.get('workspace_revision') != revision(self.path):
                raise ValueError('Profiles changed since loading. Reload profiles before saving.')
            ident = body.get('id')
            if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', ident):
                raise ValueError('Profile ID must use 1–80 letters, digits, dots, underscores or hyphens')
            original = read(source)
            base = body.get('base_id')
            if base not in original['profiles']:
                raise ValueError('Select an existing profile as a template')
            resolve_profile(base, source)
            if type(body.get('create')) is not bool:
                raise ValueError('Specify whether this is a new profile')
            data = read(self.path)
            if body['create'] and (ident in data['profiles'] or ident in original['profiles']):
                raise ValueError('This profile ID already exists. Choose a new ID or use Edit.')
            if not body['create'] and ident != base:
                raise ValueError('Editing keeps the profile ID; use Add for a new ID')
            row = deepcopy(original['profiles'][base])
            row.update({key: body.get(key) for key in ('model', 'reasoning_effort', 'service_tier')})
            settings = validate_settings(dict(profile=ident, model=row['model'], reasoning_effort=row['reasoning_effort'],
                service_tier=row['service_tier'], provider=row['provider'], retry_policy=data['retry_policy']))
            row['model'] = settings['model']
            data['profiles'][ident] = row
            archive.atomic_json(self.path, data)
            return dict(self.snapshot(), selected=ident)
