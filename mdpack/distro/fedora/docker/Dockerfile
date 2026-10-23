ARG VERSION
FROM fedora:${VERSION}

RUN dnf install -y @development-tools g++ cmake rpm-build

RUN useradd -m -u 1000 packager
USER root
