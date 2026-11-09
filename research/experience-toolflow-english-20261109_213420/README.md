English research prompt and experience materials

Use this version as the English material source for subsequent authorized research batches. It replaces Chinese prompt wording in the latest direct-routing workflow without editing historical experiments or the production experience registry.

Included material:

- `toolflow.py`: English predicate definitions, extraction/classification instructions, maintenance requirements and translated compatibility reflection helper. Routing and evidence validation functions retain the original implementation.
- `prompts/preanalysis.md`: complete English source-only extraction/classification prompt, with the current candidate AST, exact source-span catalog, English taxonomy and predicate dictionary. No experience or evaluator content is included.
- `prompts/maintenance-AUTO.md`: English maintenance prompt using the unchanged original English task and historical automatic Contract as rendering fixtures.
- `prompts/maintenance-with-T1.md` and `maintenance-with-T4.md`: examples with the corresponding complete English experience translation appended. These examples are not route selections. Actual execution must select zero or one experience using an admitted analysis and unchanged conservative routing.
- `prompts/reflection-query-rule-object.md`: English instructions for the current training-only single-body rules-object interface. The separately translated legacy compatibility helper does not replace this protocol. No reflection session is launched.
- `frozen-library.json`: two English derived translations. Every entry retains its original primary class, required predicates and exclusions, but has a new version and body/entry hashes.
- `experience/*/translation-review.json`: rule-by-rule translation lineage and AI-assisted execution-agent review. English bodies are derived translations, not new model-generated candidates or new training achievements.
- `protocol.json`, `source-manifest.json`, `summary.json` and `integrity.json`: scope, provenance, checks and preservation evidence.

Build and validate without model execution:

```bash
python3 -B research/experience-toolflow-english-20261109_213420/prepare_materials.py
python3 -B -m unittest discover -s research/experience-toolflow-english-20261109_213420 -p 'test_*.py' -v
```

The builder rejects untranslated CJK text in owned model-facing materials. It does not translate evidence automatically, invent facts or promote unknown premises. Source quotations and opaque IDs remain exact. The current task, source/docs and automatic Contract were already English and are copied byte-for-byte.

All generated prose is requested in English. Class labels use `name_en` instead of `name_zh`; class IDs, mechanism lists and definitions retain their meaning. Output schemas, character limits, model names, effort, resource budgets and conservative fallback rules are unchanged.

No model, scorer, scheduler or experiment is started by these commands. Historical analysis and route records are offline regression fixtures only. In particular, their four unknown prerequisites remain unknown and still cause AUTO fallback. No language-performance, applicability-recall or repair-benefit claim is made for the English version.

For a future execution, create a fresh authorized batch and freeze the English material hashes before its first model call. Do not resume or relabel the completed historical batch. Existing frozen Chinese inputs, raw model outputs, patches, usage and scores remain unchanged.
