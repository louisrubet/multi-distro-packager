# TODO

## TODO list

- [x] pkg deps should manage by prio: <distro>:<version>_deps, <distro>_deps, _deps
- [x] docker image name should begin with 'mdp-', be mdp-<distro>-<version>
- [x] package should be tested in the docker container at the end, after deps installation
- [x] change source_path to source
- [x] app source type = dir + path (sources are not copied)
- [ ] app source type = archive + url (prio) + path (+ signature)
- [x] app source type = git + url + (tag | commit)
- [ ] app build type = custom
- [x] app build type cmake
- [ ] app build type autotool
- [ ] app build type python
- [ ] distro `debian`
- [ ] distro `archlinux`
- [ ] distro `centos`
- [ ] checks most current errors (files exist, yaml required parameters, parameters types)
- [ ] option --force to rebuild the image because changing the user deps in the yaml doesn't make docker rebuild the image
- [ ] option --prune or --clean to clean docker images and containers
- [x] option --verbose or -v
- [ ] manifest should add a user + userid configuration (build_as ?)
- [x] distro(+version) entry in manifest must have a default (ex: if there is ubuntu_deps there must have deps too)
- [x] manifest mandatory fields check
- [ ] ~~docker image should include user deps~~

