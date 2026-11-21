'use strict';
const RunFeedback = {
    summarize(run, now = Date.now()) {
        const meta = run.meta;
        if (meta.recorded) return null;
        const cases = run.cases;
        const total = meta.config.count;
        const completed = cases.filter(c => c.finished).length;
        const requests = cases.reduce((n, c) => n + (c.completed_requests || 0), 0);
        const pending = cases.reduce((n, c) => n + (c.pending_requests || 0), 0);
        const label = meta.config.mode === 'learning' ? 'Training' : 'Testing';
        const elapsed = meta.started_at ? Math.max(0, Math.floor(((meta.finished_at ? Date.parse(meta.finished_at) : now) - Date.parse(meta.started_at)) / 1000)) : null;
        const duration = elapsed === null ? '' : ` · ${Math.floor(elapsed / 60)}m ${elapsed % 60}s elapsed`;
        const stats = `${completed} / ${total} cases finished · ${requests} model requests completed${duration}`;
        const errors = cases.filter(c => /invalid|error|failed/.test(c.status));
        if (meta.status === 'finished') {
            const success = cases.length === total && cases.every(c => c.finished && c.passed === true);
            return {kind: success ? 'success' : 'warning', terminal: true,
                title: success ? `${label} completed — all cases passed` : `${label} ended — review results`,
                text: `${stats} · ${run.passed} passed · ${run.failed} failed · ${run.unscored} unscored${errors.length ? ` · ${errors.length} execution errors` : ''}`,
                completed, total};
        }
        if (['preparation_failed', 'execution_error', 'not_monitored', 'stopped'].includes(meta.status)) {
            return {kind: 'warning', terminal: true, title: `${label}: ${meta.status.replaceAll('_', ' ')}`,
                text: meta.error || stats, completed, total};
        }
        if (meta.status === 'prepared') return {kind: 'ready', title: 'Preparation complete — ready to start',
            text: 'Click Start to begin model execution.', completed: 0, total};
        if (meta.status === 'preparing') return {kind: 'active', title: 'Preparing cases and checking evaluators',
            text: 'No model requests yet. Preparation logs update automatically.', completed: 0, total};
        if (['running', 'stopping'].includes(meta.status)) return {kind: 'active',
            title: meta.status === 'stopping' ? 'Stopping — waiting for active work to return' : `${label} in progress`,
            text: `${stats}${pending ? ` · ${pending} model request(s) in progress` : ' · processing stages'}${errors.length ? ` · ${errors.length} execution errors` : ''}`,
            completed, total};
        return null;
    },
    stage(key) {
        const labels = {routing: 'Experience routing', contract: 'Auto-Contract', extract: 'Experience extraction'};
        if (!key) return '';
        if (labels[key]) return labels[key];
        return key.replace(/^action-/, 'Repair Action ').replace(/^visible-/, 'Public checks ').replace(/^acceptance-/, 'Training acceptance ').replace(/^diagnosis-/, 'Diagnosis ');
    }
};
if (typeof module !== 'undefined') module.exports = RunFeedback;
