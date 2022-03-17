- distro should be `distro: <name>:<version> like in docker

- app
    - change source_path to source: then
        - like in flatpak: cf https://manpages.debian.org/testing/flatpak-builder/flatpak-manifest.5.en.html
            - type = dir + path (sources are not copied)
            - type = archive + url (prio) + path
            - type = git + path + url + tag + commit
- app
    - build
        type = custom, cmake, autotool
- checks anti-erreurs les plus courantes (fichiers existent, yaml paramètres obligatoires, types des paramètres)

- option --force pour refaire l'image car changer les deps dans le yaml ne les fait pas refaire
- option user ou userid pour build + pkg
- script_file possible chaque fois qu'on peut mettre script
- proposer une option pour clean images et containers

- pkg
  - type: generic (+ fields), rpm + spec_file, deb + control_file
  - 

manuel
- la configuration est faite par addition de
    - votre fichier de conf
    - distro/<distro name from your conf>/distro.yaml
    - build_app/<build.type from your conf>.yaml
    - build_pkg/<pkg.type from distro or from your conf>.yaml

## Notes

The process is the following:
- creating a docker image based on the distro name and version indicated in the manifest file,
- installing complementary dev packages,
- app building and installing,
- app packaging.


- shared with docker:
  - 1 generation directory (located in /app in the docker container) containing
    - generate.sh
    - install_user_deps.sh
    - build_app.sh
    - build_pkg.sh
    - env.sh
    - src/
    - build/
    - pkg/
  - eventually 1 directory to share external sources (called /ext_sources in the docker image)


├── examples
│   └── ...
├── mdpack
│   ├── distro
│   │   ├── <distro_name>
│   │   │   ├── docker
│   │   │   │   ├── Dockerfile
│   │   │   │   └── install_default_deps.sh
│   │   │   ├── generate.sh
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
