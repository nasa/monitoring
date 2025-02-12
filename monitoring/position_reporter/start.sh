#!/usr/bin/env bash

# This script is intended to be called from within a Docker container running
# position_reporter via the interuss/monitoring image.

# Ensure position_reporter is the working directory
OS=$(uname)
if [[ $OS == "Darwin" ]]; then
	# OSX uses BSD readlink
	BASEDIR="$(dirname "$0")"
else
	BASEDIR=$(readlink -e "$(dirname "$0")")
fi
cd "${BASEDIR}" || exit 1
echo "start.sh ${BASEDIR}"

chmod -R 766 ./output/position_report_logs

ls -l output/

# health check
cp health_check.sh /app

# Start
port=${POS_REP_PORT:-5000}
export PYTHONUNBUFFERED=TRUE
gunicorn \
    --preload \
    --config ./gunicorn.conf.py \
    --workers=4 \
    --worker-tmp-dir="/dev/shm" \
    "--bind=0.0.0.0:${port}" \
    monitoring.position_reporter:webapp
