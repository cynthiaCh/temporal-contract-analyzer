<template>
  <section>
    <schema-form ref="form" v-model="formApi" :rule="rule" :option="option" />
    <button type="button" @click="openPicker">Choose unit</button>
  </section>
</template>

<script>
import SchemaForm from "../components/SchemaForm.vue";
import localConfig from "../config/structure-form.json";

export default {
  name: "StructureRelationshipEditor",
  components: { SchemaForm },
  props: {
    parentNode: { type: Object, required: true },
    active: { type: Boolean, default: true },
  },
  data() {
    return { formApi: {}, option: {}, rule: [], pickerVisible: false, loadError: null };
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
      this.applyConfig(JSON.parse(JSON.stringify(localConfig)));
    },
    applyConfig(config) {
      const rules = config.rule.map((item) => ({ ...item }));
      this.option = { ...config.option };
      rules.forEach((item) => {
        if (item.field === "unitLookup") item.on = { search: () => this.openPicker() };
        if (item.field === "parentId") item.value = this.parentNode.id;
        if (item.field === "parentCode") item.value = this.parentNode.code;
        if (item.field === "parentName") item.value = this.parentNode.name;
      });
      this.rule = rules;
    },
    openPicker() {
      this.pickerVisible = true;
    },
  },
};
</script>
