#!/bin/bash
chmod +x /app/*.sh
[ -f /app/install_user_deps.sh ] && /app/install_user_deps.sh
su -c /app/build.sh packager
[ -f /app/postinstall.sh ] && su -c /app/postinstall.sh packager
su -c /app/pkg.sh packager
