ARG VERSION
FROM ubuntu:${VERSION}

COPY ["install_default_deps.sh", "/install_default_deps.sh"]
RUN /install_default_deps.sh

RUN useradd -m packager
USER root
