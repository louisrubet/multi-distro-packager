ARG VERSION
FROM archlinux:${VERSION}

RUN pacman -Syu --noconfirm --needed base-devel git && pacman -Scc --noconfirm

RUN useradd -m -u 1000 packager
USER root
