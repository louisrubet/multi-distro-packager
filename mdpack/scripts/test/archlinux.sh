#!/bin/bash
set -e
source /app/env.sh
pacman -Syu --noconfirm
pacman -U --noconfirm /app/${PKG_FILENAME}
[ -z "${TEST_COMMAND}" ] || ${TEST_COMMAND}
