'use strict';
const {spawn} = require('node:child_process');
const path = require('node:path');

class Cancelled extends Error {
  constructor() { super('Analysis cancelled'); this.name = 'Cancelled'; }
}

function stop(child) {
  if (!child.pid) return;
  if (process.platform === 'win32') {
    const killer = spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], {windowsHide: true, stdio: 'ignore'});
    killer.on('error', () => child.kill());
  } else {
    try { process.kill(-child.pid, 'SIGKILL'); } catch { child.kill(); }
  }
}

function execute(executable, args, {input = '', cwd, timeout = 90000, signal} = {}) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(new Cancelled()); return; }
    // Keep candidate paths off Python/Node module search paths. Electron's
    // executable supplies Node even when the user has no node on PATH.
    const env = {...process.env, ELECTRON_RUN_AS_NODE: '1', PYTHONIOENCODING: 'utf-8'};
    delete env.NODE_OPTIONS;
    delete env.NODE_PATH;
    delete env.PYTHONPATH;
    delete env.PYTHONHOME;
    const child = spawn(executable, args, {cwd, env, shell: false, windowsHide: true, detached: process.platform !== 'win32'});
    let settled = false, bytes = 0, stdout = [], stderr = '';
    const done = (error, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      signal?.removeEventListener('abort', abort);
      error ? reject(error) : resolve(value);
    };
    const abort = () => { stop(child); done(new Cancelled()); };
    const timer = setTimeout(() => { stop(child); done(new Error('分析超时；可缩小扫描目录或提高 timeoutSeconds。')); }, timeout);
    signal?.addEventListener('abort', abort, {once: true});
    child.on('error', error => done(error));
    child.stdout.on('data', data => {
      bytes += data.length;
      if (bytes > 96 * 1024 * 1024) { stop(child); done(new Error('报告超过 96 MiB，请缩小扫描范围。')); }
      else stdout.push(data);
    });
    child.stderr.on('data', data => { stderr = (stderr + data.toString('utf8')).slice(-8000); });
    child.stdin.on('error', error => { if (error.code !== 'EPIPE') done(error); });
    child.on('close', code => {
      if (code !== 0) done(new Error(stderr.trim() || `分析进程退出：${code}`));
      else done(null, Buffer.concat(stdout).toString('utf8'));
    });
    child.stdin.end(input, 'utf8');
  });
}

async function findPython(configured, options = {}) {
  const probe = ['-I', '-S', '-B', '-c', 'import sys; print(sys.executable); sys.exit(0 if sys.version_info >= (3,9) else 3)'];
  const candidates = configured ? [[configured, []]] : process.platform === 'win32'
    ? [['py', ['-3']], ['python', []], ['python3', []]]
    : [['python3', []], ['/usr/bin/python3', []], ['/opt/homebrew/bin/python3', []], ['/usr/local/bin/python3', []]];
  for (const [executable, prefix] of candidates) {
    try {
      await execute(executable, [...prefix, ...probe], {...options, timeout: 5000});
      return {executable, prefix};
    } catch (error) {
      if (error instanceof Cancelled) throw error;
    }
  }
  throw new Error('找不到 Python 3.9+。请在设置 Temporal Contracts: Python Path 中填写 Python 可执行文件路径。');
}

async function invoke(extensionPath, request, {pythonPath = '', timeout, signal, node = process.execPath} = {}) {
  const python = await findPython(pythonPath, {cwd: extensionPath, signal});
  const result = await execute(python.executable,
    [...python.prefix, '-I', '-S', '-B', '-X', 'utf8', path.join(extensionPath, 'python/bridge.py')],
    {cwd: extensionPath, signal, timeout, input: JSON.stringify({...request, node})});
  let parsed;
  try { parsed = JSON.parse(result); } catch { throw new Error('分析器未返回有效 JSON；请查看 Temporal Contracts 日志。'); }
  return parsed;
}

async function analyze(extensionPath, request, options = {}) {
  const parsed = await invoke(extensionPath, request, options);
  if (parsed.archive?.status === 'failed') {
    const error = new Error(`分析失败（已归档 ${parsed.archive.report_id}）：${parsed.archive.error}`);
    error.archive = parsed.archive;
    throw error;
  }
  if (parsed.report?.schema_version !== 'temporal-contract-analysis-1' || !parsed.ranges || typeof parsed.markdown !== 'string') {
    throw new Error('分析器返回了不兼容的报告。');
  }
  return parsed;
}

module.exports = {analyze, invoke, execute, findPython, Cancelled};
