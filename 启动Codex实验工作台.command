#!/bin/zsh
cd -- "${0:A:h}" || exit 1

experiment_python='/usr/bin/python3'

"$experiment_python" -B - <<'PY'
import sys

if sys.version_info < (3, 9):
    raise SystemExit('需要 Python 3.9 或更新版本。')

import json
import time
import webbrowser
from urllib.error import HTTPError

from temporal_contract_analyzer import hub


def main():
    service = hub.ensure_server()
    with hub._opener.open(service['url'] + '/api/health', timeout=5) as response:
        health = json.load(response)
    if health.get('experiment_ui') != 'local-codex-models-v1':
        try:
            with hub._opener.open(service['url'] + '/api/experiments', timeout=5) as response:
                active = json.load(response).get('active')
        except HTTPError as error:
            if error.code != 404:
                raise
            active = None
        if active:
            raise RuntimeError('旧版服务有实验正在运行，请完成或取消后再启动新版页面。')
        print('更新旧版报告中心服务；已有报告和实验记录保留。', flush=True)
        hub.stop_server()
        deadline = time.monotonic() + 5
        while True:
            current = hub.running_server()
            if not current or current['instance'] != service['instance']:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('旧版服务尚未退出，请稍后重试。')
            time.sleep(0.05)
        service = hub.ensure_server()

    url = service['url'] + '/experiments'
    print('\nCodex 实验工作台：' + url)
    print('选择案例 → 使用本地 Codex 运行实验。')
    print('打开页面不会调用模型；点击「运行实验」才开始运行。')
    print('已运行的服务会复用，不会中断其中的实验。')
    print('服务在后台运行，关闭此终端不会停止服务。')
    print('停止服务：/usr/bin/python3 -B -m temporal_contract_analyzer reports stop\n')
    if not webbrowser.open(url):
        print('浏览器未自动打开，请复制上面的地址。')


try:
    main()
except Exception as error:
    print('启动未完成：' + str(error), file=sys.stderr)
    raise SystemExit(1)
PY

experiment_status=$?
if (( experiment_status != 0 )); then
  printf '\n请查看上面的错误提示。按回车关闭。\n'
  read -r
fi
exit "$experiment_status"
