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
