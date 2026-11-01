"""Daily review views of archived hints; never inferred obligations or labels.

This projection is deliberately separate from the frozen analysis/layer payloads.
All locations refer to the finding's existing syntax evidence.
"""
from .lifecycle import BOUNDARIES, words


CHANGE_QUESTIONS = {
    'reentrant-state-publication': '用户函数可能在返回前同步重入入口；需核对共享状态的写入顺序与写入值。',
    'effect-after-await': '等待期间，请求、对象生命周期或结果所属版本可能已经变化；需确认。',
    'commit-after-yield': 'yield 期间事务状态或退出路径可能变化；需确认提交与通知的要求。',
    'cleanup-handle-after-call': '右侧调用期间可能发生重入、关闭或切换；需确认句柄仍属于哪次工作。',
    'continuation-and-listener-removal': '监听可能已移除，但已开始的工作是否仍在继续，需要追踪。',
    'continuation-lifecycle-boundaries': '等待或回调期间可能关闭、卸载、重开或切换；是否属于同一生命周期待确认。',
    'continuation-guard-state-review': '关闭或重开可能改变保护状态；状态与回调是否对应同一工作待确认。',
    'continuation-retry-scheduling': '结束、取消或切换后，旧工作可能继续调度；可达性待确认。',
    'state-write-inline-notification': '同步通知期间，用户回调可能改变状态或再次进入当前操作；需确认。',
    'callback-reentrant-transition': '回调可能触发关闭、切换或重入；回调前后的状态是否仍适用待确认。',
    'snapshot-output-lifetime-split': '捕获值和输出对象可能属于不同生命周期；历史记录与当前显示要求待确认。',
    'listen-before-connect': '连接期间是否同步通知、监听是否已生效，需从 API 与调用处确认。',
    'connect-before-listen': '连接期间是否同步通知、监听是否已生效，需从 API 与调用处确认。',
    'early-return-from-async-iteration': '提前返回会改变资源使用生命周期；资源归属及关闭职责待确认。',
    'cleanup-in-finally': '退出或取消期间，清理完成状态及异常路径可能变化；需确认。',
    'asyncio-shield-call': '等待者可能被取消；共享任务是否应继续及其归属待确认。',
}


def cards(report):
    if not report:
        return []
    events = {event['id']: event for file in report['files'] for event in file['events']}
    result = []
    for finding in report['findings']:
        evidence = [events[eid] for eid in finding['evidence']]
        boundaries, effects, guards = [], [], []
        for event in evidence:
            tags = set(event.get('tags', []))
            name = event.get('callee', event.get('name', '')).rsplit('.', 1)[-1]
            if (event['kind'] in {'await', 'yield', 'async_iteration', 'resource_scope', 'returned_callback'}
                    or tags & {'continuation', 'parameter_callback', 'registration', 'notification',
                               'coordination', 'cleanup_or_cancel', 'scheduling'}
                    or words(name) & BOUNDARIES):
                boundaries.append(event['id'])
            if event['kind'] == 'write' or 'effect' in tags:
                effects.append(event['id'])
            if event['kind'] == 'guard' or 'cleanup_or_cancel' in tags:
                guards.append(event['id'])
        publication = finding.get('state_publication')
        if publication:
            boundaries = [publication['callback'], *publication['execution_path']]
            guards = [publication['guard']]
        result.append({
            'finding_id': finding['id'], 'rule': finding['rule'], 'title': finding['message'],
            'classification': 'candidate_boundary_review',
            'boundary': {'summary': '候选等待、通知、调用或退出位置；实际跨越关系待核查。',
                         'evidence_ids': boundaries or finding['evidence']},
            'possible_changes': {'summary': CHANGE_QUESTIONS.get(finding['rule'],
                                 '跨越该位置时，状态、身份或资源归属可能变化；需从仓库确认。')},
            'effects': {'summary': '候选写入或效果调用；业务含义与可达性待核查。' if effects else
                        '当前线索未定位具体效果；需追踪延续或回调中的写入、通知、清理与调度。',
                        'evidence_ids': effects},
            'requirement_protection': {'summary': finding['review_question'], 'evidence_ids': guards},
            'condition': finding['condition'], 'evidence_ids': finding['evidence'],
        })
    return result
