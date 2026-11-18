# Evidence locations

Before editing, inspect the following candidate-visible locations together:

- `src/editors/PersonnelEditor.vue`: the lifecycle entry points and the
  `getPageConfig` and `applyConfig` methods;
- `src/components/SchemaForm.vue`: the `rule` watcher and the `mounted` hook;
- `src/services/config-service.js`: the implementation and return behavior of
  `getStaticConfig`.

Use these locations to determine which existing observable behaviors the
maintenance change must preserve. The locations are navigation evidence, not
a prescribed contract or repair. Then complete the maintenance task.
