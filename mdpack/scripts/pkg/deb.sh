#!/bin/bash
source /app/env.sh
# [ ! -z ${PKG_POSTINST} ] && echo ${PKG_POSTINST} > /app/install/DEBIAN/postinst
dpkg-deb --root-owner-group --build /app/install /app/${PKG_FILENAME}
