#!/bin/bash
source /app/env.sh
mkdir -p /app/rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
rpmbuild --define "_topdir /app/rpmbuild" -bb /app/rpmbuild/SPECS/pkg.spec
cp $(find /app/rpmbuild/RPMS -name "*.rpm") /app
