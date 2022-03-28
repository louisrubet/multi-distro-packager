# multi-distro-packager

**This work is still in progress** but with a heavy commitment.

## Purpose

Although [flatpak](https://flatpak.org/) and [snap](https://snapcraft.io/) are probably the future of linux packages, sometime you still have to deliver `deb` or `rpm` packages for some reason.

This project aims to develop a tool for generating such packages for several Linux distributions, according to the package managers of these distributions, and using a single easy-to-configure manifest file.

This manifest allows you to configure:

- the target Linux distros and their versions, among `ubuntu`, `fedora` ...
- your project sources location as a `git` repo, an `archive`, or a local directory,
- the generation process and tools for different languages, like `cmake` and `autotool` for now, and more later,
- the dependencies packages needed by your project,
- the packages meta-data, whether their format is `deb`, `rpm` or other.

Refer to the 'Manifest manual' paragraph below.

This manifest is quite inspired by the [flatpak](https://manpages.debian.org/testing/flatpak-builder/flatpak-manifest.5.en.html) and [snapcraft](https://snapcraft.io/docs/snapcraft-format) manifests.

Please look at [the given manifest](https://github.com/louisrubet/multi-distro-packager/blob/main/manifest.yaml) or [the examples](https://github.com/louisrubet/multi-distro-packager/tree/main/examples) to make up your mind.

## Principles

Your app is built and packaged in the docker containers matching to the distros you declared.

For a given distro and version the whole process looks like:

- fetching the docker image and installing the standard dev packages,
- creating a docker container and installing the complementary user development packages,
- building, installing and packaging the user app,
- testing the app installation.

The docker containers are run as root in order to install the complementary development dependencies.

The user application is built and installed as the user `packager` (uid=1000, gid=1000).

For the final test the generated package is installed in a new container using the package manager of the distro, which installs the needed runtime dependencies.

## Installation from this repository

- You must install `docker` and be able to run `docker run hello-world` without being root on your host.

- `mdpack.py` needs `python` >= 3.6 and the pip modules `Cerberus` and `Pyyaml`. You can install them by running

```shell
pip install -r requirements.txt
```

## Running mdpack

Example:

```shell
./mdpack.py manifest.yaml
Processing ubuntu-20.04
- building docker image ubuntu-20.04
- building rpn-2.4.2-0.amd64.deb
- testing ubuntu-20.04-rpn-2.4.2-0.amd64.deb
Processing ubuntu-22.04
- building docker image ubuntu-22.04
- building rpn-2.4.2-0.amd64.deb
- testing ubuntu-22.04-rpn-2.4.2-0.amd64.deb
Processing fedora-35
- building docker image fedora-35
- building rpn-2.4.2-0.x86_64.rpm
- testing fedora-35-rpn-2.4.2-0.x86_64.rpm
```

The generated package are delivered in the current directory.

## Manifest manual

The manifest is a yaml file containing the distros, app and packages description.

Please refer to https://yaml.org/ for the complete yaml syntax.

### example

Here is a complete example of a manifest file, for delivering the package `rpn`.

```yaml
distro: [ubuntu:20.04, ubuntu:22.04, fedora:35]

app:
  source:
    type: git
    url: https://github.com/louisrubet/rpn.git
    tag: v2.4.2
    commit: cd16651dd1c3f634fe9438d24b4a63c0c825ca06
  build:
    type: cmake
    cmake_options: [-DRPN_VERSION=v2.4.2]
    ubuntu_deps: [libgmp-dev, libmpfr6, libmpfr-dev]
    fedora_deps: [mpfr, mpfr-devel]

pkg:
  package: rpn
  version: 2.4.2
  release: 0
  license: LGPLv3
  summary: Reverse Polish Notation CLI calculator
  description: rpn is a math functional language using reverse (postfix) polish notation
  maintainer: Louis Rubet <louis@rubet.fr>
  homepage: https://github.com/louisrubet/rpn
  ubuntu_deps: libmpfr6
  fedora_deps: mpfr
```

### reference

| key                     | priority                    | description                                                                                     |
|-------------------------|-----------------------------|-------------------------------------------------------------------------------------------------|
| distro                  | required                    | list of couples `distro:version` to deliver for.                                                |
|                         |                             | distros can be `ubuntu`, `fedora`, `version` must match the docker repo version string.         |
| app                     | required                    |                                                                                                 |
| app.source              | required                    | your app source description.                                                                    |
| app.source.type         | required                    | source type among:                                                                              |
|                         |                             | - `dir`: the source is a local directory,                                                       |
|                         |                             | - `git`: the source is a git repo,                                                              |
|                         |                             | - `archive`: the source is a tar or zip archive.                           _to be implemented_  |
| app.source.path         | required (`dir`, `archive`) | Path of the local directory or archive file.                                                    |
| app.source.url          | required (`git`)            | url of the `git` repo.                                                                          |
| app.source.tag          | optional (`git`)            | For type `git` the user must fill in `tag` or `commit` or both.                                 |
| app.source.commit       | optional (`git`)            | If both are provided (better) then the tag and the commit must match.                           |
| app.build               | required                    | your app source and build description.                                                          |
| app.build.type          | required                    | The build type among:                                                                           |
|                         |                             | - `cmake`: the source is built with `cmake`                                                     |
|                         |                             | - `autotool`: the source is built with `autotool`                           _to be implemented_ |
|                         |                             | - `custom`: the user provides a bash script                                 _to be implemented_ |
| app.build.cmake_options | optional (`cmake`)          | Options for `cmake`                                                                             |
| app.build.deps          | optional                    | Distro packages dependencies for building                                                       |
| pkg **(1)**             | required                    | packages description                                                                            |
| pkg.package             | required                    | package name                                                                                    |
| pkg.version             | required                    | package version                                                                                 |
| pkg.release             | required for `rpm`          | release integer                                                                                 |
| pkg.license             | required for `rpm`          |                                                                                                 |
| pkg.arch                | optional                    | default is `x86_64` for `fedora`, `amd64` for `ubuntu`                                          |
| pkg.summary             | required                    | one line description                                                                            |
| pkg.description         | required                    | long description, each new line should begin with a space for `deb`                             |
| pkg.maintainer          | required                    | a standard format is `fullname <email>`                                                         |
| pkg.section             | optional                    | Category like `utils`, `net`, `mail`, etc.                                                      |
| pkg.priority            | optional                    | Importance like `required`, `standard`, `optional`, `extra`, etc.                               |
| pkg.homepage            | optional                    | Homepage URL                                                                                    |
| pkg.depends             | optional                    | Comma-separated `package:version` list                                                          |

**(1)** The `pkg` fields match to the following package managers:

| mdpack field | `deb` DEBIAN/control file field | `rpm` spec file field | priority            |
|--------------|---------------------------------|-----------------------|---------------------|
| package      | Package                         | Name                  | required            |
| version      | Version                         | Version               | required            |
| release      | -                               | Release               | required (rpm only) |
| license      | -                               | License               | required (rpm only) |
| arch         | Architecture                    | BuildArchitectures    | required            |
| summary      | Description (1st line)          | Summary               | required            |
| description  | Description (next lines)        | %description          | required            |
| maintainer   | Maintainer                      | -                     | required            |
| section      | Section                         | -                     | optional            |
| priority     | Priority                        | -                     | optional            |
| homepage     | Homepage                        | URL                   | optional            |
| depends      | Depends                         | Requires              | optional            |


### Important remark

Every field of the manifest can be prefixed with `<distro>_` or `<distro>_<version>_` to apply the value to the matching distros only.

Example:

```yaml
distro: [fedora:34, fedora:35, ubuntu_20.04]
(...)
app:
  source:
    (...)
  build:
    type: cmake
    cmake_options: [-DRPN_VERSION=v2.4.2]
    fedora_34_cmake_options: [-DRPN_VERSION=v2.4.2, -DDEBUG]
    ubuntu_deps: [libgmp-dev, libmpfr6, libmpfr-dev]
    fedora_deps: [mpfr, mpfr-devel]
(...)
```

- `fedora_34_cmake_options` will be applied to `fedora:34` only,
- `cmake_options` will be applied to `fedora:35` and `ubuntu_20.04`
- `ubuntu_deps` will be applied to `ubuntu_20.04`
- `fedora_deps` will be applied to `fedora:34` and `fedora:35`

## Performance

Well, this is the bad part for now.

Although building the docker images is done only once,

- `git` source type:
  - a complete clone is done at every build (meaning at every distro),
  - the clone is not shallow,
- `dir` source type: a complete source copy is made at every build (meaning at every distro),
- all source types: all is built from scratch without cache
- 2 containers are run, 1 for building 1 for testing
- the user build dependencies are installed once per container.

This induces of course performance issues, but also ensures build and test integrity.

## Known issues

- the only distros that can be listed here are those with a docker image,
- you can't use your already existing`deb` or `rpm` package metadata files.
