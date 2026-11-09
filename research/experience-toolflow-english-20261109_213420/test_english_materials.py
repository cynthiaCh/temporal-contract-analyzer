"""Offline translation, prompt-boundary and unchanged-routing checks."""
import ast,copy,json,unittest
from pathlib import Path
from prepare_materials import A,read,sources,main,sha
from english_validation import require_english_material
from toolflow import PREDICATES,canonical,digest,route,maintenance_prompt,extraction_prompt,public_material,reflection_prompt
from citations import catalog,fingerprint
from experience_translations import RULES,render
P=Path(read(A/'source-manifest.json')['source_batch'])

class EnglishMaterialTests(unittest.TestCase):
    def test_all_new_owned_text_is_free_of_untranslated_CJK(self):
        for path in A.rglob('*'):
            if path.is_file() and path.suffix in ['.py','.md','.json','.toml']:
                require_english_material(path.read_text(),str(path.relative_to(A)))

    def test_language_guard_rejects_untranslated_owned_material(self):
        with self.assertRaises(ValueError):require_english_material('prefix '+chr(0x4e2d),'synthetic fixture')
        self.assertEqual(require_english_material('known, unknown, contradicted','English fixture'),'known, unknown, contradicted')

    def test_routing_and_validation_function_ASTs_are_unchanged(self):
        def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
        old,new=functions(P/'toolflow.py'),functions(A/'toolflow.py')
        for name in old:
            if name not in ['extraction_prompt','maintenance_prompt','reflection_prompt']:
                self.assertEqual(old[name],new[name],name)

    def test_predicate_keys_schema_limits_and_taxonomy_meanings_are_preserved(self):
        old=ast.parse((P/'toolflow.py').read_text());assignment=next(n for n in old.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='PREDICATES')
        self.assertEqual(list(PREDICATES),list(ast.literal_eval(assignment.value)))
        for name in ['extraction.schema.json','maintenance.schema.json']:
            self.assertEqual((A/name).read_bytes(),(P/name).read_bytes())
        for old,new in zip(read(P/'taxonomy.json')['classes'],read(A/'taxonomy.json')['classes']):
            self.assertEqual({k:v for k,v in old.items() if k!='name_zh'},{k:v for k,v in new.items() if k!='name_en'})
        self.assertIn('or completion identity',PREDICATES['attempt_resource'])

    def test_versions_hashes_conditions_and_rule_lineage(self):
        for old,new in zip(read(P/'frozen-library.json'),read(A/'frozen-library.json')):
            for key in ['requires','excludes','primary_class']:self.assertEqual(old[key],new[key])
            self.assertNotEqual(old['version'],new['version']);self.assertNotEqual(old['text_sha256'],new['text_sha256'])
            self.assertEqual(new['text_sha256'],digest(new['text']))
            self.assertEqual(new['sha256'],digest(canonical({k:v for k,v in new.items() if k!='sha256'})))
            self.assertEqual(new['text'],render(new['primary_class']))
            self.assertEqual(len(read(A/'experience'/new['primary_class']/'translation-review.json')['rules']),len(RULES[new['primary_class']]))

    def test_historical_unknowns_still_fall_back_without_manual_promotion(self):
        x=read(A/'fixtures/historical-analysis.json');before=copy.deepcopy(x)
        result=route(x,sources(),read(A/'frozen-library.json'),task=sources()['TASK'],review=read(A/'fixtures/historical-semantic-review.json'))
        old=read(A/'fixtures/historical-route.json')
        self.assertEqual((result['condition'],result['reason'],result['selected']),(old['condition'],old['reason'],old['selected']))
        self.assertEqual(x,before)
        self.assertEqual([p['state'] for p in result['checks'][0]['premises']],[p['state'] for p in old['checks'][0]['premises']])

    def test_prompt_templates_are_English_and_append_exact_translated_body(self):
        src=sources();material=public_material(src['TASK'],src,{},read(A/'taxonomy.json')['classes'])
        for text in [extraction_prompt(material),reflection_prompt({'fixture':'Synthetic English input, not a real training payload'})]:
            require_english_material(text,'rendered prompt');self.assertIn('English',text)
        contract=(A/'materials/automatic-contract.md').read_text();common=maintenance_prompt(src['TASK'],contract)
        self.assertEqual(common,maintenance_prompt(src['TASK'],contract,None))
        for e in read(A/'frozen-library.json'):
            prompt=maintenance_prompt(src['TASK'],contract,e['text']);self.assertTrue(prompt.startswith(common));self.assertTrue(prompt.endswith(e['text']))
            self.assertNotIn(e['text'],(A/'prompts/preanalysis.md').read_text())

    def test_task_contract_citations_are_original_not_translated_or_reextracted(self):
        self.assertEqual((A/'materials/task.md').read_bytes(),(P/'materials/T/task.md').read_bytes())
        self.assertEqual((A/'materials/automatic-contract.md').read_bytes(),(P/'derived/automatic-contract.md').read_bytes())
        self.assertEqual(catalog(sources()),read(P/'materials/T/source-catalog.json'))
        self.assertEqual(read(A/'materials/source-catalog.json'),catalog(sources()))

    def test_deterministic_render_and_current_rules_object_language(self):
        paths=[p for root in [A/'prompts',A/'experience',A/'materials'] for p in root.rglob('*') if p.is_file()]+[A/'protocol.json',A/'frozen-library.json',A/'translation-lineage.json']
        before={str(p):sha(p) for p in paths};main();self.assertEqual(before,{str(p):sha(p) for p in paths})
        current=(A/'prompts/reflection-query-rule-object.md').read_text()
        self.assertIn('rules and unresolved',current);self.assertIn('each body once',current);self.assertIn('English',current);self.assertNotIn('Chinese preferred',current)
        self.assertIn('with a still-live cancellation signal',RULES['T4'][1][1]);self.assertIn('zero entry or entry with an already-aborted signal',RULES['T4'][-1][1])

if __name__=='__main__':unittest.main(verbosity=2)
