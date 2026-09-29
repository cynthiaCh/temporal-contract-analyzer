'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {runTests} = require('@vscode/test-electron');

async function main() {
  // Some editor terminals export this; the test host must start as Electron.
  delete process.env.ELECTRON_RUN_AS_NODE;
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'tca-vscode-host-'));
  const workspace = path.join(temporary, 'workspace');
  fs.mkdirSync(workspace);
  fs.writeFileSync(path.join(workspace, 'Demo.vue'), '<template><div>Demo</div></template>\n<script setup>const value = 1;</script>\n');
  fs.writeFileSync(path.join(workspace, 'Broken.vue'), '<script src="./external.js"></script>');
  fs.mkdirSync(path.join(workspace, '.vscode'));
  fs.writeFileSync(path.join(workspace, '.vscode/settings.json'), JSON.stringify({'temporalContracts.scanOnSave': false}));
  const installed = '/Applications/Visual Studio Code.app/Contents/MacOS/Code';
  const executable = process.env.VSCODE_EXECUTABLE_PATH || (fs.existsSync(installed) ? installed : undefined);
  try {
    await runTests({
      vscodeExecutablePath: executable,
      extensionDevelopmentPath: process.env.TCA_EXTENSION_PATH || path.resolve(__dirname, '..'),
      extensionTestsPath: path.join(__dirname, 'host-suite.cjs'),
      launchArgs: [workspace, '--user-data-dir=' + path.join(temporary, 'user'),
        '--extensions-dir=' + path.join(temporary, 'extensions'), '--disable-extensions',
        '--disable-workspace-trust', '--skip-welcome', '--skip-release-notes', '--disable-updates'],
    });
  } finally {
    fs.rmSync(temporary, {recursive: true, force: true});
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
