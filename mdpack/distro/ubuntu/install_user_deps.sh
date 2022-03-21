#!/bin/bash
source /app/env.sh
apt update
apt install -y ${APP_BUILD_DEPS}
