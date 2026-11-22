#!/bin/zsh
cd -- "${0:A:h}" || exit 1

printf '\nTempoEvo | Training and Testing Workspace\n\n'
printf 'An existing workspace will reopen automatically.\n'
printf 'To close the service, double-click stop-tempoevo-workspace.command.\n'
printf 'If a new server starts, keep this terminal open while it is in use.\n'
printf 'Prepare makes no model requests. Start training/testing invokes the model.\n'
printf 'Keep the service running until your execution has finished.\n\n'

/usr/bin/python3 -B tools/experience-lab/serve.py --open
launcher_status=$?
if (( launcher_status != 0 )); then
  printf '\nThe workspace could not start. Check the message above.\n'
  printf 'Press Return to close.\n'
  read -r
fi
exit "$launcher_status"
