#!/bin/bash
source /app/env.sh
dnf localinstall -y /app/${PKG_FILENAME}
