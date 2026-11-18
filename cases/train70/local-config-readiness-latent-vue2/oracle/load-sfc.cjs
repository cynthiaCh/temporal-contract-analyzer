"use strict";

const fs = require("fs");
const Module = require("module");
const path = require("path");

const runtimeRoot = path.resolve(__dirname, "../../../../../runtimes/vue2");
const esbuild = require(path.join(runtimeRoot, "node_modules/esbuild"));
const {
  compileTemplate,
  parse,
  rewriteDefault,
} = require(path.join(runtimeRoot, "node_modules/vue/compiler-sfc"));

function sfcPlugin() {
  return {
    name: "vue2-official-sfc-compiler",
    setup(build) {
      build.onLoad({ filter: /\.vue$/ }, async (args) => {
        const source = await fs.promises.readFile(args.path, "utf8");
        const descriptor = parse({ source, filename: args.path });
        if (descriptor.errors.length) {
          throw new Error(`cannot parse ${args.path}: ${descriptor.errors.join("; ")}`);
        }
        if (!descriptor.template || !descriptor.script || descriptor.scriptSetup) {
          throw new Error(`${args.path} must contain one template and one ordinary script`);
        }
        const template = compileTemplate({
          source: descriptor.template.content,
          filename: args.path,
          id: `ftcb-${path.basename(args.path)}`,
        });
        if (template.errors.length) {
          throw new Error(`cannot compile ${args.path}: ${template.errors.join("; ")}`);
        }
        const script = rewriteDefault(descriptor.script.content, "__script");
        return {
          contents: [
            script,
            template.code,
            "__script.render = render;",
            "__script.staticRenderFns = staticRenderFns;",
            "export default __script;",
          ].join("\n"),
          loader: "js",
          resolveDir: path.dirname(args.path),
        };
      });
    },
  };
}

async function loadSfc(candidateRoot, relativeEntry) {
  const entry = path.resolve(candidateRoot, relativeEntry);
  const relative = path.relative(candidateRoot, entry);
  if (relative.startsWith("..") || path.isAbsolute(relative) || !entry.endsWith(".vue")) {
    throw new Error("SFC entry escapes the candidate repository");
  }
  const result = await esbuild.build({
    absWorkingDir: candidateRoot,
    bundle: true,
    entryPoints: [entry],
    external: ["vue"],
    format: "cjs",
    logLevel: "silent",
    platform: "node",
    plugins: [sfcPlugin()],
    target: "node16",
    write: false,
  });
  if (result.outputFiles.length !== 1) throw new Error("SFC compilation returned an invalid bundle");
  const compiled = new Module(entry, module);
  compiled.filename = entry;
  compiled.paths = [
    path.join(runtimeRoot, "node_modules"),
    ...Module._nodeModulePaths(candidateRoot),
  ];
  compiled._compile(result.outputFiles[0].text, entry);
  return compiled.exports.default || compiled.exports;
}

module.exports = { loadSfc };
