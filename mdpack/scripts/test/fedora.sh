#!/bin/bash
set -e
source /app/env.sh
dnf install -y /app/${PKG_FILENAME}
[ -z "${TEST_COMMAND}" ] || ${TEST_COMMAND}
