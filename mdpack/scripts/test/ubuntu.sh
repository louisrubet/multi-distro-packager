#!/bin/bash
source /app/env.sh
apt-get update
apt-get install -y /app/${PKG_FILENAME}
