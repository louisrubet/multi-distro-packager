# TODO

## TODO list

- [x] pkg deps should manage by prio: <distro>:<version>_deps, <distro>_deps, _deps
- [x] docker image name should begin with 'mdp-', be mdp-<distro>-<version>
- [ ] package should be tested in the docker container at the end, after deps installation
- [x] change source_path to source
- [x] app source type = dir + path (sources are not copied)
- [ ] app source type = archive + url (prio) + path (+ signature)
- [ ] app source type = git + path + url + tag + commit
- [ ] app build type = custom
- [x] app build type cmake
- [ ] app build type autotool
- [ ] app build type python
- [ ] checks most current errors (files exist, yaml required parameters, parameters types)
- [ ] option --force to rebuild the image pour refaire l'image car changer les deps dans le yaml ne les fait pas refaire
- [ ] option --prune or --clean to clean docker images and containers
- [ ] manifest should add a user + userid configuration (build_as ?)
- [ ] distro(+version) entry in manifest must have a default (ex: if there is ubuntu_deps there must have deps too)
- [ ] ~~docker image should include user deps~~

manuel
- la configuration est faite par addition de
    - votre fichier de conf
    - distro/<distro name from your conf>/distro.yaml
    - build_app/<build.type from your conf>.yaml
    - build_pkg/<pkg.type from distro or from your conf>.yaml

## Notes

You should be able to run docker without being root
`docker run hello-world`

```
docker run -it ubuntu bash
root@df69f66bb799:/# apt update
Get:1 http://archive.ubuntu.com/ubuntu focal InRelease [265 kB]
Get:2 http://security.ubuntu.com/ubuntu focal-security InRelease [114 kB]
(...)
```

The process is the following:
- creating a docker image based on the distro name and version indicated in the manifest file,
- installing complementary dev packages,
- app building and installing,
- app packaging.

- shared with docker:
  - 1 generation directory (located in /app in the docker container) containing
    - whole_process.sh
    - install_user_deps.sh
    - build_app.sh
    - build_pkg.sh
    - env.sh
    - src/
    - build/
    - pkg/
  - eventually 1 directory to share external sources (called /ext_sources in the docker image)

```
├── examples
│   └── ...
├── mdpack
│   ├── distro
│   │   ├── <distro_name>
│   │   │   ├── docker
│   │   │   │   ├── Dockerfile
│   │   │   │   └── install_default_deps.sh
│   │   │   ├── whole_process.sh
│   │   │   ├── install_users_deps.sh
│   │   │   └── <distro_name>.yaml
│   │   └── (...)
│   └── scripts
│       ├── build
│       │   ├── cmake.sh
│       │   └── (...)
│       └── pkg
│           └── deb.sh
│           └── (...)
├── mdpack.py
├── README.md
├── spec.md
├── test_manifest.yaml
├── tests
│   ├── tests.py
│   └── (...)
└── TODO.md
```

https://packaging.ubuntu.com/html/
https://packagecloud.io/l/apt-repository


DEB
https://manpages.debian.org/testing/dpkg-dev/deb-control.5.en.html
https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-binarycontrolfiles

DEBIAN/control:

- [x] Package (mandatory)
- [ ] Source
- [x] Version (mandatory)
- [x] Section (recommended) This is a general field that gives the package a category based on the software that it installs. Some common sections are utils, net, mail, text, x11, etc.
- [x] Priority (recommended) Sets the importance of this package in relation to the system as a whole. Common priorities are required, standard, optional, extra, etc.
- [x] Architecture (mandatory)
- [ ] Essential
- [ ] Depends
- [ ] Installed-Size
- [x] Maintainer (mandatory)
- [x] Description (mandatory)
- [x] Homepage
- [ ] Built-Using

RPM
https://rpm-software-management.github.io/rpm/manual/spec.html

- [x] Name The base name of the package, which should match the SPEC file name.
- [x] Version The upstream version number of the software.
- [ ] Release The number of times this version of the software was released.
- [x] Summary A brief, one-line summary of the package.
- [ ] License The license of the software being packaged.
- [x] URL The full URL for more information about the program. Most often this is the upstream project website for the software being packaged.
- [ ] Source0 Path or URL to the compressed archive of the upstream source code (unpatched, patches are handled elsewhere).
- [ ] Patch0 The name of the first patch to apply to the source code if necessary.
- [x] BuildArch If the package is not architecture dependent BuildArch: noarch. If not set, the package automatically inherits the Architecture of the machine on which it is built, for example x86_64.
- [ ] BuildRequires A comma- or whitespace-separated list of packages required for building the program written in a compiled language. There can be multiple entries of BuildRequires, each on its own line in the SPEC file.
- [ ] Requires A comma- or whitespace-separated list of packages required by the software to run once installed. There can be multiple entries of Requires, each on its own line in the SPEC file.
- [ ] ExcludeArch If a piece of software can not operate on a specific processor architecture, you can exclude that architecture here.

| generic     | deb control field        | rpm spec field     | priority            | descr | notes                                                     |
|-------------|--------------------------|--------------------|---------------------|-------|-----------------------------------------------------------|
| package     | Package                  | Name               | required            |       | Package name                                              |
| version     | Version                  | Version            | required            |       | Package version                                           |
| release     | -                        | Release            | required (rpm only) |       | Package release                                           |
| license     | -                        | License            | required (rpm only) |       |                                                           |
| arch        | Architecture             | BuildArchitectures | optional            |       | By default: `amd64` for deb and `x86_64` for rpm.         |
|             |                          |                    |                     |       | `auto`: arch is deduced from build                        |
|             |                          |                    |                     |       | `all` for deb will be changed to `noarch` on rpm          |
| summary     | Description (1st line)   | Summary            | required            |       | One line description                                      |
| description | Description (next lines) | %description       | required            |       | Long description                                          |
| maintainer  | Maintainer               | -                  | required            |       | `fullname <email>`                                        |
| section     | Section                  | -                  | optional            |       | Category like `utils`, `net`, `mail`, etc.                |
| priority    | Priority                 | -                  | optional            |       | Importance like required, standard, optional, extra, etc. |
| homepage    | Homepage                 | URL                | optional            |       | Homepage URL                                              |
| depends     | Depends                  | Requires           | optional            |       | Comma-separated `package:version` list                    |

- manifest manual

| entry    | priority | note                                      |
|----------|----------|-------------------------------------------|
| `distro` | required | ex: `distro: [ ubuntu:20.04, fedora:34 ]` |

RPMBUILD

mkdir -p rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
rpmbuild --define "_topdir `pwd`" -v -ba SPECS/{*spec_file.specs*}

- distros
`ubuntu`, `fedora`, `mint`, `opensuse`, `arch`, `debian`, `centos`, `manjaro`, `elementary`, `zorin`, `cute fish`, `deepin`

- why flatpak is better

cf https://www.youtube.com/watch?v=zs9QpPKDw74&ab_channel=TheLinuxExperiment

old world:
- dependencies problems, multiple ppa
- packages to be done for every distro x release x architecture -> updates, maintainance
- retro-compatibility of the applications (old libs)
- security issues (privileged installation, unbound packages)
- so for security reasons some versions are frozen for some years (ubuntu LTS for example)

flatpak
- one package for all distros
- safer at install time because not installed as root
- safer at runtime because sandboxed (even if not perfect, is many miles ahead from no sandboxing)
- cannot break the user apps
- now well integrated in app stores

Not very space-efficient, but that's only half true: libraries are shared between packages.
Flatpak packages don't use more RAM than regular packages.

why not snap?
- held by Canonical, which annoys people
- has a closed backend source code
- designed for servers and IoT first (-> slow to start ??)
- not really well integratd with your desktop
- less apps than flathub (?)
