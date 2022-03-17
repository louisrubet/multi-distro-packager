ARG VERSION
FROM fedora:${VERSION}

RUN dnf install -y @development-tools g++ cmake rpm-build

RUN useradd -m packager
USER root
