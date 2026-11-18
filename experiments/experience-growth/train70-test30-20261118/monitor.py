"""Render the experiment's public state; never starts jobs or calls a model."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import time

ROOT = Path(__file__).resolve().parent
POINTS = list(range(0, 71, 10))


def show(value):
    return '—' if value is None else str(value)


def render(state):
    if state.get('schema_version') != 'experience-growth-monitor-v1':
        raise ValueError('Unknown monitor schema')
    rows = state['checkpoints']
    if [r['processed_training_cases'] for r in rows] != POINTS:
        raise ValueError('Expected exactly M0 through M70 in steps of ten')
    identity = state['experiment_model']
    if identity.get('model') != 'deepseek-flash' or identity.get('reasoning_effort') != 'high':
        raise ValueError('Experiment model or reasoning effort drift in monitor state')
    status = {'ready_for_new_chat_not_started': '交接就绪，实验尚未启动',
              'running': '运行中', 'recovering': '恢复处理中',
              'admission_in_progress': '工程准入中，正式实验未启动',
              'pilot_completed': '独立小试已完成，正式实验未启动',
              'needs_engineering_attention': '已停止派发，正在处理工程问题',
              'paused_by_user': '用户已暂停', 'completed': '已完成',
              'awaiting_protocol_decision': '等待实验方法确认，正式实验未启动'}.get(state['status'], state['status'])
    lines = ['# 实时进度：70训练 / 30测试', '',
             '**状态：' + str(status) + '**', '',
             '- run_id：' + show(state.get('run_id')),
             '- 模型：' + identity['model'] + ' / ' + identity['reasoning_effort'],
             '- 已闭审训练：' + str(state['training']['closed']) + '/70',
             '- 已收尾测试：' + str(state['testing']['completed']) + '/240',
             '- 当前节点：' + show(state.get('current_checkpoint')),
             '- 当前 case / stage：' + show(state.get('current_case')) + ' / ' + show(state.get('current_stage')),
             '- 当前问题或停止原因：' + show(state.get('stop_reason')), '']
    heartbeat = state.get('updated_at')
    if heartbeat:
        stamp = datetime.fromisoformat(heartbeat.replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('Heartbeat must include timezone')
        age = max(0, int((datetime.now(timezone.utc) - stamp).total_seconds()))
        lines += ['最后心跳：' + stamp.astimezone(timezone(timedelta(hours=8))).isoformat() + '（北京时间，距今' + str(age) + '秒）。', '']
        if state['status'] in ('running', 'recovering', 'admission_in_progress') and age > 120:
            lines += ['**心跳已陈旧；不能据此认定仍在运行。请检查控制器、账本和当前stage。**', '']
    else:
        lines += ['尚无运行心跳：实验未启动，运行器尚未接入此状态接口。', '']
    money = state['finance']
    lines += ['用户报告余额约' + show(money.get('reported_start_balance_cny')) + '元；启动余额核实：' + show(money.get('confirmed_start_balance_cny')) + '元；本轮实扣观测：' + show(money.get('observed_spend_cny')) + '元。',
              '未知费用事件：' + show(money.get('unknown_usage_events')) + '。未知不能当0元；账户余额变化与逐请求估价分开。', '',
              '| 节点 | 收尾/30 | 有效Gold | PASS | 行为FAIL | 无效 | 最终准确率 | 状态 |',
              '|---|---:|---:|---:|---:|---:|---|---|']
    for row in rows:
        valid, passed, failed = row.get('valid_gold'), row.get('passed'), row.get('behavioral_failed')
        if valid is not None and (type(valid) is not int or not 0 <= valid <= 30):
            raise ValueError('Invalid Gold coverage')
        if all(v is not None for v in (valid, passed, failed)) and valid != passed + failed:
            raise ValueError('Gold count does not match PASS plus behavioural FAIL')
        accuracy = ('%.1f%%' % (100 * passed / 30)) if valid == 30 and passed is not None else '—'
        lines.append('| M' + str(row['processed_training_cases']) + ' | ' + str(row['completed']) + '/30 | ' +
                     show(valid) + ' | ' + show(passed) + ' | ' + show(failed) + ' | ' + show(row.get('invalid')) +
                     ' | ' + accuracy + ' | ' + row['status'] + ' |')
    lines += ['', '完整节点才显示最终PASS/30；缺失/无效不计行为FAIL。当前空白不是零准确率。', '',
              '[结果与曲线](RESULTS.md) · [实验方案](PLAN.md) · [全过程事件](EVENTS.jsonl)', '']
    return '\n'.join(lines)


def refresh(root):
    state = json.loads((root / 'LIVE_PROGRESS.json').read_text(encoding='utf-8'))
    body = render(state)
    destination = root / 'LIVE_PROGRESS.md'
    if destination.exists() and destination.read_text(encoding='utf-8') == body:
        return False
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=root,
                                         prefix='.progress-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--interval', type=float, default=10)
    args = parser.parse_args()
    if args.interval < 1:
        parser.error('--interval must be at least one second')
    try:
        while True:
            changed = refresh(args.root.resolve())
            if changed:
                print('Updated: ' + str(args.root.resolve() / 'LIVE_PROGRESS.md'), flush=True)
            if not args.watch:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
