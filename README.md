# multi-distro-packager

**This work is still in progress**.

Although flatpak and snap are probably the future of linux packages, sometime you still have to deliver `deb` or `rpm` packages for some reason.

This project aims to develop a tool for generating such packages for several Linux distributions, according to the package managers of these distributions, and using a single easy-to-configure manifest file.

## Principles

The manifest file allows you to configure

- the target Linux distro and its version, among the most common one: `ubuntu`, `fedora`, `mint`, `opensuse`, `arch`, `debian`, `centos`, `manjaro` etc..
- your project sources location, `git`, `archive`, or local
- the generation process and tools for different languages, like `C` and `C++` with `cmake`, `autotool` for now, and later `python`,  `java`, `rust`, `go`
- the dependencies packages needed by your project,
- the packages meta-data, whether their format is `deb`, `rpm`, `pacman`, `ipk` etc.

Your project is built and packaged in a docker container.

This manifest is quite inspired by the [flatpak](https://manpages.debian.org/testing/flatpak-builder/flatpak-manifest.5.en.html) and [snapcraft](https://snapcraft.io/docs/snapcraft-format) manifests.
