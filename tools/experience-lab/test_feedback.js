const assert = require('node:assert/strict');
const {test} = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');
const feedback = require('./web/feedback.js');

function fixture(status = 'running') {
    return {meta: {id: 'run-fixture', status, config: {mode: 'learning', count: 1}, started_at: '2026-11-21T06:00:00Z'},
        cases: [{id: 'case-fixture', status: 'action_running', current_stage: 'action-1', completed_requests: 4, pending_requests: 1}],
        passed: 0, failed: 0, unscored: 1};
}

test('live feedback shows measured counts and elapsed time', () => {
    const result = feedback.summarize(fixture(), Date.parse('2026-11-21T06:01:05Z'));
    assert.match(result.text, /4 model requests completed/);
    assert.match(result.text, /1 model request\(s\) in progress/);
    assert.match(result.text, /1m 5s elapsed/);
    assert.equal(result.completed, 0);
});

test('finished queue with execution errors never reports success', () => {
    const run = fixture('finished');
    run.cases[0] = {status: 'execution_invalid', finished: true, passed: null};
    const result = feedback.summarize(run);
    assert.equal(result.kind, 'warning');
    assert.match(result.text, /1 execution errors/);
    assert.doesNotMatch(result.title, /all cases passed/);
    run.cases[0] = {status: 'passed', passed: true, finished: true};
    run.passed = 1; run.unscored = 0;
    assert.equal(feedback.summarize(run).kind, 'success');
});

test('Qoder feedback labels turns and keeps HTTP request counts unknown', () => {
    const run = fixture();
    run.meta.model = {request_unit: 'model turns'};
    const result = feedback.summarize(run);
    assert.match(result.text, /4 model turns completed/);
    assert.match(result.text, /HTTP request count unknown/);
    assert.doesNotMatch(result.text, /4 model requests completed/);
});

test('completion alert appears once and stays visible in the progress panel', () => {
    const elements = new Map();
    const element = () => ({hidden: false, value: '', textContent: '', classList: {toggle() {}},
        append() {}, replaceChildren() {}, addEventListener() {}});
    const document = {getElementById(id) {if (!elements.has(id)) elements.set(id, element()); return elements.get(id);},
        createElement: element};
    const context = vm.createContext({document, fetch: () => new Promise(() => {}), fixture: fixture()});
    vm.runInContext(fs.readFileSync(__dirname+'/web/feedback.js', 'utf8'), context);
    vm.runInContext(fs.readFileSync(__dirname+'/web/app.js', 'utf8'), context);
    vm.runInContext('run=fixture; renderFeedback()', context);
    assert.equal(elements.get('run-feedback').hidden, false);
    context.fixture.meta.status = 'finished';
    context.fixture.cases[0] = {id: 'case-fixture', status: 'passed', passed: true, finished: true};
    context.fixture.passed = 1; context.fixture.unscored = 0;
    vm.runInContext('renderFeedback()', context);
    assert.match(elements.get('notice').textContent, /all cases passed/);
    assert.match(document.title, /completed/);
    elements.get('notice').textContent = '';
    vm.runInContext('renderFeedback()', context);
    assert.equal(elements.get('notice').textContent, '');
    assert.match(elements.get('feedback-title').textContent, /all cases passed/);
});
