#!/usr/bin/env python3

import sys
import os
import subprocess
import shutil
import logging
import yaml  # pip install pyyaml
from cerberus import Validator  # pip cerberus pyyaml
import argparse

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')

# mdpack's own files (distros, scripts), wherever it is run from
MDPACK_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mdpack')

# Cache kept between builds (Rust toolchain, crates...), mounted as /cache
CACHE_DIR = os.path.join(os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), 'mdpack')


class LocalScript:
    def __init__(self, name):
        try:
            self.path = os.path.realpath(name)
            self.file = open(self.path, mode="w+")
        except:
            logging.critical(rf"Couldn't open {self.path} for writing")

    def path(self):
        self.file.close()
        return self.path

    def append(self, text):
        self.file.write(text)
        return self

    def close(self):
        self.file.close()


class LocalDirectory:
    def __init__(self, name, clear_if_exist=True):
        self.path = ''
        try:
            self.path = os.path.realpath(name)
            if os.path.exists(name) and clear_if_exist:
                shutil.rmtree(self.path)
            if not os.path.exists(name):
                os.makedirs(name, mode=0o777)
        except:
            logging.critical(f'Problem in creating {name}')

    def path(self):
        return self.path


class AddingYaml():
    def __init__(self, yaml_path):
        self.dict = dict()
        try:
            with open(yaml_path) as file:
                self.dict = yaml.full_load(file)
        except:
            logging.critical(f'Error opening manifest "{yaml_path}", does this file exist?')

    def __add__(self, o):
        return self.complete(self.dict, o.dict)

    def complete(self, a, b, path=[]):
        # cf https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.complete(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]
        return self


class Manifest:
    def __init__(self, in_dict):
        "transform dictionary to object"
        # cf https://joelmccune.com/python-dictionary-as-object/
        for key, val in in_dict.items():
            if isinstance(val, (list, tuple)):
                setattr(self, key, [Manifest(x) if isinstance(x, dict) else x for x in val])
            else:
                setattr(self, key, Manifest(val) if isinstance(val, dict) else val)

    @staticmethod
    def check_required_fields(in_dict):
        schema = {
            'distro': {
                'required': True,
                'type': 'list',
                'schema': {'type': 'string'}
            },
            'app': {
                'required': True,
                'type': 'dict',
                'schema': {
                    'source': {
                        'required': True,
                        'type': 'dict',
                        'schema': {'type': {'required': True, 'type': 'string'}}
                    },
                    'build': {
                        'required': True,
                        'type': 'dict',
                        'schema': {'type': {'required': True, 'type': 'string'}}
                    }
                }
            },
            'pkg': {
                'required': True,
                'type': 'dict',
                'schema': {
                    'package': {'required': True, 'type': 'string'},
                    'version': {'required': True, 'type': 'string'}
                }
            }
        }
        val = Validator(schema, allow_unknown=True)
        if not val.validate(in_dict, schema):
            logging.critical('Manifest validation error')
            logging.critical(val.errors)
            return False
        return True

    @staticmethod
    def add_defaults(in_dict, distro, version):
        "Add key=XXX when distro_key or distro_version_key exist"
        d = distro + '_'
        dv = distro + '_' + version + '_'
        add_list = list()
        for key, val in in_dict.items():
            if isinstance(val, dict):
                Manifest.add_defaults(val, distro, version)
            else:
                kern = None
                if key.startswith(d):
                    kern = key[len(d):]
                if key.startswith(dv):
                    kern = key[len(dv):]
                if kern is not None and not kern in in_dict:
                    add_list.append(kern)
        for element in add_list:
            in_dict[element] = ''

    @staticmethod
    def substitute_defaults(in_dict, distro, version):
        "Replace value in key=value with value from distro_version_key=value or distro_key=value"
        d = distro + '_'
        dv = distro + '_' + version + '_'
        for key, val in in_dict.items():
            if isinstance(val, dict):
                Manifest.substitute_defaults(val, distro, version)
            elif in_dict.get(dv + key) is not None:
                in_dict[key] = in_dict[dv + key]
            elif in_dict.get(d + key) is not None:
                in_dict[key] = in_dict[d + key]


class PkgConfBuilder:
    def __init__(self, manifest, dest_dir):
        match (manifest.pkg.type):
            case 'deb':
                self.to_deb(manifest, dest_dir)
            case 'rpm':
                self.to_rpm(manifest, dest_dir)
            case 'pacman':
                self.to_pacman(manifest, dest_dir)

    def write(self, file, text, manifest, field):
        if hasattr(manifest, field):
            file.write(text + str(getattr(manifest, field)) + '\n')
            return True
        return False

    def to_deb(self, manifest, dest_dir):
        LocalDirectory(dest_dir + '/install/DEBIAN')

        # DEBIAN/control file structure
        with open(dest_dir + '/install/DEBIAN/control', 'w+') as conf:
            self.write(conf, 'Package: ', manifest.pkg, 'package')
            self.write(conf, 'Version: ', manifest.pkg, 'version')
            self.write(conf, 'Architecture: ', manifest.pkg, 'arch')
            if hasattr(manifest.pkg, 'summary') and hasattr(manifest.pkg, 'description'):
                conf.write('Description: ' + str(manifest.pkg.summary) + '\n ' + str(manifest.pkg.description) + '\n')
            self.write(conf, 'Maintainer: ', manifest.pkg, 'maintainer')
            self.write(conf, 'Section: ', manifest.pkg, 'section')
            self.write(conf, 'Priority: ', manifest.pkg, 'priority')
            self.write(conf, 'Homepage: ', manifest.pkg, 'homepage')
            self.write(conf, 'Depends: ', manifest.pkg, 'deps')
            conf.close()

    def to_rpm(self, manifest, dest_dir):
        LocalDirectory(dest_dir + '/rpmbuild/SPECS/')

        # RPM spec file structure
        with open(dest_dir + '/rpmbuild/SPECS/pkg.spec', 'w+') as conf:
            self.write(conf, 'Name: ', manifest.pkg, 'package')
            self.write(conf, 'Version: ', manifest.pkg, 'version')
            self.write(conf, 'Release: ', manifest.pkg, 'release')
            self.write(conf, 'License: ', manifest.pkg, 'license')
            self.write(conf, 'BuildArchitectures: ', manifest.pkg, 'arch')
            self.write(conf, 'Summary: ', manifest.pkg, 'summary')
            self.write(conf, 'URL: ', manifest.pkg, 'homepage')
            self.write(conf, 'Requires: ', manifest.pkg, 'deps')
            self.write(conf, '%description\n', manifest.pkg, 'description')
            conf.write('%define _build_id_links none\n')
            conf.write('%define debug_package %{nil}\n')
            conf.write('%prep\n')
            conf.write('%build\n')
            conf.write('%install\ncp -rf /app/install/. %{buildroot}/\n')
            # automatic list of files in /app/install
            # excluding already existing files and directories
            conf.write(r"find /app/install -name '*' | sed 's/\/app\/install//g' | tail -n +2")
            conf.write(
                " | bash -c 'while read file ; do [ ! -f ${file} -a ! -d ${file} ] "
                "&& echo \"${file}\"; done' > /app/rpmbuild/files_list\n")
            conf.write('%files -f /app/rpmbuild/files_list\n')
            conf.close()

    def to_pacman(self, manifest, dest_dir):
        LocalDirectory(dest_dir + '/pacman')

        # PKGBUILD packaging what was built and installed in /app/install
        def quoted(value):
            return "'" + str(value).replace("'", "'\\''") + "'"

        pkg = manifest.pkg
        with open(dest_dir + '/pacman/PKGBUILD', 'w+') as conf:
            conf.write(f'pkgname={quoted(pkg.package)}\n')
            conf.write(f'pkgver={quoted(pkg.version)}\n')
            conf.write(f'pkgrel={quoted(getattr(pkg, "release", 1))}\n')
            conf.write(f'pkgdesc={quoted(getattr(pkg, "summary", ""))}\n')
            conf.write(f'arch=({quoted(pkg.arch)})\n')
            if hasattr(pkg, 'homepage'):
                conf.write(f'url={quoted(pkg.homepage)}\n')
            if hasattr(pkg, 'license'):
                conf.write(f'license=({quoted(pkg.license)})\n')
            deps = str(getattr(pkg, 'deps', '') or '').replace(',', ' ').split()
            conf.write('depends=(' + ' '.join(quoted(d) for d in deps) + ')\n')
            conf.write('options=(!debug)\n')
            conf.write('package() {\n    cp -a /app/install/. "$pkgdir"/\n}\n')
            conf.close()


class Packager:

    @ staticmethod
    def get_distro_version(distro_version):
        split = distro_version.split(':')
        if len(split) != 2:
            logging.critical(f'Incorrect "{distro_version}", should be <distro>:<name>')
            return '', ''
        return split[0], split[1]

    @ staticmethod
    def run(args):
        result = subprocess.run(args, capture_output=True)
        if (result.returncode != 0):
            logging.critical(result.stdout.decode('utf-8', 'replace'))
            logging.critical(result.stderr.decode('utf-8', 'replace'))
            return False
        logging.debug(result.stdout.decode("utf-8"))
        return True

    def package_name(self, manifest):
        # the compound package name is based on rpm full package name convention
        # <PKG_PACKAGE>-<PKG_VERSION>[-PKG_RELEASE].<PKG_ARCH>.<PKG_TYPE>
        # ex: rpn-2.4.2-0.x86_64.rpm
        # pacman has its own: <PKG_PACKAGE>-<PKG_VERSION>-<PKG_RELEASE>-<PKG_ARCH>.pkg.tar.zst
        name = f'{manifest.pkg.package}-{manifest.pkg.version}'
        if manifest.pkg.type == 'pacman':
            return name + f'-{getattr(manifest.pkg, "release", 1)}-{manifest.pkg.arch}.pkg.tar.zst'
        if getattr(manifest.pkg, 'release', None) is not None:
            name += f'-{manifest.pkg.release}'
        name += f'.{manifest.pkg.arch}.{manifest.pkg.type}'
        return name

    def package_final_name(self, distro, version, manifest):
        # the complete name of the delivered package
        # ex: fedora-35-rpn-2.4.2-0.x86_64.rpm
        return distro + '-' + version + '-' + self.package_name(manifest)

    def container_name(self, image_tag, manifest):
        return image_tag + '-' + manifest.pkg.package

    def container_shared_dir(self, image_tag, manifest):
        return LocalDirectory(self.container_name(image_tag, manifest)).path

    def make_docker_image(self, distro, version, image_tag):
        # docker image
        dockerfile_path = MDPACK_DIR + '/distro/' + distro + '/docker'

        # TODO --network host to be removed if possible (security)
        return Packager.run(['docker', 'build', '--network', 'host', '--build-arg',
                             f'VERSION={version}', '--tag', image_tag, dockerfile_path])

    def export_env(self, env, env_name, manifest_obj, manifest_attr):
        "export a manifest entry as a shell env variable"
        if hasattr(manifest_obj, manifest_attr):
            val = getattr(manifest_obj, manifest_attr)
            env.append(f'export {env_name}="{val}"\n')

    def export_env_list(self, env, env_name, manifest_obj, manifest_attr):
        "export a list manifest entry as a shell env variable"
        if hasattr(manifest_obj, manifest_attr):
            val_list = getattr(manifest_obj, manifest_attr)
            if len(val_list) > 0:
                env.append(f'export {env_name}="')
                for val in val_list:
                    env.append(val + ' ')
                env.append('"\n')

    def make_env_script(self, dest_dir, manifest):
        env = LocalScript(dest_dir + '/env.sh')
        env.append('#!/bin/bash\n')
        self.export_env(env, 'PKG_PACKAGE', manifest.pkg, 'package')
        self.export_env_list(env, 'APP_BUILD_CMAKE_OPTIONS', manifest.app.build, 'cmake_options')
        self.export_env_list(env, 'APP_BUILD_CARGO_OPTIONS', manifest.app.build, 'cargo_options')
        self.export_env_list(env, 'APP_BUILD_CARGO_BINS', manifest.app.build, 'cargo_bins')
        self.export_env_list(env, 'APP_BUILD_FILES', manifest.app.build, 'files')
        self.export_env(env, 'APP_BUILD_RUST_VERSION', manifest.app.build, 'rust_version')
        self.export_env_list(env, 'APP_BUILD_DEPS', manifest.app.build, 'deps')
        if hasattr(manifest, 'test'):
            self.export_env(env, 'TEST_COMMAND', manifest.test, 'command')
        env.append(f'export PKG_FILENAME={self.package_name(manifest)}\n')
        env.close()

    def make_user_deps_script(self, dest_dir, manifest, distro):
        if hasattr(manifest.app.build, 'deps'):
            shutil.copy(MDPACK_DIR + '/distro/' + distro + '/install_user_deps.sh',
                        dest_dir + '/install_user_deps.sh')

    def make_build_script(self, dest_dir, manifest):
        src_path = MDPACK_DIR + '/scripts/build/' + manifest.app.build.type + '.sh'
        if (os.path.exists(src_path)):
            shutil.copy(src_path, dest_dir + '/build.sh')

    def make_pkg_script(self, dest_dir, manifest):
        src_path = MDPACK_DIR + '/scripts/pkg/' + manifest.pkg.type + '.sh'
        if (os.path.exists(src_path)):
            PkgConfBuilder(manifest, dest_dir)
            shutil.copy(src_path, dest_dir + '/pkg.sh')

    def make_process_script(self, dest_dir, manifest, distro):
        src_path = MDPACK_DIR + '/distro/' + distro + '/whole_process.sh'
        if (os.path.exists(src_path)):
            shutil.copy(src_path, dest_dir + '/whole_process.sh')

    def make_test_script(self, dest_dir, manifest, distro):
        src_path = MDPACK_DIR + '/scripts/test/' + distro + '.sh'
        if (os.path.exists(src_path)):
            shutil.copy(src_path, dest_dir + '/test.sh')

    def extract_source(self, dest_dir, manifest):
        match manifest.app.source.type:
            case 'dir':
                return Packager.run(['cp', '-rp', manifest.app.source.path + '/.', dest_dir])

            case 'git':
                LocalDirectory(dest_dir)

                # first check required fields
                if not hasattr(manifest.app.source, 'url'):
                    logging.critical('app.source.url is required for git type')
                    return False
                if not hasattr(manifest.app.source, 'tag') and not hasattr(manifest.app.source, 'commit'):
                    logging.critical('app.source.tag or app.source.commit is required for git type')
                    return False

                # check commit and tag match (the commit of an annotated tag is its peeled ref)
                if hasattr(manifest.app.source, 'tag') and hasattr(manifest.app.source, 'commit'):
                    tag = f'refs/tags/{manifest.app.source.tag}'
                    result = subprocess.run(['git', 'ls-remote', manifest.app.source.url, tag, tag + '^{}'],
                                            capture_output=True, text=True)
                    refs = dict(reversed(line.split('\t')) for line in result.stdout.splitlines())
                    found = refs.get(tag + '^{}', refs.get(tag))
                    if found != str(manifest.app.source.commit):
                        logging.critical(f'tag {manifest.app.source.tag} is {found}, '
                                         f'not commit {manifest.app.source.commit}')
                        return False

                if hasattr(manifest.app.source, 'tag'):
                    commit = manifest.app.source.tag
                elif hasattr(manifest.app.source, 'commit'):
                    commit = manifest.app.source.commit

                # clone and checkout
                if not Packager.run(['git', 'clone', '--recurse-submodules', manifest.app.source.url, dest_dir]):
                    return False

                return Packager.run(['git', '-C', dest_dir, 'checkout', commit])

        logging.critical(f'source type "{manifest.app.source.type}" is unknown')
        return False

    def build(self, image_tag, distro, version, manifest):
        dest_dir = self.container_shared_dir(image_tag, manifest)

        # generate process scripts
        self.make_env_script(dest_dir, manifest)
        self.make_user_deps_script(dest_dir, manifest, distro)
        self.make_build_script(dest_dir, manifest)
        self.make_pkg_script(dest_dir, manifest)
        self.make_process_script(dest_dir, manifest, distro)

        if (not self.extract_source(dest_dir + '/src', manifest)):
            return False

        # run a docker container, which entry point is '/app/whole_process.sh'
        # TODO should we create unnamed containers instead?
        subprocess.run(['docker', 'stop', self.container_name(image_tag, manifest)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['docker', 'rm', self.container_name(image_tag, manifest)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # TODO --net=host probably bad for security
        cache_dir = LocalDirectory(os.path.join(CACHE_DIR, image_tag), clear_if_exist=False).path
        if not Packager.run(
            ['docker', 'run', *Packager.interactive(), '--net=host', '--rm', '--name',
             self.container_name(image_tag, manifest), '-v', dest_dir + ':/app:z', '-v', cache_dir + ':/cache:z',
             image_tag, '/bin/bash', '-x', '/app/whole_process.sh']):
            return False

        # deliver the generated package near the current script
        if os.path.exists(dest_dir + '/' + self.package_name(manifest)):
            shutil.copyfile(dest_dir + '/' + self.package_name(manifest),
                            dest_dir + '/../' + self.package_final_name(distro, version, manifest))

        return True

    def test(self, image_tag, distro, version, manifest):
        dest_dir = LocalDirectory(self.container_name(image_tag, manifest), clear_if_exist=False).path

        # generate test script
        self.make_env_script(dest_dir, manifest)
        self.make_test_script(dest_dir, manifest, distro)

        # TODO --net=host probably bad for security
        return Packager.run(
            ['docker', 'run', *Packager.interactive(), '--net=host', '--rm', '-v', dest_dir + ':/app:z',
             distro + ':' + version, '/bin/bash', '-x', '/app/test.sh'])

    @ staticmethod
    def interactive():
        "docker run options: a terminal only when there is one"
        return ['-it'] if sys.stdin.isatty() else ['-i']


class Options():

    @ staticmethod
    def parse():
        # -h option is provided by default
        parser = argparse.ArgumentParser()
        parser.add_argument('manifests', metavar='manifest_file', type=str, nargs='+', help='manifest files')
        parser.add_argument('-v', '--verbose', action='store_true', help='increase verbosity')
        Options.args = parser.parse_args()


def main():

    Options.parse()
    if Options.args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    for path in Options.args.manifests:

        pak = Packager()
        user_manifest = AddingYaml(path)
        if not user_manifest.dict:
            continue

        for distro_version in user_manifest.dict['distro']:

            distro, version = pak.get_distro_version(distro_version)
            if not distro:
                continue

            # complete manifest with distro fields then replace default entries by distro entries
            distro_yaml = MDPACK_DIR + '/distro/' + distro + '/' + distro + '.yaml'
            distro_dict = (AddingYaml(path) + AddingYaml(distro_yaml)).dict
            Manifest.add_defaults(distro_dict, distro, version)
            Manifest.substitute_defaults(distro_dict, distro, version)
            if not Manifest.check_required_fields(distro_dict):
                logging.critical(f'Please correct the file {path}')
                os._exit(1)

            manifest = Manifest(distro_dict)

            # 1. build docker image
            logging.info('Processing ' + distro + '-' + version)
            logging.info('- building docker image ' + distro + '-' + version)
            image_tag = 'mdp-' + distro + '-' + version
            if (not pak.make_docker_image(distro=distro,
                                          version=version,
                                          image_tag=image_tag)):
                logging.critical('FAILED, is docker running on your host?')
                continue

            # 2. build the sources and package them
            logging.info('- building ' + pak.package_name(manifest))
            if (not pak.build(image_tag=image_tag, distro=distro, version=version, manifest=manifest)):
                logging.critical('FAILED')
                continue

            # 3. test the package installation
            logging.info('- testing ' + pak.package_final_name(distro, version, manifest))
            if (not pak.test(image_tag=image_tag, distro=distro, version=version, manifest=manifest)):
                logging.critical('FAILED')
                continue


if __name__ == '__main__':
    main()
