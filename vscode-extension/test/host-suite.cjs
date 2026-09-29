'use strict';
const assert = require('node:assert/strict');
const vscode = require('vscode');
const fs = require('node:fs/promises');
const path = require('node:path');

async function waitFor(predicate, message) {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    if (await predicate()) return;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('Timeout: ' + message);
}
function hints(uri) { return vscode.languages.getDiagnostics(uri).filter(d => d.source === 'Temporal Contracts'); }
async function replace(document, text) {
  const edit = new vscode.WorkspaceEdit();
  edit.replace(document.uri, new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length)), text);
  assert(await vscode.workspace.applyEdit(edit));
}

exports.run = async () => {
  const extension = vscode.extensions.getExtension('temporal-contract-tools.temporal-contract-analyzer');
  assert(extension, 'Extension manifest is discoverable');
  const api = await extension.activate();
  const root = vscode.workspace.workspaceFolders[0].uri;
  const uri = vscode.Uri.joinPath(root, 'Demo.vue');
  const document = await vscode.workspace.openTextDocument(uri);
  await vscode.window.showTextDocument(document);
  const original = await fs.readFile(uri.fsPath, 'utf8');
  const source = '<template><div>😀</div></template>\n<script setup>async function load() { await fetch(); store.save(); }</script>\n';

  await replace(document, source);
  const first = await vscode.commands.executeCommand('temporalContracts.scanFile');
  assert.equal(first.report.status, 'parsed');
  assert(first.archive?.report_id, 'The plugin persists a shared report ID');
  const archived = JSON.parse(await fs.readFile(path.join(first.archive.archive_path, 'snapshot.json'), 'utf8'));
  assert.equal(archived.sources['Demo.vue'], source, 'The archive preserves the exact dirty buffer');
  assert.equal(first.archive.origin, 'vscode');
  assert.equal(await fs.readFile(uri.fsPath, 'utf8'), original, 'Unsaved buffer is not written');
  const hint = hints(uri).find(d => d.code === 'effect-after-await');
  assert(hint, 'Real Problems diagnostics include temporal hints');
  assert.equal(hint.severity, vscode.DiagnosticSeverity.Information);
  assert.equal(document.getText(hint.range), 'await fetch()');
  assert.equal(hint.relatedInformation.length, 2);
  console.log('PASS: unsaved Vue scan, real diagnostics, exact positions');
  const previousClipboard = await vscode.env.clipboard.readText();
  try {
    assert.equal(await vscode.commands.executeCommand('temporalContracts.copyReportId'), first.archive.report_id);
    assert.equal(await vscode.env.clipboard.readText(), first.archive.report_id);
  } finally { await vscode.env.clipboard.writeText(previousClipboard); }
  console.log('PASS: shared archive preserves editor snapshots and exposes report IDs');

  const row = api.getRows().find(item => item.resourceUri?.toString() === uri.toString());
  const evidence = row.children[0].children[1];
  await vscode.commands.executeCommand(evidence.command.command, ...evidence.command.arguments);
  assert.equal(vscode.window.activeTextEditor.document.getText(vscode.window.activeTextEditor.selection), 'store.save()');
  console.log('PASS: tree evidence navigation selects the exact expression');

  const reportUri = await vscode.commands.executeCommand('temporalContracts.showReport');
  const reportDocument = await vscode.workspace.openTextDocument(reportUri);
  assert.match(reportDocument.getText(), /effect-after-await/);
  await replace(document, '<script setup>const value = 2;</script>');
  await waitFor(() => !hints(uri).length && api.isStale(), 'Edit removes old diagnostics');
  await waitFor(() => reportDocument.getText().includes('历史报告'), 'Open report is marked stale');
  console.log('PASS: changes invalidate diagnostics and visible report snapshots');

  await vscode.window.showTextDocument(document);
  await replace(document, source);
  const directory = await vscode.commands.executeCommand('temporalContracts.scanFolder', root);
  assert.equal(directory.report.status, 'partial');
  assert(directory.report.findings.some(f => f.path === 'Demo.vue' && f.rule === 'effect-after-await'));
  const broken = vscode.Uri.joinPath(root, 'Broken.vue');
  assert(hints(broken).some(d => d.code === 'incomplete-analysis' && d.severity === vscode.DiagnosticSeverity.Warning));
  assert.equal(await fs.readFile(uri.fsPath, 'utf8'), original);
  console.log('PASS: directory overlays, partial status and parser failure diagnostics');

  await fs.writeFile(broken.fsPath, '<script setup>externalChange();</script>');
  await waitFor(() => api.isStale() && !hints(uri).length, 'External file change invalidates a folder scan');
  console.log('PASS: external filesystem changes invalidate directory results');

  // Starting a newer scan prevents a slower/older request from publishing.
  // Use an unchanged target: delayed filesystem events from the previous test
  // legitimately cancel scans of Broken.vue and are unrelated to supersession.
  const stable = vscode.Uri.joinPath(root, 'Stable.vue');
  const old = vscode.commands.executeCommand('temporalContracts.scanFile', uri);
  const recent = vscode.commands.executeCommand('temporalContracts.scanFile', stable);
  await Promise.all([old, recent]);
  assert.equal(api.getLastResult().report.files[0].path, 'Stable.vue');
  assert.equal(hints(uri).length, 0);
  console.log('PASS: superseded scans cannot overwrite newer results');

  await vscode.commands.executeCommand('temporalContracts.clear');
  await document.save();
  await new Promise(resolve => setTimeout(resolve, 800));
  assert.equal(api.getLastResult(), undefined, 'scanOnSave=false remains manual');
  console.log('PASS: automatic scanning can be disabled');

  await vscode.workspace.getConfiguration('temporalContracts').update('scanOnSave', true, vscode.ConfigurationTarget.Workspace);
  await vscode.window.showTextDocument(document);
  await replace(document, source + '\n');
  await document.save();
  await waitFor(() => hints(uri).some(d => d.code === 'effect-after-await'), 'Scan on save');
  console.log('PASS: saving runs the bundled parser in the VS Code extension host');

  const json = vscode.Uri.joinPath(root, 'plain.json');
  await fs.writeFile(json.fsPath, '{}');
  await vscode.commands.executeCommand('temporalContracts.clear');
  assert.equal(hints(uri).length, 0);
  assert.equal(hints(broken).length, 0);
  assert.equal(api.getLastResult(), undefined);
  console.log('PASS: clear removes all diagnostics and scan state');
  await vscode.commands.executeCommand('workbench.action.closeAllEditors');
};
