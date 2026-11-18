"use strict";

const path = require("path");
const { pathToFileURL } = require("url");

const candidateRoot = path.resolve(process.argv[2] || "");
const bootstrapMode = process.argv[3];

if (!["synchronous", "deferred"].includes(bootstrapMode)) {
  throw new Error("unknown bootstrap mode");
}

async function main() {
  const entry = pathToFileURL(path.join(candidateRoot, "src/render-workspace.js")).href;
  const workspace = await import(entry);
  const snapshot = await workspace.render({ token: "public-listener", bootstrapMode });
  process.stdout.write(JSON.stringify({ bootstrapMode, snapshot }));
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 2;
});
