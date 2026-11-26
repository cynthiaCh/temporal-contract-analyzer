'use strict';
const vscode = require('vscode');
const path = require('node:path');
const crypto = require('node:crypto');
const fs = require('node:fs');
const {invoke} = require('./runner');

function activate(context) {
  let panel, entries = [];
  const changed = new vscode.EventEmitter();
  const config = () => vscode.workspace.getConfiguration('temporalContracts');
  const store = () => context.globalState.get('experienceStore', '') || config().get('experienceStore', '');
  const call = (operation, extra = {}) => {
    if (!store()) throw new Error('Choose your experience library first.');
    return invoke(context.extensionPath, {operation, store: store(), ...extra}, {pythonPath: config().get('pythonPath', '')});
  };
  async function reload() {
    const result = await call('experience_list');
    entries = result.entries;
    changed.fire();
    panel?.webview.postMessage({type: 'loaded', ...result, store: store()});
  }
  async function choose() {
    const selected = await vscode.window.showOpenDialog({canSelectFiles: false, canSelectFolders: true, canSelectMany: false, openLabel: 'Use experience library'});
    if (!selected) return;
    await invoke(context.extensionPath, {operation: 'experience_init', store: selected[0].fsPath}, {pythonPath: config().get('pythonPath', '')});
    await context.globalState.update('experienceStore', selected[0].fsPath);
    await reload();
  }
  const tree = {
    onDidChangeTreeData: changed.event,
    getChildren: () => entries,
    getTreeItem: entry => {
      const item = new vscode.TreeItem(entry.record.title);
      item.description = entry.category;
      item.command = {command: 'temporalContracts.openExperience', title: 'Open experience', arguments: [entry.id]};
      return item;
    },
  };
  function open(id) {
    if (panel) {
      panel.reveal();
      if (id) panel.webview.postMessage({type: 'select', id});
      return;
    }
    panel = vscode.window.createWebviewPanel('tempoevo.experiences', 'My experiences', vscode.ViewColumn.One,
      {enableScripts: true, retainContextWhenHidden: true, localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'web'))]});
    const current = panel;
    const nonce = crypto.randomBytes(18).toString('base64');
    const script = panel.webview.asWebviewUri(vscode.Uri.file(path.join(context.extensionPath, 'web/experiences.js')));
    const style = panel.webview.asWebviewUri(vscode.Uri.file(path.join(context.extensionPath, 'web/experiences.css')));
    const template = fs.readFileSync(path.join(context.extensionPath, 'web/experiences.html'), 'utf8');
    panel.webview.html = template.replace(/\{\{(cspSource|nonce|style|script)\}\}/g,
      (_, key) => ({cspSource: panel.webview.cspSource, nonce, style, script})[key]);
    current.onDidDispose(() => { if (panel === current) panel = undefined; });
    current.webview.onDidReceiveMessage(async message => {
      try {
        if (message.type === 'ready') { if (store()) { await reload(); if (id) current.webview.postMessage({type: 'select', id}); } }
        else if (message.type === 'choose') { await choose(); open(); }
        else if (message.type === 'reload') await reload();
        else if (message.type === 'history') current.webview.postMessage({type: 'history', ...await call('experience_history')});
        else if (message.type === 'change') {
          const result = await call('experience_change', {change: message.change});
          entries = result.entries; changed.fire();
          current.webview.postMessage({type: 'saved', ...result, id: message.change.id, deleted: message.change.action === 'delete'});
        }
      } catch (error) { current.webview.postMessage({type: 'error', message: error.message}); vscode.window.showErrorMessage(error.message); }
    }, undefined, context.subscriptions);
  }
  context.subscriptions.push(changed, vscode.window.registerTreeDataProvider('temporalContracts.experiences', tree),
    vscode.commands.registerCommand('temporalContracts.openExperience', open),
    vscode.commands.registerCommand('temporalContracts.chooseLibrary', async () => { try { if (panel) { panel.webview.postMessage({type: 'choose-request'}); return; } await choose(); open(); } catch (e) { vscode.window.showErrorMessage(e.message); } }),
    {dispose: () => panel?.dispose()});
  if (store()) reload().catch(e => vscode.window.showErrorMessage(e.message));
}
module.exports = {activate};
