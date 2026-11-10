#!/bin/zsh
cd -- "${0:A:h}" || exit 1

launcher_python='/usr/bin/python3'

function launch_failed() {
  printf '\nAST review could not start. Check the message above. Press Return to close.\n'
  read -r
  exit 1
}

"$launcher_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else "Python 3.9 or newer is required.")' || launch_failed

printf '\nTempoEvo | AST Evidence Review\n\n'
printf 'Scan candidate source, inspect boundary cards and source context, then record review judgments.\n'
printf 'Review each hint against the task and source; a syntax pattern alone does not establish a defect.\n'
printf 'Report annotations, analysis review and experience activation are separate records.\n\n'
printf 'Next steps in the unified experience workflow:\n'
printf '  Analysis: review the automatic Contract, obligation labels and mechanism premises.\n'
printf '  Experience: review rules and evidence before activating an exact version.\n'
printf '    python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory\n'
printf '  Evolution: use experience-evolution for bounded development or frozen evaluation.\n'
printf '    See docs/EXPERIENCE_EVOLUTION.md for configuration and execution.\n\n'
printf 'Using the report store shared by the CLI, VS Code and Codex MCP.\n'
printf 'Restarting the report service to load the current code; saved reports and annotations are retained.\n'
printf 'Keep this terminal open. Press Ctrl+C or close the terminal to stop this service.\n\n'

"$launcher_python" -B -m temporal_contract_analyzer reports stop >/dev/null || launch_failed

# Replace the launcher with its foreground service so terminal signals reach it.
exec "$launcher_python" -B - <<'PY'
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
