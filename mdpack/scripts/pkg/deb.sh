#!/bin/bash
source /app/env.sh
mkdir -p /app/pkg/DEBIAN
cd /app/pkg
echo "${PKG_CONTROL}" > DEBIAN/control
[ ! -z ${PKG_POSTINST} ] && echo ${PKG_POSTINST} > DEBIAN/postinst
dpkg-deb --root-owner-group --build /app/pkg ${PKG_NAME}.deb
