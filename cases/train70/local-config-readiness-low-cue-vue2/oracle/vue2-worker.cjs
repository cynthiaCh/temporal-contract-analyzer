"use strict";

const fs = require("fs");
const path = require("path");
const { JSDOM } = require(path.resolve(__dirname, "../../../../../runtimes/vue2/node_modules/jsdom"));
const { loadSfc } = require("./load-sfc.cjs");

const candidateRoot = path.resolve(process.argv[2] || "");
const editorName = process.argv[3];
const schedule = process.argv[4];

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

async function tick(Vue) {
  await Vue.nextTick();
  await Promise.resolve();
}

async function delay(milliseconds) {
  await new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function main() {
  if (!fs.statSync(candidateRoot).isDirectory()) throw new Error("candidate root is missing");
  if (!["personnel", "structure"].includes(editorName)) throw new Error("unknown editor");
  if (!["fresh-open", "reused-open"].includes(schedule)) throw new Error("unknown schedule");

  const dom = new JSDOM("<!doctype html><html><body><div id=app></div></body></html>");
  global.window = dom.window;
  global.document = dom.window.document;
  global.navigator = dom.window.navigator;
  dom.window.__FORM_API_DELAY_MS__ = schedule === "fresh-open" ? 25 : 5;

  const Vue = require(path.resolve(__dirname, "../../../../../runtimes/vue2/node_modules/vue"));
  Vue.config.productionTip = false;
  Vue.config.devtools = false;
  const errors = [];
  Vue.config.errorHandler = (error) => errors.push(error.message);

  const remoteRequests = [];
  global.fetch = async (request) => {
    remoteRequests.push(String(request));
    const match = String(request).match(/\/static-config\/([a-z-]+)\.json$/);
    if (!match) return { ok: false, json: async () => null };
    await delay(45);
    const configPath = path.join(candidateRoot, "src/config", `${editorName}-form.json`);
    return {
      ok: true,
      json: async () => clone(JSON.parse(fs.readFileSync(configPath, "utf8"))),
    };
  };

  const componentPath = path.join(
    candidateRoot,
    "src/editors",
    editorName === "personnel" ? "PersonnelEditor.vue" : "StructureEditor.vue"
  );
  const Editor = await loadSfc(candidateRoot, path.relative(candidateRoot, componentPath));
  const parent = {
    id: `${editorName}-parent-7f3a`,
    code: `${editorName}-code-29c1`,
    name: `${editorName}-name-84d6`,
  };
  const root = new Vue({
    data: () => ({ active: schedule === "fresh-open" }),
    render(h) {
      return h(Editor, {
        ref: "editor",
        props: { active: this.active, parentNode: parent },
      });
    },
  }).$mount("#app");

  await tick(Vue);
  if (schedule === "reused-open") {
    await delay(20);
    await tick(Vue);
    root.active = true;
    await tick(Vue);
  }
  await delay(70);
  await tick(Vue);

  const editor = root.$refs.editor;
  if (editor) editor.openPicker();
  await tick(Vue);
  const form = editor && editor.$refs.form;
  const snapshot = {
    error: errors[0] || (editor && editor.loadError) || null,
    formApiReady: Boolean(editor && editor.formApi),
    rules: editor && Array.isArray(editor.rule)
      ? editor.rule.map((item) => item.field)
      : [],
    values: form ? { ...form.values } : {},
    imperativeWriteCount: form ? form.imperativeWriteCount : 0,
    ruleHydrationCount: form ? form.ruleHydrationCount : 0,
    pickerVisible: Boolean(editor && editor.pickerVisible),
    remoteRequests,
  };
  root.$destroy();
  delete global.fetch;
  process.stdout.write(JSON.stringify(snapshot));
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 2;
});
