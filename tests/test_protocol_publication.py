"""Bounded listener identities and cache exception windows, including exclusions."""
import copy
from pathlib import Path
import tempfile
import unittest

from temporal_contract_analyzer.core import analyze_sources, compare
from temporal_contract_analyzer.layers import freeze_bundle, verify_bundle
from temporal_contract_analyzer.report import markdown, html_report
from temporal_contract_analyzer.review import focused_review


STRICT = '''function wrap(fn) {
  return function entry(...args) {
    if (fn === null) throw new Error("already called");
    var saved = fn;
    fn = null;
    saved.apply(this, args);
  };
}'''

EMITTER = '''function E() {}
E.prototype = {
 on: function(name, callback, ctx) {
  var e = this.e || (this.e = {});
  (e[name] || (e[name] = [])).push({fn: callback, ctx: ctx});
  return this;
 },
 once: function(name, callback, ctx) {
  var self = this;
  function listener() {
   self.off(name, listener);
   callback.apply(ctx, arguments);
  }
  listener._ = callback;
  return this.on(name, listener, ctx);
 },
 off: function(name, callback) {
  var e = this.e || (this.e = {});
  var evts = e[name];
  var liveEvents = [];
  if (evts && callback) {
   for (var i=0, len=evts.length; i<len; i++) {
    if (evts[i].fn !== callback && evts[i].fn._ !== callback) liveEvents.push(evts[i]);
   }
  }
  (liveEvents.length) ? e[name] = liveEvents : delete e[name];
  return this;
 }
};'''

CACHE = '''function cache(fn, equal) {
 var lastThis = null, lastArgs = null, lastResult = null;
 var isEqual = equal;
 return function entry() {
  var args = [].slice.call(arguments);
  if (!lastArgs || this !== lastThis || !isEqual(lastArgs, args)) {
   lastThis = this;
   lastArgs = args;
   lastResult = fn.apply(this, args);
  }
  return lastResult;
 };
}'''


def late(source):
    return source.replace('self.off(name, listener);\n   callback.apply(ctx, arguments);',
                          'callback.apply(ctx, arguments);\n   self.off(name, listener);')


class ProtocolPublicationTests(unittest.TestCase):
    def report(self, source, path='a.js'):
        report = analyze_sources({path: source})
        self.assertEqual(report['status'], 'parsed')
        return report

    def hints(self, source, rule):
        return [f for f in self.report(source)['findings'] if f['rule'] == rule]

    def test_null_throw_early_and_late_clear(self):
        early = self.report(STRICT)
        delayed = self.report(STRICT.replace('fn = null;\n    saved.apply(this, args);',
                                           'saved.apply(this, args);\n    fn = null;'))
        self.assertEqual(focused_review(early)['cards'], [])
        card = focused_review(delayed)['cards'][0]
        self.assertIn('拒绝', card['review_question'])
        self.assertEqual(delayed['findings'][0]['state_publication']['guard_exit'], 'throw')
        self.assertEqual(len(compare(early, delayed)['added_hints']), 1)

    def test_null_throw_blocks_reversed_comparison_and_identifier_exception(self):
        for guard in ['if (null === fn) { throw new Error("used"); }', 'if (fn === null) throw failure;']:
            source = STRICT.replace('if (fn === null) throw new Error("already called");', guard)
            self.assertEqual(len(self.hints(source, 'reentrant-state-publication')), 1)

    def test_null_throw_rejects_uncertain_or_effectful_exit(self):
        for exit_code in ['throw buildError();', 'throw new CustomError();',
                          '{ notify(); throw failure; }', '{ if (flag) throw failure; }']:
            source = STRICT.replace('throw new Error("already called");', exit_code)
            self.assertEqual(self.hints(source, 'reentrant-state-publication'), [])
        for source in [STRICT.replace('wrap(fn)', 'wrap(fn, Error)'),
                       'import Error from "other";\n' + STRICT,
                       STRICT.replace('var saved = fn;', 'var saved = fn; saved = other;')]:
            self.assertEqual(self.hints(source, 'reentrant-state-publication'), [])

    def test_null_throw_suspend_and_shadowing_are_not_guessed(self):
        sources = [STRICT.replace('function entry', 'async function entry').replace('fn = null;', 'await wait(); fn = null;'),
                   STRICT.replace('entry(...args)', 'entry(fn, ...args)'),
                   STRICT.replace('saved.apply(this, args)', 'setTimeout(() => saved.apply(this, args))')]
        for source in sources:
            self.assertEqual(self.hints(source, 'reentrant-state-publication'), [])

    def test_listener_original_is_context_and_late_detach_has_complete_card(self):
        self.assertEqual(focused_review(self.report(EMITTER))['cards'], [])
        report = self.report(late(EMITTER))
        self.assertEqual(len(focused_review(report)['cards']), 1)
        hint = self.hints(late(EMITTER), 'reentrant-listener-detach')[0]
        self.assertEqual(hint['listener_detach']['status'], 'detach_after_call')
        self.assertEqual(len(hint['evidence']), 7)
        evidence = {e['id']: e for f in report['files'] for e in f['events']}
        self.assertIn('delete e[name]', evidence[hint['listener_detach']['remove_definition']]['text'])
        self.assertIn('.push(', evidence[hint['listener_detach']['register_definition']]['text'])
        self.assertEqual(len(compare(self.report(EMITTER), report)['added_hints']), 1)

    def test_listener_names_comments_and_declaration_styles_do_not_select_case(self):
        source = late(EMITTER).replace('off', 'detach').replace('on:', 'subscribe:').replace('this.on(', 'this.subscribe(')
        source = source.replace('self', 'receiver').replace('callback', 'user').replace('listener', 'wrapped')
        source = source.replace('var ', 'let ').replace('liveEvents', 'kept').replace('.fn', '.handler').replace('fn:', 'handler:')
        source = source.replace('._', '.original').replace('this.e', 'this.entries')
        source = source.replace('function(name, user)', 'function (name, /* comment */ user)')
        self.assertEqual(len(self.hints(source, 'reentrant-listener-detach')), 1)

    def test_listener_unknown_implementations_are_not_api_name_matches(self):
        for source in [late(EMITTER).replace('delete e[name]', 'delete e["other"]'),
                       late(EMITTER).replace('liveEvents.push(evts[i])', 'liveEvents.push(callback)'),
                       late(EMITTER).replace('fn: callback', 'fn: other'),
                       late(EMITTER).replace('var self = this;', 'var self = other;'),
                       late(EMITTER).replace('self.off(name, listener)', 'self.off(other, listener)'),
                       late(EMITTER).replace('self.off(name, listener)', 'self.off(name, other)'),
                       late(EMITTER) + '\nE.prototype.off = replacement;',
                       late(EMITTER) + '\nE = replacement;',
                       late(EMITTER).replace('return this.on(name, listener, ctx);', 'name = other; return this.on(name, listener, ctx);'),
                       late(EMITTER).replace('E.prototype = {', 'E.prototype = {...other,'),
                       late(EMITTER).replace('E.prototype = {', 'E.prototype = {[unknown]: other,')]:
            with self.subTest(source=source):
                self.assertEqual(self.hints(source, 'reentrant-listener-detach'), [])

    def test_listener_defer_conditions_and_early_exit_are_unknown(self):
        for body in ['queueMicrotask(() => self.off(name, listener));',
                     'if (flag) self.off(name, listener);', 'return; self.off(name, listener);',
                     'await wait(); self.off(name, listener);']:
            source = late(EMITTER).replace('function listener()', 'async function listener()') if 'await' in body else late(EMITTER)
            source = source.replace('self.off(name, listener);', body)
            self.assertEqual(self.hints(source, 'reentrant-listener-detach'), [])

    def test_listener_shadowed_capture_and_callback_are_unknown(self):
        for signature in ['listener(self)', 'listener(callback)', 'listener(name)', 'listener(listener)']:
            self.assertEqual(self.hints(late(EMITTER).replace('listener()', signature), 'reentrant-listener-detach'), [])

    def test_cache_key_result_and_return_relations_are_visible(self):
        report = self.report(CACHE)
        finding = self.hints(CACHE, 'argument-cache-publication')[0]
        self.assertEqual(len(focused_review(report)['cards']), 1)
        self.assertEqual(finding['cache_publication']['status'], 'key_before_result')
        self.assertIn('抛错', markdown(report))
        kinds = [r['kind'] for r in report['relations']]
        self.assertEqual(kinds.count('cache_key_before_compute'), 2)
        self.assertIn('compute_before_cache_result', kinds)

    def test_cache_publish_keys_after_success_suppresses_candidate(self):
        source = CACHE.replace('lastThis = this;\n   lastArgs = args;\n   lastResult = fn.apply(this, args);',
                               'lastResult = fn.apply(this, args);\n   lastThis = this;\n   lastArgs = args;')
        self.assertEqual(self.hints(source, 'argument-cache-publication'), [])
        self.assertEqual(focused_review(self.report(source))['cards'], [])

    def test_cache_names_and_typescript_are_supported(self):
        source = CACHE.replace('lastArgs', '$key').replace('lastThis', '$receiver').replace('lastResult', '$result')
        source = source.replace('fn', 'compute').replace('var args', 'const args')
        self.assertEqual(len(self.hints(source, 'argument-cache-publication')), 1)
        self.assertEqual(len(focused_review(self.report(source, 'a.ts'))['cards']), 1)

    def test_cache_catch_and_finally_are_not_unprotected_paths(self):
        for statement in ['try { lastResult = fn.apply(this, args); } catch(e) { lastArgs = null; throw e; }',
                          'try { lastResult = fn.apply(this, args); } finally { lastArgs = null; }']:
            source = CACHE.replace('lastResult = fn.apply(this, args);', statement)
            self.assertEqual(self.hints(source, 'argument-cache-publication'), [])

    def test_cache_extra_writes_unmatched_keys_and_wrong_return_are_unknown(self):
        sources = [CACHE.replace('lastArgs = args;', 'lastArgs = other;'),
                   CACHE.replace('return lastResult;', 'return other;'),
                   CACHE.replace('lastResult = fn.apply(this, args);', 'lastResult = fn.apply(other, args);'),
                   CACHE.replace('return function entry', 'function reset(){lastArgs=null;} return function entry'),
                   CACHE.replace('var isEqual = equal;', 'var isEqual = equal; isEqual = other;'),
                   CACHE.replace('function entry()', 'function entry(lastArgs)'),
                   CACHE.replace('if (!lastArgs', 'if (extra || !lastArgs'),
                   CACHE.replace('var lastThis = null, lastArgs = null, lastResult = null;',
                                 'var lastThis = other, lastArgs = null, lastResult = null;')]
        for source in sources:
            self.assertEqual(self.hints(source, 'argument-cache-publication'), [])

    def test_cache_deferred_and_suspended_computation_are_unknown(self):
        for source in [CACHE.replace('fn.apply(this, args)', 'Promise.resolve().then(() => fn.apply(this, args))'),
                       CACHE.replace('function entry()', 'async function entry()').replace('fn.apply(this, args)', 'await fn.apply(this, args)')]:
            self.assertEqual(self.hints(source, 'argument-cache-publication'), [])

    def test_specialized_cards_require_all_relations_and_source_events(self):
        for source in [late(EMITTER), CACHE]:
            for damage in ['relations', 'event', 'uncertainty', 'file', 'evidence']:
                report = self.report(source)
                finding = next(f for f in report['findings'] if f['rule'] in {'argument-cache-publication', 'reentrant-listener-detach'})
                data = finding.get('cache_publication', finding.get('listener_detach'))
                if damage == 'relations': report['relations'] = []
                elif damage == 'event': data['callback'] = 'missing'
                elif damage == 'uncertainty': data['uncertainties'] = ['unknown']
                elif damage == 'file': report['files'][0]['status'] = 'parse_error'
                else: finding['evidence'] = []
                with self.subTest(source=source[:20], damage=damage):
                    self.assertEqual(focused_review(report)['cards'], [])

    def test_specialized_duplicate_cards_merge_without_mutating_report(self):
        report = self.report(CACHE)
        original = copy.deepcopy(report)
        finding = next(f for f in report['findings'] if f['rule'] == 'argument-cache-publication')
        duplicate = copy.deepcopy(finding); duplicate['id'] = 'duplicate'
        report['findings'].append(duplicate)
        review = focused_review(report)
        self.assertEqual(len(review['cards']), 1)
        self.assertEqual(review['summary']['merged_findings'], 1)
        report['findings'].pop()
        self.assertEqual(report, original)

    def test_new_frozen_layers_and_html_keep_source_evidence(self):
        for source in [STRICT, late(EMITTER), CACHE]:
            report = (self.report('<script setup>'+source+'</script>', 'A.vue') if source == CACHE else
                      self.report(source))
            with tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)/'bundle'
                manifest = freeze_bundle(report, folder)
                self.assertEqual(verify_bundle(folder), manifest)
                if source != STRICT:
                    self.assertIn('publication' if source == CACHE else 'listener_detach', (folder/'review.md').read_text())
            self.assertIn('时序', html_report(report))


if __name__ == '__main__':
    unittest.main()
