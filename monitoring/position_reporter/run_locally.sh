#!/usr/bin/env bash

set -eo pipefail

if [[ -z $(command -v docker) ]]; then
  echo "docker is required but not installed.  Visit https://docs.docker.com/install/ to install."
  exit 1
fi

OS=$(uname)
if [[ "$OS" == "Darwin" ]]; then
	# OSX uses BSD readlink
	BASEDIR="$(dirname "$0")"
else
	BASEDIR=$(readlink -e "$(dirname "$0")")
fi

cd "${BASEDIR}" || exit 1

echo "run_locally.sh ${BASEDIR}"

DC_COMMAND=$*

if [[ ! "$DC_COMMAND" ]]; then
  DC_COMMAND="up"
  DC_OPTIONS="--build"
elif [[ "$DC_COMMAND" == "down" ]]; then
  DC_OPTIONS="--volumes --remove-orphans"
elif [[ "$DC_COMMAND" == "debug" ]]; then
  DC_COMMAND=up
  export DEBUG_ON=1
fi


UID_GID="$(id -u):$(id -g)"
export UID_GID
echo "DC_COMMAND is ${DC_COMMAND}"

declare log_folder="output/position_report_logs"

mkdir -p "$log_folder"

chmod -R 766 "$log_folder"

if [[ "$DC_COMMAND" == up* ]]; then
      find "$log_folder" -name "*.yaml" -exec rm {} \;
      find "$log_folder" -name "*.json" -exec rm {} \;
fi

docker compose -f docker-compose.yaml -p position_reporter "$DC_COMMAND" "$DC_OPTIONS"
