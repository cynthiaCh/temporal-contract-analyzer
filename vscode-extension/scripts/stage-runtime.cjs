'use strict';
// Copy only this analyzer and its locked parser dependencies, never benchmark data.
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const dest = path.resolve(__dirname, '../runtime');
const parser = path.join(root, 'tools/temporal-contract-analyzer');
if (!fs.existsSync(path.join(parser, 'node_modules/@vue/compiler-sfc/package.json'))) {
  throw new Error('先运行 npm ci --prefix tools/temporal-contract-analyzer --ignore-scripts');
}
execFileSync(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['ls', '--omit=dev', '--all', '--json'], {cwd: parser, stdio: 'pipe'});
fs.rmSync(dest, {recursive: true, force: true});
fs.mkdirSync(path.join(dest, 'temporal_contract_analyzer'), {recursive: true});
for (const name of fs.readdirSync(path.join(root, 'temporal_contract_analyzer'))) {
  if (name.endsWith('.py')) fs.copyFileSync(path.join(root, 'temporal_contract_analyzer', name), path.join(dest, 'temporal_contract_analyzer', name));
}
const target = path.join(dest, 'tools/temporal-contract-analyzer');
fs.mkdirSync(target, {recursive: true});
for (const name of ['parse.cjs', 'package.json', 'package-lock.json']) fs.copyFileSync(path.join(parser, name), path.join(target, name));
fs.cpSync(path.join(parser, 'node_modules'), path.join(target, 'node_modules'), {
  recursive: true,
  filter: source => !source.split(path.sep).includes('.bin'),
});
fs.mkdirSync(path.join(root, 'dist'), {recursive: true});
console.log('Bundled analyzer + locked Babel/Vue parsers in runtime/.');
