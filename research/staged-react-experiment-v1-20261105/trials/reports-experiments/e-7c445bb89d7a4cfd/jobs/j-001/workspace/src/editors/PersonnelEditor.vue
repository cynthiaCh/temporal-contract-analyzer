<template>
  <section>
    <schema-form ref="form" v-model="formApi" :rule="rule" :option="option" />
    <button type="button" @click="openPicker">Choose unit</button>
  </section>
</template>

<script>
import SchemaForm from "../components/SchemaForm.vue";
import personnelConfig from "../config/personnel-form.json";

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
      return new Promise((resolve) => {
        if (typeof this.formApi.setValue === "function") {
          resolve();
          return;
        }
        const unwatch = this.$watch("formApi", (api) => {
          if (typeof api.setValue === "function") {
            unwatch();
            resolve();
          }
        });
      })
        .then(() => {
          this.applyConfig(personnelConfig);
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
