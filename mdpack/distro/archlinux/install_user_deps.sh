#!/bin/bash
source /app/env.sh
pacman -Syu --noconfirm --needed ${APP_BUILD_DEPS}
