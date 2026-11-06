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
