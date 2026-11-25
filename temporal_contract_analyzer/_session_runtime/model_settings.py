"""Model profiles shared by preparation and the isolated runner; no network IO."""
import json
import re
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_CONFIG = Path(__file__).with_name('model-profiles.json')


def validate_settings(value):
    if not isinstance(value, dict) or set(value) != {'profile', 'model', 'reasoning_effort', 'service_tier', 'provider', 'retry_policy'}:
        raise ValueError('Invalid resolved model settings')
    if any(not isinstance(value[k], str) or not value[k].strip() for k in ('profile', 'model')):
        raise ValueError('Model/profile must be nonempty strings')
    for key in ('reasoning_effort', 'service_tier'):
        if value[key] is not None and (not isinstance(value[key], str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', value[key])):
            raise ValueError('Invalid '+key)
    provider = value['provider']
    required = {'name', 'wire_api', 'requires_openai_auth'}
    if not isinstance(provider, dict) or not required <= set(provider) or set(provider)-required-{'base_url','env_key'}:
        raise ValueError('Invalid provider fields')
    if not isinstance(provider['name'], str) or not provider['name'].strip() or provider['wire_api'] not in ('responses', 'qoder_cli') or type(provider['requires_openai_auth']) is not bool:
        raise ValueError('Only Codex Responses or Qoder CLI providers are supported')
    if provider['wire_api'] == 'qoder_cli':
        efforts = {'DeepSeek-Flash': ('low', 'high', 'max'),
                   'DeepSeek-V4-Pro': ('high', 'max'), 'MiniMax-M3.1-Flash': (),
                   'Efficient': ()}
        if set(provider) != required or provider['requires_openai_auth'] or value['model'] not in efforts or value['service_tier'] is not None:
            raise ValueError('Qoder Credits requires a supported built-in model without an API endpoint/key or service tier')
        supported = efforts[value['model']]
        if value['reasoning_effort'] is not None and value['reasoning_effort'] not in supported:
            raise ValueError('Unsupported Qoder model reasoning effort')
    if 'base_url' in provider:
        if not isinstance(provider['base_url'],str):raise ValueError('Provider base_url must be a URL string')
        u = urlsplit(provider['base_url'])
        if u.scheme not in ('https','http') or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('Provider base_url must contain no credentials, query or fragment')
    if 'env_key' in provider and (not isinstance(provider['env_key'], str) or not re.fullmatch(r'[A-Z][A-Z0-9_]*', provider['env_key'])):
        raise ValueError('Provider env_key must be an environment variable name')
    if provider.get('env_key') in {'HOME','PATH','CODEX_HOME','LANG','DIAG_CALL_ID','LD_PRELOAD','PYTHONPATH'}:
        raise ValueError('Provider credentials cannot replace runtime environment settings')
    retry = value['retry_policy']
    if not isinstance(retry, dict) or set(retry) != {'max_retries','backoff_seconds'} or type(retry['max_retries']) is not int or not 0 <= retry['max_retries'] <= 2 or type(retry['backoff_seconds']) not in (int,float) or not 0 <= retry['backoff_seconds'] <= 30:
        raise ValueError('Retry policy requires 0–2 retries and 0–30 second backoff')
    return deepcopy(value)


def resolve_profile(profile=None, config_file=None):
    data = json.loads(Path(config_file or DEFAULT_CONFIG).read_text())
    if set(data) != {'schema_version','default_profile','retry_policy','profiles'} or data['schema_version'] != 'tempoevo-model-profiles-v1':
        raise ValueError('Invalid model profile configuration')
    name = profile or data['default_profile']
    if name not in data['profiles']:raise ValueError('Unknown model profile: '+str(name))
    row = data['profiles'][name]
    if not isinstance(row, dict) or not {'model','provider'} <= set(row) or set(row)-{'model','reasoning_effort','service_tier','provider'}:
        raise ValueError('Invalid model profile fields')
    return validate_settings(dict(profile=name, model=row['model'], reasoning_effort=row.get('reasoning_effort'),
        service_tier=row.get('service_tier'), provider=row['provider'], retry_policy=data['retry_policy']))


def identity(settings):
    return {k: settings[k] for k in ('model','reasoning_effort')}


# Compatibility exports for shared infrastructure. Live sessions use frozen settings.
_DEFAULT = resolve_profile()
MODEL = _DEFAULT['model']
EFFORT = _DEFAULT['reasoning_effort']
