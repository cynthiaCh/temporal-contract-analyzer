#!/bin/zsh
cd -- "${0:A:h}" || exit 1

workbench_python='/usr/bin/python3'

function workbench_failed() {
  printf '\n启动未完成，请查看上面的提示。按回车关闭。\n'
  read -r
  exit 1
}

"$workbench_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else "需要 Python 3.9 或更新版本。")' || workbench_failed

printf '\n打开边界审查工作台：扫描 → 四问卡片 → 人工核查。\n'
printf '完整 E/T/L/H 位于「高级测量」，可按需展开。\n'
printf '使用 CLI、VS Code 与 Codex 共用的已配置报告库。\n'
printf '重新启动报告库服务以加载当前源码；已有报告和核查记录保留。\n'
printf '请保留此终端窗口；关闭窗口或按 Ctrl+C 会停止服务。\n\n'

"$workbench_python" -B -m temporal_contract_analyzer reports stop >/dev/null || workbench_failed

# Replace the launcher with its foreground service so terminal signals reach it.
exec "$workbench_python" -B - <<'PY'
import os
import signal
import threading
import time
import webbrowser

from temporal_contract_analyzer import archive, hub


def stop_on_signal(signum, frame):
    # Unwind hub.serve's finally block, closing the socket and removing server.json.
    raise SystemExit(0)


for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
    signal.signal(signum, stop_on_signal)

store = archive.store_path()


def open_when_ready():
    for _ in range(100):
        current = hub.running_server(store)
        if current and current['pid'] == os.getpid():
            webbrowser.open(current['url'])
            return
        time.sleep(0.1)


threading.Thread(target=open_when_ready, daemon=True).start()
hub.serve(store)
PY
