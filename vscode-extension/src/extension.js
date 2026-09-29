'use strict';
const vscode = require('vscode');
const path = require('node:path');
const {analyze, Cancelled} = require('./runner');

const EXTENSIONS = new Set(['.vue', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.py']);
const EXCLUDED = new Set(['oracle', 'reference', 'references', 'mutants', 'negative-controls', 'results', 'studies', 'evidence', 'paper', 'node_modules', 'vendor', 'dist', 'build', '__pycache__', '.git', '.venv', 'venv']);
const SOURCE_GLOB = '**/*.{vue,js,jsx,ts,tsx,mjs,cjs,py}';

function inside(root, file) {
  const relative = path.relative(root, file);
  return relative === '' || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative));
}
function supported(uri) { return uri?.scheme === 'file' && EXTENSIONS.has(path.extname(uri.fsPath).toLowerCase()); }
function sourceName(root, file) { return path.relative(root, file).split(path.sep).join('/'); }
function range(numbers) { return new vscode.Range(numbers[0], numbers[1], numbers[2], numbers[3]); }

class FindingsTree {
  constructor() {
    this.changed = new vscode.EventEmitter();
    this.onDidChangeTreeData = this.changed.event;
    this.rows = [];
  }
  set(rows) {
    const assignParents = (items, parent) => { for (const item of items) { item.parent = parent; assignParents(item.children || [], item); } };
    assignParents(rows, undefined);
    this.rows = rows;
    this.changed.fire();
  }
  getChildren(item) { return item ? item.children || [] : this.rows; }
  getTreeItem(item) { return item; }
  getParent(item) { return item.parent; }
  dispose() { this.changed.dispose(); }
}

function notice(label, description) {
  const item = new vscode.TreeItem(label);
  item.description = description;
  item.iconPath = new vscode.ThemeIcon('info');
  return item;
}

function presentation(result, root) {
  const rows = [], diagnostics = [];
  const report = result.report;
  for (const file of report.files) {
    const uri = vscode.Uri.file(path.join(root, file.path));
    const findings = report.findings.filter(f => f.path === file.path);
    const events = new Map(file.events.map(e => [e.id, e]));
    const row = new vscode.TreeItem(file.path, vscode.TreeItemCollapsibleState.Expanded);
    row.resourceUri = uri;
    row.description = file.status === 'parsed' ? `${findings.length} 条待核查 · ${file.events.length} 个事件` : '解析不完整';
    row.tooltip = file.analysis_scope || file.path;
    row.children = [];
    const items = [];
    if (file.status !== 'parsed') {
      const adapter = report.adapters.javascript_typescript;
      const message = file.error?.message || adapter?.reason || file.status;
      const errorRange = new vscode.Range(Math.max(0, (file.error?.line || 1) - 1), 0, Math.max(0, (file.error?.line || 1) - 1), 1);
      const diagnostic = new vscode.Diagnostic(errorRange, `分析未完成：${message}`, vscode.DiagnosticSeverity.Warning);
      diagnostic.source = 'Temporal Contracts';
      diagnostic.code = 'incomplete-analysis';
      items.push(diagnostic);
      row.children.push(notice('分析未完成', message));
    }
    for (const finding of findings) {
      const evidence = finding.evidence.map(id => events.get(id)).filter(Boolean);
      if (!evidence.length) continue;
      const first = evidence[0];
      const selected = range(result.ranges[first.id]);
      const message = `待核查：${finding.message}\n条件：${finding.condition}\n核查：${finding.review_question}`;
      const diagnostic = new vscode.Diagnostic(selected, message, vscode.DiagnosticSeverity.Information);
      diagnostic.source = 'Temporal Contracts';
      diagnostic.code = finding.rule;
      diagnostic.relatedInformation = evidence.map(e => new vscode.DiagnosticRelatedInformation(
        new vscode.Location(uri, range(result.ranges[e.id])), `${e.kind} · ${e.text.slice(0, 220)}`));
      items.push(diagnostic);
      const hint = new vscode.TreeItem(finding.message, vscode.TreeItemCollapsibleState.Collapsed);
      hint.description = `L${first.line} · ${finding.rule}`;
      hint.tooltip = message;
      hint.iconPath = new vscode.ThemeIcon('comment-discussion');
      hint.command = {command: 'vscode.open', title: '定位证据', arguments: [uri, {selection: selected, preview: true}]};
      hint.children = evidence.map(e => {
        const anchor = new vscode.TreeItem(`L${e.line} · ${e.kind}`);
        anchor.description = e.text.replace(/\s+/g, ' ').slice(0, 110);
        anchor.tooltip = e.text;
        anchor.command = {command: 'vscode.open', title: '定位证据', arguments: [uri, {selection: range(result.ranges[e.id]), preview: true}]};
        return anchor;
      });
      row.children.push(hint);
    }
    if (!row.children.length) row.children.push(notice('没有规则命中', '不代表安全；可查看完整报告中的范围与限制'));
    diagnostics.push([uri, items]);
    rows.push(row);
  }
  if (report.skipped.length) rows.push(notice(`跳过 ${report.skipped.length} 个文件或目录`, '详见完整报告'));
  if (!report.files.length) rows.push(notice('目录中没有可分析的源码'));
  return {rows, diagnostics};
}

function activate(context) {
  const output = vscode.window.createOutputChannel('Temporal Contracts');
  const diagnostics = vscode.languages.createDiagnosticCollection('temporal-contracts');
  const tree = new FindingsTree();
  const view = vscode.window.createTreeView('temporalContracts.findings', {treeDataProvider: tree, showCollapseAll: true});
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 20);
  status.name = 'Temporal Contracts';
  status.command = 'temporalContracts.scanFile';
  status.text = '$(inspect) Temporal';
  status.tooltip = '扫描当前文件的时序线索';
  status.show();
  const reports = new Map();
  const reportChanged = new vscode.EventEmitter();
  const provider = {onDidChange: reportChanged.event, provideTextDocumentContent: uri => {
    const snapshot = reports.get(uri.toString());
    return snapshot ? (snapshot.stale ? '> 这是源码修改前的历史报告，定位已失效。请重新扫描。\n\n' : '') + snapshot.text : '此报告已过期，请重新扫描。';
  }};
  let active, latest, sequence = 0, timer, disposed = false;
  const config = uri => vscode.workspace.getConfiguration('temporalContracts', uri);
  const relevant = (scan, uri) => scan && uri.scheme === 'file' &&
    (scan.request.mode === 'file' ? uri.fsPath === scan.filePath : inside(scan.root, uri.fsPath));

  function cancel() {
    sequence++;
    if (active) active.controller.abort();
    active = undefined;
  }
  function clear() {
    clearTimeout(timer);
    cancel();
    latest = undefined;
    diagnostics.clear();
    tree.set([]);
    view.message = undefined;
    status.text = '$(inspect) Temporal';
    status.tooltip = '扫描当前文件的时序线索';
  }
  function invalidate(uri) {
    if (!supported(uri)) return;
    for (const [key, snapshot] of reports) {
      if (relevant(snapshot, uri) && !snapshot.stale) { snapshot.stale = true; reportChanged.fire(vscode.Uri.parse(key)); }
    }
    const affected = relevant(active, uri) || relevant(latest, uri);
    if (relevant(active, uri)) cancel();
    if (affected) {
      if (latest) latest.stale = true;
      diagnostics.clear();
      tree.set([notice('源码已修改，请重新扫描', '保存可自动扫描当前文件')]);
      view.message = '旧结果已失效，避免跳转到错误位置。';
      status.text = '$(history) Temporal';
      status.tooltip = '源码已修改；点击重新扫描当前文件';
    } else if (!active) {
      status.text = '$(inspect) Temporal';
    }
  }

  async function run(request, root, filePath, quiet) {
    if (!vscode.workspace.isTrusted) throw new Error('请先信任工作区，再运行 Temporal Contracts。');
    clearTimeout(timer);
    cancel();
    const id = sequence;
    const controller = new AbortController();
    const job = {request, root, filePath, controller};
    active = job;
    // A new scope replaces the previous scan. Never present old results as new.
    latest = undefined;
    diagnostics.clear();
    tree.set([notice('正在分析…')]);
    status.text = '$(sync~spin) Temporal';
    view.message = request.mode === 'file' ? '当前文件扫描 · 使用编辑器中的内容' : '目录扫描 · 包含已打开文件的未保存内容';
    const started = Date.now();
    try {
      const settings = config(filePath ? vscode.Uri.file(filePath) : vscode.Uri.file(root));
      const result = await analyze(context.extensionPath, request, {
        pythonPath: settings.get('pythonPath', ''),
        timeout: settings.get('timeoutSeconds', 90) * 1000,
        signal: controller.signal,
      });
      if (disposed || id !== sequence) return;
      latest = {...job, result, stale: false};
      const shown = presentation(result, root);
      diagnostics.set(shown.diagnostics);
      tree.set(shown.rows);
      const summary = result.report.summary;
      const incomplete = result.report.status !== 'parsed';
      status.text = `$(inspect) Temporal: ${summary.review_hints}${incomplete ? ' · 未完整' : ''}`;
      status.tooltip = `${summary.parsed_files}/${summary.files} 个文件解析完成，${summary.review_hints} 条待核查。点击扫描当前文件。`;
      view.message = `${request.mode === 'file' ? '当前文件' : '目录'} · ${summary.parsed_files}/${summary.files} 个文件 · ${summary.review_hints} 条待核查${incomplete ? ' · 分析未完整' : ''}。提示不是缺陷判决。`;
      output.appendLine(`${new Date().toISOString()} ${request.mode}: ${filePath || root} — ${result.report.status}, ${summary.review_hints} hints, ${Date.now() - started} ms`);
      for (const file of result.report.files.filter(f => f.status !== 'parsed')) output.appendLine(`  ${file.path}: ${file.error?.message || file.status}`);
      if (!quiet && shown.rows.length) await view.reveal(shown.rows[0], {focus: false, select: false, expand: true});
      return result;
    } catch (error) {
      if (error instanceof Cancelled || disposed || id !== sequence) return;
      diagnostics.clear();
      tree.set([notice('分析未完成', error.message)]);
      status.text = '$(warning) Temporal';
      status.tooltip = error.message;
      view.message = '分析未完成；运行日志中可查看原因。';
      output.appendLine(`ERROR: ${error.message}`);
      if (!quiet) {
        vscode.window.showErrorMessage(`Temporal Contracts：${error.message}`, '打开设置', '查看日志').then(choice => {
          if (choice === '打开设置') vscode.commands.executeCommand('workbench.action.openSettings', 'temporalContracts');
          if (choice === '查看日志') output.show(true);
        });
      }
    } finally {
      if (id === sequence) active = undefined;
    }
  }

  async function scanFile(uri, quiet = false) {
    const target = uri?.scheme ? uri : vscode.window.activeTextEditor?.document.uri;
    if (!supported(target)) {
      if (!quiet) vscode.window.showInformationMessage('请打开 Vue、JavaScript、TypeScript 或 Python 源码文件。');
      return;
    }
    const workspace = vscode.workspace.getWorkspaceFolder(target);
    const root = workspace?.uri.fsPath || path.dirname(target.fsPath);
    const relative = sourceName(root, target.fsPath);
    if (relative.split('/').some(part => EXCLUDED.has(part) || part.startsWith('.'))) {
      if (!quiet) vscode.window.showInformationMessage('此文件位于分析器排除的目录中。请扫描项目源码。');
      return;
    }
    cancel();
    const ticket = sequence;
    const document = await vscode.workspace.openTextDocument(target);
    if (ticket !== sequence || disposed) return;
    const text = document.getText();
    if (Buffer.byteLength(text, 'utf8') > 1024 * 1024) {
      if (!quiet) vscode.window.showInformationMessage('当前文件超过 1 MiB，请缩小文件后再扫描。');
      return;
    }
    return run({mode: 'file', path: relative, text}, root, target.fsPath, quiet);
  }

  async function scanFolder(uri) {
    let target = uri?.scheme === 'file' ? uri : undefined;
    if (!target) {
      const chosen = await vscode.window.showOpenDialog({canSelectFiles: false, canSelectFolders: true, canSelectMany: false,
        defaultUri: vscode.workspace.workspaceFolders?.[0]?.uri, openLabel: '扫描此目录'});
      target = chosen?.[0];
    }
    if (!target) return;
    if (target.scheme !== 'file') throw new Error('当前只支持扩展宿主文件系统中的目录。');
    const root = target.fsPath, overlays = {};
    for (const document of vscode.workspace.textDocuments) {
      if (supported(document.uri) && inside(root, document.uri.fsPath) && document.isDirty) overlays[sourceName(root, document.uri.fsPath)] = document.getText();
    }
    return run({mode: 'folder', root, overlays}, root, undefined, false);
  }

  async function showReport() {
    if (!latest) { vscode.window.showInformationMessage('请先扫描当前文件或目录。'); return; }
    const uri = vscode.Uri.parse(`temporal-contract-report:/scan-${sequence}-${Date.now()}.md`);
    const scope = latest.request.mode === 'file' ? '当前文件的编辑器快照；其他文件未纳入分析。' : '目录源码快照，包含扫描开始时已打开文件的未保存内容。';
    reports.set(uri.toString(), {text: '> ' + scope + '\n\n' + latest.result.markdown, stale: latest.stale,
      root: latest.root, filePath: latest.filePath, request: {mode: latest.request.mode}});
    while (reports.size > 10) reports.delete(reports.keys().next().value);
    const document = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(document, {preview: true, viewColumn: vscode.ViewColumn.Beside});
    return uri;
  }

  const command = (name, callback) => vscode.commands.registerCommand(name, async (...args) => {
    try { return await callback(...args); }
    catch (error) { output.appendLine(`ERROR: ${error.message}`); vscode.window.showErrorMessage(`Temporal Contracts：${error.message}`); }
  });
  const watcher = vscode.workspace.createFileSystemWatcher(SOURCE_GLOB);
  context.subscriptions.push(output, diagnostics, tree, view, status, watcher, reportChanged,
    vscode.workspace.registerTextDocumentContentProvider('temporal-contract-report', provider),
    command('temporalContracts.scanFile', uri => scanFile(uri)),
    command('temporalContracts.scanFolder', scanFolder),
    command('temporalContracts.showReport', showReport),
    command('temporalContracts.clear', clear),
    command('temporalContracts.showOutput', () => output.show(true)),
    vscode.workspace.onDidChangeTextDocument(event => { if (event.contentChanges.length) invalidate(event.document.uri); }),
    vscode.workspace.onDidCloseTextDocument(document => {
      // Closing a dirty buffer may discard edits without a text-change event.
      if (relevant(latest, document.uri) && document.isDirty) invalidate(document.uri);
    }),
    vscode.workspace.onDidSaveTextDocument(document => {
      if (!vscode.workspace.isTrusted || !supported(document.uri) || !config(document.uri).get('scanOnSave', true)) return;
      clearTimeout(timer);
      timer = setTimeout(() => { scanFile(document.uri, true).catch(error => output.appendLine(`ERROR: ${error.message}`)); }, 500);
    }),
    watcher.onDidChange(invalidate), watcher.onDidCreate(invalidate), watcher.onDidDelete(invalidate),
    vscode.workspace.onDidChangeConfiguration(event => {
      if (event.affectsConfiguration('temporalContracts')) clear();
    }),
    {dispose() { disposed = true; clearTimeout(timer); cancel(); reports.clear(); }},
  );
  // This small read-only API is also used by real extension-host tests.
  return {getLastResult: () => latest?.result, isStale: () => !!latest?.stale, getRows: () => tree.rows};
}

module.exports = {activate};
