#!/usr/bin/env bash

set -eo pipefail

# Find and change to repo root directory
OS=$(uname)
if [[ "$OS" == "Darwin" ]]; then
	# OSX uses BSD readlink
	BASEDIR="$(dirname "$0")"
else
	BASEDIR=$(readlink -e "$(dirname "$0")")
fi
cd "${BASEDIR}/../.." || exit 1

(
cd monitoring || exit 1
make image
)

AUTH_SPEC="DummyOAuth(http://host.docker.internal:8085/token,uss1)"
container_name="position_reporter"

PORT=8074
#BASE_URL="http://${MOCK_USS_TOKEN_AUDIENCE:-host.docker.internal}:${PORT}"

if [ "$CI" == "true" ]; then
  docker_args="--add-host host.docker.internal:host-gateway" # Required to reach other containers in Ubuntu (used for Github Actions)
else
  docker_args="-it"
fi

docker container rm -f ${container_name} || echo "No pre-existing ${container_name} container to remove"

# shellcheck disable=SC2086
docker run ${docker_args} --name ${container_name} \
  -e POS_REP_AUTH_SPEC="${AUTH_SPEC}" \
  -p ${PORT}:5000 \
  "$@" \
  interuss/monitoring \
  position_reporter/start.sh
