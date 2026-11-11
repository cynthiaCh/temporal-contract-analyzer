#!/bin/zsh
cd -- "${0:A:h}" || exit 1

launcher_python='/usr/bin/python3'

function launch_failed() {
  printf '\nExperience review could not start. Check the message above. Press Return to close.\n'
  read -r
  exit 1
}

"$launcher_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else "Python 3.9 or newer is required.")' || launch_failed

if [[ ! -f experience-memory/memory.json ]]; then
  printf '\nNo experience library was found in this repository.\n'
  printf 'Initialize or restore experience-memory/ before opening the review page.\n'
  launch_failed
fi

printf '\nTempoEvo | Experience Review\n\n'
printf "Opening this repository's experience library in your browser.\n"
printf 'The review queue shows pending and reviewed versions with counts and filters.\n'
printf 'Review rules and retained evidence, then record your decision.\n'
printf 'Content acceptance and activation are separate; activation also requires effect qualification.\n'
printf 'Keep this terminal open. Press Ctrl+C or close the terminal to stop this service.\n\n'

exec "$launcher_python" -B -m temporal_contract_analyzer experience-memory review --store experience-memory
