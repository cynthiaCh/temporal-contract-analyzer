"""Public-API coverage for structural, candidate-only reentrancy clues."""
import tempfile
from pathlib import Path
import unittest

from temporal_contract_analyzer.core import analyze_sources, scan
from temporal_contract_analyzer.layers import coverage_summary, freeze_bundle, render_layers, verify_bundle


WRITE_NOTIFY = 'state-write-inline-notification'
CALLBACK_TRANSITION = 'callback-reentrant-transition'
SNAPSHOT_SPLIT = 'snapshot-output-lifetime-split'
RULES = {WRITE_NOTIFY, CALLBACK_TRANSITION, SNAPSHOT_SPLIT}


class ReentrancyTests(unittest.TestCase):
    def report(self, source, path='unrelated-domain.js'):
        report = analyze_sources({path: source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def rules(self, report):
        return {finding['rule'] for finding in report['findings']}

    def assert_rule(self, report, rule):
        selected = [finding for finding in report['findings'] if finding['rule'] == rule]
        self.assertTrue(selected, rule)
        events = {event['id']: event for file in report['files'] for event in file['events']}
        for finding in selected:
            self.assertEqual(finding['classification'], 'review_hint_not_bug_verdict')
            self.assertTrue(finding['condition'])
            self.assertTrue(finding['review_question'])
            self.assertTrue(finding['evidence'])
            self.assertTrue(all(identifier in events for identifier in finding['evidence']))
        return [events[identifier] for finding in selected for identifier in finding['evidence']]

    def test_member_write_then_renamed_parameter_callback(self):
        report = self.report('''function alterGantry(machine, value, deliver) {
  machine.position = value;
  deliver(value);
}''')
        evidence = self.assert_rule(report, WRITE_NOTIFY)
        self.assertTrue(any(event['kind'] == 'write' and event['target'] == 'machine.position'
                            for event in evidence))
        self.assertTrue(any(event.get('callee') == 'deliver' for event in evidence))

    def test_mutator_then_loop_bound_callback_without_listener_names(self):
        report = self.report('''function recordReading(ledger, key, value, processors) {
  ledger.set(key, value);
  for (const apply of processors) {
    apply(value);
  }
}''')
        evidence = self.assert_rule(report, WRITE_NOTIFY)
        self.assertTrue(any(event.get('callee') == 'ledger.set' for event in evidence))
        self.assertTrue(any(event.get('callee') == 'apply' for event in evidence))

    def test_python_member_write_and_loop_callbacks(self):
        for source in (
            '''def alter_gantry(machine, value, deliver):
    machine.position = value
    deliver(value)
''',
            '''def record_reading(ledger, value, processors):
    ledger.append(value)
    for apply in processors:
        apply(value)
''',
        ):
            with self.subTest(source=source):
                self.assert_rule(self.report(source, 'gantry.py'), WRITE_NOTIFY)

    def test_scheduled_and_suspended_callbacks_are_not_inline_notifications(self):
        examples = {
            'microtask.js': '''function change(motor, deliver) {
  motor.position = 1;
  queueMicrotask(() => deliver(1));
}''',
            'timer.js': '''function change(motor, deliver) {
  motor.position = 1;
  setTimeout(() => deliver(1), 0);
}''',
            'await.js': '''async function change(motor, deliver) {
  motor.position = 1;
  await pause();
  deliver(1);
}''',
            'await.py': '''async def change(motor, deliver):
    motor.position = 1
    await pause()
    deliver(1)
''',
            'yield.py': '''def change(motor, deliver):
    motor.position = 1
    yield None
    deliver(1)
''',
            'scheduled.py': '''def change(motor, deliver, loop):
    motor.position = 1
    loop.call_soon(deliver, 1)
''',
        }
        for path, source in examples.items():
            with self.subTest(path=path):
                self.assertNotIn(WRITE_NOTIFY, self.rules(self.report(source, path)))

    def test_notification_before_write_and_unrelated_functions_are_not_joined(self):
        examples = (
            '''function change(motor, deliver) { deliver(1); motor.position = 1; }''',
            '''function change(motor) { motor.position = 1; }
function unrelated(deliver) { deliver(1); }''',
            '''function change(motor, deliver) {
  motor.position = 1;
  function deferred() { deliver(1); }
  return deferred;
}''',
            '''const text = "motor.position = 1; deliver(1)";
// function change(motor, deliver) { motor.position = 1; deliver(1); }
''',
        )
        for source in examples:
            with self.subTest(source=source):
                self.assertNotIn(WRITE_NOTIFY, self.rules(self.report(source)))

    def test_registration_callback_can_call_a_transition_in_renamed_domain(self):
        report = self.report('''function wireGauge(bus, instrument) {
  bus.subscribe(reading => instrument.close(reading));
}''')
        evidence = self.assert_rule(report, CALLBACK_TRANSITION)
        self.assertTrue(any(event.get('callee') == 'bus.subscribe' for event in evidence))
        self.assertTrue(any(event.get('callee') == 'instrument.close' for event in evidence))

    def test_python_registration_lambda_can_call_a_transition(self):
        report = self.report('''def wire_gauge(bus, instrument):
    bus.subscribe(lambda reading: instrument.close(reading))
''', 'gauge.py')
        self.assert_rule(report, CALLBACK_TRANSITION)

    def test_generator_callbacks_do_not_execute_when_registered_callback_is_called(self):
        examples = {
            'generator.js': '''function wireGauge(bus, instrument) {
  bus.subscribe(function* () { instrument.close(); yield 1; });
}''',
            'generator.py': '''def wire_gauge(bus, instrument):
    def receive(reading):
        instrument.close()
        yield reading
    bus.subscribe(receive)
''',
        }
        for path, source in examples.items():
            with self.subTest(path=path):
                self.assertNotIn(CALLBACK_TRANSITION, self.rules(self.report(source, path)))

    def test_generator_notifications_before_yield_still_need_explicit_resumption(self):
        examples = {
            'generator.js': '''function* change(instrument, deliver) {
  instrument.position = 1;
  deliver(1);
  yield 1;
}''',
            'generator.py': '''def change(instrument, deliver):
    instrument.position = 1
    deliver(1)
    yield 1
''',
        }
        for path, source in examples.items():
            with self.subTest(path=path):
                self.assertNotIn(WRITE_NOTIFY, self.rules(self.report(source, path)))

    def test_named_registration_callback_is_scoped_to_its_binding(self):
        report = self.report('''def wire_gauge(bus, instrument):
    def process(reading):
        instrument.close(reading)
    bus.subscribe(process)
''', 'gauge.py')
        self.assert_rule(report, CALLBACK_TRANSITION)

    def test_callback_forwarding_exact_local_object_selects_transition_definitions(self):
        report = self.report('''function assemble(registry, actuator, receive) {
  registry.subscribe(value => receive(value, consolePort));
  const consolePort = {
    open(value) { actuator.start(value); },
    close() { actuator.stop(); },
  };
  return consolePort;
}''')
        evidence = self.assert_rule(report, CALLBACK_TRANSITION)
        self.assertTrue(any(event.get('callee') == 'receive' for event in evidence))
        self.assertTrue(any(event['kind'] == 'function_definition'
                            and event.get('name') in {'open', 'close'} for event in evidence))

    def test_unrelated_objects_and_scopes_do_not_supply_forwarded_transitions(self):
        examples = (
            '''function assemble(registry, receive) {
  const metrics = { sample() {} };
  registry.subscribe(value => receive(value, metrics));
  const consolePort = { open() {}, close() {} };
  return consolePort;
}''',
            '''function assemble(registry, receive) {
  const consolePort = { sample() {} };
  registry.subscribe(value => receive(value, consolePort));
}
function other() {
  const consolePort = { open() {}, close() {} };
  return consolePort;
}''',
            '''function assemble(registry, consolePort) {
  registry.subscribe(value => consolePort.inspect(value));
  function unrelated() { consolePort.close(); }
}''',
            '''function assemble(registry, consolePort) {
  registry.subscribe(value => setTimeout(() => consolePort.close(), 0));
}''',
            '''function assemble(registry, receive) {
  const consolePort = { open() {}, close() {} };
  registry.subscribe(consolePort => receive(consolePort));
  return consolePort;
}''',
            '''function assemble(registry, receive, source) {
  const consolePort = { open() {}, close() {} };
  registry.subscribe(value => {
    const consolePort = source.read();
    receive(consolePort);
  });
  return consolePort;
}''',
        )
        for source in examples:
            with self.subTest(source=source):
                self.assertNotIn(CALLBACK_TRANSITION, self.rules(self.report(source)))

    def test_capture_archive_receipt_and_projection_are_locally_associated(self):
        report = self.report('''function sealInstrument(instrument, history, dashboard) {
  const reading = instrument.measure();
  const confirmation = history.persist({ amount: reading.amount });
  dashboard.render(confirmation);
  return confirmation;
}''')
        evidence = self.assert_rule(report, SNAPSHOT_SPLIT)
        self.assertTrue(any(event['kind'] == 'write' and event['target'] == 'reading'
                            for event in evidence))
        self.assertTrue(any(event.get('callee') == 'history.persist' for event in evidence))
        self.assertTrue(any(event.get('callee') == 'dashboard.render' for event in evidence))

    def test_python_capture_then_archive_and_projection(self):
        report = self.report('''def seal_instrument(instrument, history, dashboard):
    reading = instrument.measure()
    confirmation = history.persist(reading.amount)
    dashboard.render(confirmation)
    return confirmation
''', 'instrument.py')
        self.assert_rule(report, SNAPSHOT_SPLIT)

    def test_captured_object_and_guard_still_prompt_review_instead_of_proving_validity(self):
        report = self.report('''function sealInstrument(instrument, history, dashboard) {
  const reading = { amount: instrument.amount, visit: instrument.visit };
  history.append(reading);
  if (reading.visit === instrument.visit) dashboard.show(reading);
}''')
        self.assert_rule(report, SNAPSHOT_SPLIT)
        self.assertNotIn('verdict', report)

    def test_snapshot_sink_and_ui_must_share_a_local_capture_or_return_value(self):
        examples = (
            '''function first(instrument, history) {
  const reading = instrument.measure();
  history.persist(reading);
}
function second(instrument, dashboard) {
  const reading = instrument.measure();
  dashboard.render(reading);
}''',
            '''function seal(instrument, history, dashboard, other) {
  const reading = instrument.measure();
  history.persist(reading);
  dashboard.render(other);
}''',
            '''function seal(instrument, history, dashboard, other) {
  const reading = instrument.measure();
  history.persist(other);
  dashboard.render(reading);
}''',
            '''function seal(instrument, history, dashboard) {
  const reading = instrument.measure();
  dashboard.render(reading);
  history.persist(reading);
}''',
            '''function seal(instrument, history, dashboard, other) {
  const reading = instrument.measure();
  const confirmation = other;
  history.persist(reading);
  dashboard.render(confirmation);
}''',
            '''function seal(instrument, history, dashboard, other) {
  let reading = instrument.measure();
  reading = other;
  history.persist(reading);
  dashboard.render(reading);
}''',
            '''function seal(instrument, history, dashboard, other) {
  const reading = instrument.measure();
  let confirmation = history.persist(reading);
  confirmation = other;
  dashboard.render(confirmation);
}''',
            '''function seal(instrument, history, dashboard, other) {
  const reading = instrument.measure();
  history.persist({ reading: other });
  dashboard.render(reading);
}''',
            '''function seal(instrument, history, dashboard) {
  const reading = instrument.measure();
  history.persist("reading");
  dashboard.render(reading);
}''',
            '''function seal(instrument, history, dashboard) {
  const reading = instrument.measure();
  history.persist(() => reading);
  dashboard.render(reading);
}''',
            '''function seal(instrument, history, dashboard) {
  const reading = instrument.measure();
  const confirmation = history.persist(reading);
  dashboard.render(() => confirmation);
}''',
        )
        for source in examples:
            with self.subTest(source=source):
                self.assertNotIn(SNAPSHOT_SPLIT, self.rules(self.report(source)))

    def test_new_rules_have_nonempty_shared_location_fact_and_review_inputs(self):
        report = self.report('''function build(registry, instrument, history, dashboard, receive) {
  registry.subscribe(value => receive(value, consolePort));
  const consolePort = {
    open(value) { instrument.position = value; },
    close() { instrument.position = null; },
  };
  function update(value, deliver) { instrument.position = value; deliver(value); }
  function submit() {
    const reading = instrument.measure();
    const confirmation = history.persist(reading);
    dashboard.render(confirmation);
  }
  return { consolePort, update, submit };
}''')
        self.assertTrue(RULES <= self.rules(report))
        self._assert_shared_bundle(report)

    def test_document_candidate_base_is_nonempty_without_external_contract_data(self):
        root = Path(__file__).resolve().parents[1]
        candidate = root/'test-fixtures/document-review-binding/arms/document-submit-snapshot-vanilla/base'
        report = scan(candidate)
        self.assertTrue(RULES <= self.rules(report))
        self._assert_shared_bundle(report)

    def _assert_shared_bundle(self, report):
        counts = coverage_summary(report)
        self.assertTrue(counts['has_substantive_report'])
        self.assertGreater(counts['selected_locations'], 0)
        self.assertTrue(counts['within_limit'])
        layers = render_layers(report)
        self.assertEqual(layers['none'], '')
        self.assertTrue(layers['facts'].startswith(layers['locations']))
        self.assertTrue(layers['review'].startswith(layers['facts']))
        for rule in RULES:
            self.assertNotIn(rule, layers['locations'])
            self.assertNotIn(rule, layers['facts'])
            self.assertIn(rule, layers['review'])
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)/'frozen'
            manifest = freeze_bundle(report, bundle)
            self.assertEqual(verify_bundle(bundle), manifest)
            self.assertEqual(len(manifest['selected_locations']), counts['selected_locations'])
            actual = {identifier for location in manifest['selected_locations']
                      for identifier in location['evidence_ids']}
            expected = {identifier for finding in report['findings']
                        for identifier in finding['evidence']}
            self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
