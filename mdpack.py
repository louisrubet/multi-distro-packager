#!/usr/bin/env python3

import sys
import os
import subprocess
import yaml  # pip install pyyaml
#import tempfile
import shutil


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
        pass

    def check(self, text):
        self.stop_check()
        self.check_begun = True
        print(text + ' .. ', end='')
        sys.stdout.flush()


logger = Log()


def syntax():
    logger.info('Syntax: deliver.py distro_config.yaml ...')


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


class YamlObject:
    def __init__(self, yaml_path=None, in_dict=None):
        self.merge(yaml_path, in_dict)

    def merge(self, yaml_path=None, in_dict=None):
        if (yaml_path is not None):
            with open(yaml_path) as file:
                in_dict = yaml.full_load(file)
        if in_dict is not None:  # cf https://joelmccune.com/python-dictionary-as-object/
            for key, val in in_dict.items():
                if (hasattr(self, key) and isinstance(val, dict)):
                    obj = YamlObject()
                    if isinstance(val, (list, tuple)):
                        setattr(obj, key, [YamlObject(in_dict=x) if isinstance(x, dict) else x for x in val])
                    else:
                        setattr(obj, key, YamlObject(in_dict=val) if isinstance(val, dict) else val)
                    for i, (k, v) in enumerate(getattr(obj, key).__dict__.items()):
                        setattr(getattr(self, key), k, v)
                else:
                    if isinstance(val, (list, tuple)):
                        setattr(self, key, [YamlObject(in_dict=x) if isinstance(x, dict) else x for x in val])
                    else:
                        setattr(self, key, YamlObject(in_dict=val) if isinstance(val, dict) else val)


class Packager:
    def __init__(self):
        pass

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

    def export_env(self, env, env_name, env_obj, env_attr):
        try:
            if hasattr(env_obj, env_attr):
                val = getattr(env_obj, env_attr)
                env.append(f'export {env_name}="{val}"\n')
        finally:
            pass

    def export_env_list(self, env, env_name, env_obj, env_attr):
        try:
            if hasattr(env_obj, env_attr):
                val_list = getattr(env_obj, env_attr)
                env.append(f'export {env_name}="')
                for val in val_list:
                    env.append(val + ' ')
                env.append('"\n')
        finally:
            pass

    def generate_env(self, dest_dir, manifest):
        env = LocalScript(dest_dir + '/env.sh')
        env.append('#!/bin/bash\n')
        self.export_env(env, 'PKG_NAME', manifest.pkg, 'name')
        self.export_env(env, 'PKG_CONTROL', manifest.pkg, 'control')
        self.export_env(env, 'PKG_POSTINST', manifest.pkg, 'postinst')
        self.export_env_list(env, 'APP_BUILD_CMAKE_OPTIONS', manifest.app.build, 'cmake_options')
        self.export_env_list(env, 'APP_DEPENDENCIES', manifest.app, 'dependencies')
        env.close()

    def generate_user_deps(self, dest_dir, manifest):
        if hasattr(manifest.app, 'dependencies'):
            shutil.copy('mdpack/distro/' + manifest.distro.name + '/install_user_deps.sh',
                        dest_dir + '/install_user_deps.sh')

    def generate_build_app(self, dest_dir, manifest):
        src_path = 'mdpack/scripts/build/' + manifest.app.build.type + '.sh'
        if (os.path.exists(src_path)):
            shutil.copy(src_path, dest_dir + '/build_app.sh')

    def generate_build_pkg(self, dest_dir, manifest):
        src_path = 'mdpack/scripts/pkg/' + manifest.pkg.type + '.sh'
        if (os.path.exists(src_path)):
            shutil.copy(src_path, dest_dir + '/build_pkg.sh')

    def generate_process_script(self, dest_dir, manifest):
        src_path = 'mdpack/distro/' + manifest.distro.name + '/generate.sh'
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

    def build_and_install(self, image_tag, version, manifest):
        container_name = image_tag + '-' + manifest.pkg.name
        local_dir = LocalDirectory(f'{container_name}').path

        # generate process scripts
        self.generate_env(local_dir, manifest)
        self.generate_user_deps(local_dir, manifest)
        self.generate_build_app(local_dir, manifest)
        self.generate_build_pkg(local_dir, manifest)
        self.generate_process_script(local_dir, manifest)

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
        shutil.move(local_dir + '/pkg/' + manifest.pkg.name + '.' + manifest.pkg.type,
                    manifest.distro.name + '-' + version + '-' + manifest.pkg.name + '.' + manifest.pkg.type)

        return True


def main():

    if len(sys.argv) == 1:
        syntax()
        sys.exit(1)

    for path in sys.argv[1:]:

        pak = Packager()
        manifest = YamlObject(path)  # user (prioritary) configuration
        manifest.merge('mdpack/distro/' + manifest.distro.name + '/' + manifest.distro.name + '.yaml')  # generic conf

        for version in manifest.distro.version:
            logger.info('Processing ' + manifest.distro.name + '-' + version)

            logger.check('\tbuilding docker image ' + manifest.distro.name + '-' + version)
            image_tag = manifest.distro.name + '-' + version
            if (not pak.make_docker_image(distro=manifest.distro.name,
                                          version=version,
                                          image_tag=image_tag)):
                logger.stop_check(critical=True)
                continue
            logger.stop_check()

            logger.check('\tbuilding app and package ' + manifest.distro.name + '-' + version)
            if (not pak.build_and_install(image_tag=image_tag, version=version, manifest=manifest)):
                logger.stop_check(critical=True)
                continue
            logger.stop_check()


if __name__ == '__main__':
    main()
