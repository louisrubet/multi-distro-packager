#!/bin/bash
set -e
source /app/env.sh
apt-get update
apt-get install -y /app/${PKG_FILENAME}
[ -z "${TEST_COMMAND}" ] || ${TEST_COMMAND}
