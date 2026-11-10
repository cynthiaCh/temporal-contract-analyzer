"""Optional assistance for the revealed review stage; never an oracle input."""
import copy
from pathlib import PurePosixPath
from .core import CODE_EXT, analyze_sources, sha
from .report import markdown


def attach_review_evidence(packet):
    p=copy.deepcopy(packet)
    sources={f['path']:f['text'] for f in p['files'] if f['role']=='candidate' and PurePosixPath(f['path']).suffix.lower() in CODE_EXT}
    report=analyze_sources(sources)
    if report['adapters'].get('javascript_typescript',{}).get('status')=='unavailable':
        raise ValueError('生成工具辅助材料需要 Node.js 与固定解析器；先运行 npm ci --prefix temporal_contract_analyzer/javascript')
    content=markdown(report)
    p['files']=[f for f in p['files'] if f['path']!='TEMPORAL-CONTRACT-ANALYSIS.md']
    p['files'].append(dict(path='TEMPORAL-CONTRACT-ANALYSIS.md',text=content,sha256=sha(content.encode()),role='analysis'))
    p['analysis_assistance']=dict(kind='deterministic-source-evidence',tool_version=report['tool_version'],tool_sha256=report['tool_sha256'],input_sha256=report['input_sha256'],status=report['status'],visibility='after-both-recovery-locks',not_primary_evidence=True)
    p['scope_note']=p.get('scope_note','')+' 本版本含工具辅助线索，在 01A/01B 锁定后显示；请回到源码引用，不得引用工具报告代替原始证据。此版本的 Oracle 复核属于工具辅助条件，不与无辅助结果混合。'
    return p
