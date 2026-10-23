#!/bin/bash
# Packages /app/install with makepkg, from the PKGBUILD written by mdpack.
set -e
source /app/env.sh
cd /app/pacman
makepkg --force --nodeps
cp /app/pacman/${PKG_FILENAME} /app/${PKG_FILENAME}
