#!/usr/bin/env python3

import sys
import os
import subprocess
import yaml  # pip install pyyaml
# import tempfile
import shutil
import glob


class Log:
    def __init__(self):
        self.check_begun = False

    def stop_check(self, critical=False):
        if self.check_begun:
            if critical:
                print('FAILED')
            else:
                print('ok')
        self.check_begun = False

    def critical(self, text):
        self.stop_check(critical=True)
        print(text)

    def info(self, text):
        self.stop_check()
        print(text)

    def debug(self, text):
        self.stop_check()
        print(text)
        pass

    def check(self, text):
        self.stop_check()
        self.check_begun = True
        print(text + ' .. ', end='')
        sys.stdout.flush()


logger = Log()


def syntax():
    logger.info('Syntax: deliver.py manifest.yaml ...')


class LocalScript:
    def __init__(self, name):
        # self.path = tempfile.gettempdir() + '/' + name
        self.path = os.path.realpath(name)
        self.file = open(self.path, mode="w+")

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
        # self.path = tempfile.TemporaryDirectory()
        self.path = os.path.realpath(name)
        if os.path.exists(name) and clear_if_exist:
            shutil.rmtree(self.path)
        if not os.path.exists(name):
            os.makedirs(name, mode=0o777)

    def path(self):
        return self.path


class AddingYaml():
    def __init__(self, yaml_path):
        self.dict = dict()
        with open(yaml_path) as file:
            self.dict = yaml.full_load(file)

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


class DictObj():
    # cf https://joelmccune.com/python-dictionary-as-object/
    def __init__(self, in_dict):
        for key, val in in_dict.items():
            if isinstance(val, (list, tuple)):
                setattr(self, key, [DictObj(x) if isinstance(x, dict) else x for x in val])
            else:
                setattr(self, key, DictObj(val) if isinstance(val, dict) else val)


class PkgConfBuilder:
    def __init__(self, manifest, distro, version, dest_dir):
        match (distro):
            case 'ubuntu':
                self.to_deb(manifest, distro, version, dest_dir)
            case 'fedora':
                self.to_rpm(manifest, distro, version, dest_dir)

    def write(self, file, text, manifest, field):
        if hasattr(manifest.pkg, field):
            file.write(text + str(getattr(manifest.pkg, field)) + '\n')
            return True
        return False

    def to_deb(self, manifest, distro, version, dest_dir):
        if not os.path.exists(dest_dir + '/install/DEBIAN'):
            os.makedirs(dest_dir + '/install/DEBIAN', mode=0o777)
        # DEBIAN/control file structure
        with open(dest_dir + '/install/DEBIAN/control', 'w+') as conf:
            self.write(conf, 'Package: ', manifest, 'package')
            self.write(conf, 'Version: ', manifest, 'version')
            self.write(conf, 'Architecture: ', manifest, 'arch')
            self.write(conf, 'Description: ', manifest, 'description')
            self.write(conf, 'Maintainer: ', manifest, 'maintainer')
            self.write(conf, 'Section: ', manifest, 'section')
            self.write(conf, 'Priority: ', manifest, 'priority')
            self.write(conf, 'Homepage: ', manifest, 'homepage')
            if not self.write(conf, 'Depends: ', manifest, distro + '-' + version + '-' + 'deps'):
                if not self.write(conf, 'Depends: ', manifest, distro + '-' + 'deps'):
                    self.write(conf, 'Depends: ', manifest, 'deps')
            conf.close()

    def to_rpm(self, manifest, distro, version, dest_dir):
        if not os.path.exists(dest_dir + '/rpmbuild/SPECS/'):
            os.makedirs(dest_dir + '/rpmbuild/SPECS/', mode=0o777)
        # RPM spec file structure
        with open(dest_dir + '/rpmbuild/SPECS/pkg.spec', 'w+') as conf:
            self.write(conf, 'Name: ', manifest, 'package')
            self.write(conf, 'Version: ', manifest, 'version')
            self.write(conf, 'Release: ', manifest, 'release')
            self.write(conf, 'License: ', manifest, 'license')
            self.write(conf, 'BuildArchitectures: ', manifest, 'arch')
            self.write(conf, 'Summary: ', manifest, 'summary')
            self.write(conf, 'URL: ', manifest, 'Homepage')
            if not self.write(conf, 'Requires: ', manifest, distro + '-' + version + '-' + 'deps'):
                if not self.write(conf, 'Requires: ', manifest, distro + '-' + 'deps'):
                    self.write(conf, 'Requires: ', manifest, 'deps')
            self.write(conf, '%description\n', manifest, 'description')
            conf.write('%define _build_id_links none\n')
            conf.write('%prep\n')
            conf.write('%build\n')
            conf.write('%install\ncp -rf /app/install/. %{buildroot}/\n')  # TODO a link here?
            # automatic list of files in /app/install
            # excluding already existing files and directories
            conf.write("find /app/install -name '*' | sed 's/\/app\/install//g' | tail -n +2")
            conf.write(
                " | bash -c 'while read file ; do [ ! -f ${file} -a ! -d ${file} ] && echo \"${file}\"; done' > /app/rpmbuild/files_list\n")
            conf.write('%files -f /app/rpmbuild/files_list\n')
            conf.close()


class Packager:
    def __init__(self):
        pass

    def package_name(self, manifest):
        # the compound package name is based on rpm full package name convention
        # <PKG_PACKAGE>-<PKG_VERSION>[-PKG_RELEASE].<PKG_ARCH>.<PKG_TYPE>
        # ex: rpn-2.4.2-0.x86_64.rpm
        name = f'{manifest.pkg.package}-{manifest.pkg.version}'
        if hasattr(manifest.pkg, 'release'):
            name += f'-{manifest.pkg.release}'
        name += f'.{manifest.pkg.arch}.{manifest.pkg.type}'
        return name

    def package_final_name(self, distro, version, manifest):
        # the complete name of the delivered package
        # ex: fedora-35-rpn-2.4.2-0.x86_64.rpm
        return distro + '-' + version + '-' + self.package_name(manifest)

    def make_docker_image(self, distro, version, image_tag):
        # docker image
        dockerfile_path = os.path.dirname(__file__) + '/mdpack/distro/' + distro + '/docker'
        result = subprocess.run(
            ['docker', 'build', '--build-arg', f'VERSION={version}', '--tag', image_tag, dockerfile_path],
            stdout=subprocess.PIPE)

        logger.debug(result.stdout.decode("utf-8"))

        if (result.returncode != 0):
            logger.critical(result.stdout.decode("utf-8"))
            return False
        return True

    def export_env(self, env, env_name, manifest_obj, manifest_attr):
        try:
            if hasattr(manifest_obj, manifest_attr):
                val = getattr(manifest_obj, manifest_attr)
                env.append(f'export {env_name}="{val}"\n')
        finally:
            pass

    def export_env_list(self, env, env_name, manifest_obj, manifest_attr):
        try:
            if hasattr(manifest_obj, manifest_attr):
                val_list = getattr(manifest_obj, manifest_attr)
                env.append(f'export {env_name}="')
                for val in val_list:
                    env.append(val + ' ')
                env.append('"\n')
        finally:
            pass

    def generate_env(self, dest_dir, manifest, distro, version):
        env = LocalScript(dest_dir + '/env.sh')
        env.append('#!/bin/bash\n')
        self.export_env(env, 'PKG_NAME', manifest.pkg, 'package')
        self.export_env_list(env, 'APP_BUILD_CMAKE_OPTIONS', manifest.app.build, 'cmake_options')
        if hasattr(manifest.app.build, distro + '_' + version + '_deps'):
            self.export_env_list(env, 'APP_BUILD_DEPS', manifest.app.build, distro + '_' + version + '_deps')
        elif hasattr(manifest.app.build, distro + '_deps'):
            self.export_env_list(env, 'APP_BUILD_DEPS', manifest.app.build, distro + '_deps')
        elif hasattr(manifest.app.build, 'deps'):
            self.export_env_list(env, 'APP_BUILD_DEPS', manifest.app.build, 'deps')
        env.append(f'export PKG_FILENAME={self.package_name(manifest)}\n')
        env.close()

    def generate_user_deps(self, dest_dir, manifest, distro, version):
        if hasattr(
                manifest.app.build, distro + '_' + version + '_deps') or hasattr(
                manifest.app.build, distro + '_deps') or hasattr(
                manifest.app.build, 'deps'):
            shutil.copy('mdpack/distro/' + distro + '/install_user_deps.sh',
                        dest_dir + '/install_user_deps.sh')

    def generate_build_app(self, dest_dir, manifest, distro):
        src_path = 'mdpack/scripts/build/' + manifest.app.build.type + '.sh'
        if (os.path.exists(src_path)):
            shutil.copy(src_path, dest_dir + '/build_app.sh')

    def generate_build_pkg(self, dest_dir, manifest, distro, version):
        src_path = 'mdpack/scripts/pkg/' + manifest.pkg.type + '.sh'
        if (os.path.exists(src_path)):
            PkgConfBuilder(manifest, distro, version, dest_dir)
            shutil.copy(src_path, dest_dir + '/build_pkg.sh')

    def generate_process_script(self, dest_dir, manifest, distro):
        src_path = 'mdpack/distro/' + distro + '/generate.sh'
        if (os.path.exists(src_path)):
            shutil.copy(src_path, dest_dir + '/generate.sh')

    def extract_source(self, dest_dir, manifest):
        match manifest.app.source.type:
            case 'dir':
                result = subprocess.run(['cp', '-rp', manifest.app.source.path + '/.', dest_dir + '/src'],
                                        stdout=subprocess.PIPE)
                if (result.returncode != 0):
                    logger.critical(result.stdout.decode('utf-8'))
                    return False
        return True

    def build_and_install(self, image_tag, distro, version, manifest):
        container_name = image_tag + '-' + manifest.pkg.package
        local_dir = LocalDirectory(f'{container_name}').path

        # generate process scripts
        self.generate_env(local_dir, manifest, distro, version)
        self.generate_user_deps(local_dir, manifest, distro, version)
        self.generate_build_app(local_dir, manifest, distro)
        self.generate_build_pkg(local_dir, manifest, distro, version)
        self.generate_process_script(local_dir, manifest, distro)

        if (not self.extract_source(local_dir, manifest)):
            return False

        # run a docker container, which entry point is '/app/generate.sh'
        subprocess.run(['docker', 'stop', container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['docker', 'rm', container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        result = subprocess.run(
            ['docker', 'run', '-it', '--rm', '--name', container_name,
             '-v', f'{local_dir}:/app',
             image_tag, '/bin/sh', '-x', '/app/generate.sh'], stdout=subprocess.PIPE)

        logger.debug(result.stdout.decode('utf-8'))

        if (result.returncode != 0):
            logger.critical(result.stdout.decode('utf-8'))
            return False

        # deliver the generated package near the current script
        if os.path.exists(local_dir + '/' + self.package_name(manifest)):
            shutil.move(local_dir + '/' + self.package_name(manifest),
                        local_dir + '/../' + self.package_final_name(distro, version, manifest))

        return True


def main():

    if len(sys.argv) == 1:
        syntax()
        sys.exit(1)

    for path in sys.argv[1:]:

        pak = Packager()
        user_manifest = AddingYaml(path)

        for distro in user_manifest.dict['distro']:

            split = distro.split(':')
            if len(split) != 2:
                logger.critical(f'Incorrect "{distro}", should be <distro>:<name>')
                continue
            name = split[0]
            version = split[1]

            # complete manifest with optional missing fields
            # TODO avoid reopening path or copying user_manifest if possible
            manifest = DictObj((AddingYaml(path) + AddingYaml('mdpack/distro/' + name + '/' + name + '.yaml')).dict)

            logger.info('Processing ' + name + '-' + version)
            logger.check('\tbuilding docker image ' + name + '-' + version)
            image_tag = 'mdp-' + name + '-' + version
            if (not pak.make_docker_image(distro=name,
                                          version=version,
                                          image_tag=image_tag)):
                logger.stop_check(critical=True)
                continue
            logger.stop_check()

            logger.check('\tbuilding app and package ' + name + '-' + version)
            if (not pak.build_and_install(image_tag=image_tag, distro=name, version=version, manifest=manifest)):
                logger.stop_check(critical=True)
                continue
            logger.stop_check()


if __name__ == '__main__':
    main()
