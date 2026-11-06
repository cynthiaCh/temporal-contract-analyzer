# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## package.json:1-6
```
{
  "name": "local-config-readiness-low-cue-vue2-fixture",
  "version": "0.1.0",
  "private": true,
  "description": "Synthetic Vue 2 temporal-contract fixture"
}
```

## src/config/personnel-form.json:1-9
```
{
  "rule": [
    { "field": "parentId" },
    { "field": "parentCode" },
    { "field": "parentName" },
    { "field": "unitLookup" }
  ],
  "option": { "layout": "compact" }
}
```

## src/config/structure-form.json:1-9
```
{
  "rule": [
    { "field": "parentId" },
    { "field": "parentCode" },
    { "field": "parentName" },
    { "field": "unitLookup" }
  ],
  "option": { "layout": "wide" }
}
```

## src/editors/PersonnelEditor.vue:1-70
```
<template>
  <section>
    <schema-form ref="form" v-model="formApi" :rule="rule" :option="option" />
    <button type="button" @click="openPicker">Choose unit</button>
  </section>
</template>

<script>
import SchemaForm from "../components/SchemaForm.vue";
import { getStaticConfig } from "../services/config-service.js";

export default {
  name: "PersonnelRelationshipEditor",
  components: { SchemaForm },
  props: {
    parentNode: { type: Object, required: true },
    active: { type: Boolean, default: true },
  },
  data() {
    return {
      formApi: {},
      option: {},
      rule: [],
      pickerVisible: false,
      loadError: null,
    };
  },
  mounted() {
    if (this.active) this.getPageConfig();
  },
  watch: {
    active(next) {
      if (next) this.getPageConfig();
    },
  },
  methods: {
    getPageConfig() {
      return getStaticConfig("personnel-form")
        .then((response) => {
          if (response.ok) this.applyConfig(response.data);
        })
        .catch((error) => {
          this.loadError = error.message;
        });
    },
    applyConfig(config) {
      const rules = config.rule.map((item) => ({ ...item }));
      this.option = { ...config.option };
      rules.forEach((item) => {
        if (item.field === "unitLookup") {
          item.on = { search: () => this.openPicker() };
        }
        if (item.field === "parentCode") item.value = this.parentNode.code;
        if (item.field === "parentName") {
          item.value = this.parentNode.name;
          this.formApi.setValue({
            parentId: this.parentNode.id,
            parentCode: this.parentNode.code,
            parentName: this.parentNode.name,
          });
        }
      });
      this.rule = rules;
    },
    openPicker() {
      this.pickerVisible = true;
    },
  },
};
</script>
```

## src/editors/StructureEditor.vue:1-76
```
<template>
  <section>
    <schema-form ref="form" v-model="formApi" :rule="rule" :option="option" />
    <button type="button" @click="openPicker">Choose unit</button>
  </section>
</template>

<script>
import SchemaForm from "../components/SchemaForm.vue";
import { getStaticConfig } from "../services/config-service.js";

export default {
  name: "StructureRelationshipEditor",
  components: { SchemaForm },
  props: {
    parentNode: { type: Object, required: true },
    active: { type: Boolean, default: true },
  },
  data() {
    return {
      formApi: {},
      option: {},
      rule: [],
      pickerVisible: false,
      loadError: null,
    };
  },
  mounted() {
    if (this.active) this.getPageConfig();
  },
  watch: {
    active(next) {
      if (next) this.getPageConfig();
    },
  },
  methods: {
    getPageConfig() {
      return getStaticConfig("structure-form")
        .then((response) => {
          if (response.ok) this.applyConfig(response.data);
        })
        .catch((error) => {
          this.loadError = error.message;
        });
    },
    applyConfig(config) {
      this.option = { ...config.option };
      this.rule = this.buildRuleSet(config.rule);
      this.writeParentValues();
    },
    buildRuleSet(sourceRules) {
      const rules = sourceRules.map((item) => ({ ...item }));
      rules.forEach((item) => {
        if (item.field === "unitLookup") {
          item.on = { search: () => this.openPicker() };
        }
        if (item.field === "parentCode") item.value = this.parentNode.code;
        if (item.field === "parentName") {
          item.value = this.parentNode.name;
        }
      });
      return rules;
    },
    writeParentValues() {
      this.formApi.setValue({
        parentId: this.parentNode.id,
        parentCode: this.parentNode.code,
        parentName: this.parentNode.name,
      });
    },
    openPicker() {
      this.pickerVisible = true;
    },
  },
};
</script>
```

## src/services/config-service.js:1-5
```
export async function getStaticConfig(name) {
  const response = await fetch(`/static-config/${encodeURIComponent(name)}.json`);
  if (!response.ok) throw new Error("configuration request failed");
  return { ok: true, data: await response.json() };
}
```

