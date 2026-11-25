'use strict';
// Bundle the Python library adapter; the experience editor does not need JS parsers.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const dest = path.resolve(__dirname, '../runtime');
fs.rmSync(dest, {recursive: true, force: true});
fs.mkdirSync(path.join(dest, 'temporal_contract_analyzer'), {recursive: true});
for (const name of fs.readdirSync(path.join(root, 'temporal_contract_analyzer'))) {
  if (name.endsWith('.py')) fs.copyFileSync(path.join(root, 'temporal_contract_analyzer', name), path.join(dest, 'temporal_contract_analyzer', name));
}
fs.cpSync(path.join(root, 'temporal_contract_analyzer/web'), path.join(dest, 'temporal_contract_analyzer/web'), {recursive: true});
for (const name of ['contract-taxonomy.json', 'contract-reminders.json']) {
  fs.copyFileSync(path.join(root, 'temporal_contract_analyzer', name), path.join(dest, 'temporal_contract_analyzer', name));
}
for (const name of ['prompts', '_session_runtime']) {
  fs.cpSync(path.join(root, 'temporal_contract_analyzer', name), path.join(dest, 'temporal_contract_analyzer', name), {
    recursive: true,
    filter: source => !source.split(path.sep).includes('__pycache__') && !source.endsWith('.pyc'),
  });
}
fs.mkdirSync(path.join(root, 'dist'), {recursive: true});
console.log('Bundled Python experience library in runtime/.');
