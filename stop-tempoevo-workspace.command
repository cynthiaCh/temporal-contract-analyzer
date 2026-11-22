#!/bin/zsh
cd -- "${0:A:h}" || exit 1

printf '\nTempoEvo | Close workspace\n\n'
/usr/bin/python3 -B tools/experience-lab/serve.py --stop
launcher_status=$?
printf '\nPress Return to close this window.\n'
read -r
exit "$launcher_status"
