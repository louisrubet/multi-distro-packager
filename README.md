# multi-distro-packager

**This work is still in progress**.

This project aims to develop a tool for generating packages for several Linux distributions, according to the package managers of these distributions, and using an easy-to-configure manifest file.

## Principles

The manifest file allows you to configure

- the target Linux distro and its version, among the most common one: `ubuntu`, `centos`, `fedora`, `arch`, `debian` etc..
- your project sources, `git`, `archive`, or local
- the build process and tools for different languages, like `C` and `C++` with `cmake`, `autotool` for now, and later `java`, `rust`, `go`
- the dependencies packages needed by your project,
- the packages meta-data, whether their format is `deb` or `rpm`, `pacman`, `ipk` etc.

Your project is built and packaged in a docker container.

This manifest is quite inspired by the [flatpak](https://manpages.debian.org/testing/flatpak-builder/flatpak-manifest.5.en.html) and [snapcraft](https://snapcraft.io/docs/snapcraft-format) manifests.
