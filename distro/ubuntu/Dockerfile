ARG DISTRO
ARG VERSION
FROM ${DISTRO}:${VERSION}

COPY ["default_deps.sh", "/default_deps.sh"]
RUN /default_deps.sh

RUN useradd -m packager
USER root
