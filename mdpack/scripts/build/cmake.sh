#!/bin/bash
source /app/env.sh
mkdir /app/build
cmake ${APP_BUILD_CMAKE_OPTIONS} -DCMAKE_INSTALL_PREFIX=/pkg -B /app/build /app/src
make -C /app/build && make -C /app/build install
