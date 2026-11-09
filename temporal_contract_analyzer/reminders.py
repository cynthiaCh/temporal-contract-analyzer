"""Fixed, class-specific inspection questions, separate from learned experience."""
import json
from pathlib import Path

from . import taxonomy
from .core import EvidenceError, canonical, sha


def definition():
    data = json.loads(Path(__file__).with_name('contract-reminders.json').read_text(encoding='utf-8'))
    if data.get('schema_version') != 'temporal-class-reminders-7-v1' \
            or data.get('taxonomy_version') != taxonomy.VERSION \
            or not isinstance(data.get('by_label'), dict) or set(data['by_label']) != set(taxonomy.CODES) \
            or not isinstance(data.get('common'), str) or not data['common'].strip() \
            or any(not isinstance(text, str) or not text.strip() for text in data['by_label'].values()):
        raise EvidenceError('Invalid seven-label reminder definitions')
    return data


def material(obligation_labels):
    """Canonical order, no duplicate reminders, no inferred labels for unknown cases."""
    codes = taxonomy.labels(obligation_labels)
    data = definition()
    selected = [dict(code=code, text=data['by_label'][code]) for code in codes]
    names = {row['code']: row['name_zh'] for row in taxonomy.definition()['codebook']}
    text = '\n\n七类通用核查提醒（检查问题，不是该案例的标准答案）：\n'
    if selected:
        text += '\n'.join(f"[{row['code']} · {names[row['code']]}] {row['text']}" for row in selected)
    else:
        text += '当前分类未知，不追加任何类别提醒；继续依据任务与源码核查，不据此推断安全。'
    return dict(schema_version=data['schema_version'], taxonomy_version=taxonomy.VERSION,
                reminders_sha256=sha(canonical(data).encode()), selected_labels=codes,
                selected=selected, text=text)
