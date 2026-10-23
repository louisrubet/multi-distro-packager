ARG VERSION
FROM ubuntu:${VERSION}

ENV DEBIAN_FRONTEND noninteractive

COPY ["install_default_deps.sh", "/install_default_deps.sh"]
RUN /install_default_deps.sh

RUN (userdel -r ubuntu 2>/dev/null || true) && useradd -m -u 1000 packager
USER root
