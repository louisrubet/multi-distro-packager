#!/usr/bin/env python3

# process
# 1. create distro:version image, with standard dev tools and libs
# 2. complete distro with user dependencies
# 3. build -> 1 script
# 4. install -> 1 script
# 5. package -> 1 script
# Questions
# instead of 1 file per distro:version, why not 1 file for all?

import sys
import os
import subprocess
import yaml  # pip install pyyaml
#import tempfile
import shutil

NORMAL = '\033[0;37;40m'
RED = '\033[1;31;40m'
GREEN = '\033[1;32;40m'


class Log:
    def __init__(self):
        self.check_begun = False

    def stop_check(self, critical=False):
        if self.check_begun:
            if critical:
                print(RED + 'FAILED' + NORMAL)
            else:
                print(GREEN + 'ok' + NORMAL)
        self.check_begun = False

    def critical(self, text=None):
        self.stop_check(critical=True)
        if text is not None:
            print(RED + text + NORMAL)

    def info(self, text=None):
        self.stop_check()
        if text is not None:
            print(text)

    def debug(self, text=None):
        pass
        # self.stop_check()
        # if text is not None:
        #    print(text)

    def check(self, text):
        self.stop_check()
        if text is not None:
            self.check_begun = True
            print(text + ' .. ', end='')


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

# self: attr simple / other: attr whatever type -> other is dropped
# self: attr list / other: attr simple -> other is dropped
# self: attr dict / other attr dict : other attr dict is added

class YamlObject:
    def __init__(self, yaml_path=None, in_dict=None):
        self.merge(yaml_path, in_dict)

    def merge(self, yaml_path=None, in_dict=None):
        if (yaml_path is not None):
            with open(yaml_path) as file:
                in_dict = yaml.full_load(file)
        # cf https://joelmccune.com/python-dictionary-as-object/
        if in_dict is not None:
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

    def make_image(self, distro, version, image_tag):
        # docker image
        dockerfile_path = os.path.dirname(__file__) + '/distro/' + distro
        result = subprocess.run(
            ['docker', 'build', '--build-arg', f'DISTRO={distro}', '--build-arg', f'VERSION={version}', '--tag',
             image_tag, dockerfile_path],
            stdout=subprocess.PIPE)

        logger.debug(result.stdout.decode("utf-8"))

        if (result.returncode != 0):
            logger.critical(result.stdout.decode("utf-8"))
            return False
        return True

    def build_and_install(self, image_tag, version, distro_conf, app_conf, pkg_conf):

        container_name = image_tag + '-' + pkg_conf.name
        app_dir = LocalDirectory(f'{container_name}-app')
        pkg_dir = LocalDirectory(f'{container_name}-pkg')

        if hasattr(app_conf, 'dependencies'):
            deps = LocalScript(app_dir.path + '/user_deps.sh').append(app_conf.dependencies)
            deps.close()

        app_build_conf = YamlObject('app_build/' + app_conf.build.type + '.yaml')
        build = LocalScript(app_dir.path + '/build_app.sh').append(app_build_conf.script)
        build.close()

        env = LocalScript(app_dir.path + '/env.sh')
        env.append(f'export DEB_NAME="{pkg_conf.name}"\n')
        env.append(f'export DEB_CONTROL="{pkg_conf.control}"\n')
        if hasattr(pkg_conf, 'postinst'):
            env.append(f'export DEB_POSTINST="{pkg_conf.postinst}"')
        env.close()

        pkg_build_conf = YamlObject('pkg/' + pkg_conf.type + '.yaml')
        package = LocalScript(app_dir.path + '/build_package.sh').append(pkg_build_conf.script)
        package.close()

        generate = LocalScript(app_dir.path + '/generate.sh').append(distro_conf.generate.script)
        generate.close()

        subprocess.run(['docker', 'stop', container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['docker', 'rm', container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        result = subprocess.run(
            ['docker', 'run', '-it', '--rm', '--name', container_name,
             '-v', f'{app_conf.source_path}:/source',
             '-v', f'{app_dir.path}:/app',
             '-v', f'{pkg_dir.path}:/pkg',
             image_tag, '/bin/bash', '-x', '/app/generate.sh'], stdout=subprocess.PIPE)

        logger.debug(result.stdout.decode('utf-8'))

        if (result.returncode != 0):
            logger.critical(result.stdout.decode('utf-8'))
            return False

        shutil.move(pkg_dir.path + '/' + pkg_conf.name + '.' + pkg_conf.type,
                    distro_conf.name + '-' + version + '-' + pkg_conf.name + '.' + pkg_conf.type)

        return True


def main():

    if len(sys.argv) == 1:
        syntax()
        sys.exit(1)

    for config_path in sys.argv[1:]:

        # load the configuration: user (priority) configuration is complemented by generic distro configuration
        pak = Packager()
        config = YamlObject(config_path)
        config.merge('distro/' + config.distro.name + '/distro.yaml')

        for version in config.distro.version:
            logger.info('Processing ' + config.distro.name + '-' + version)

            logger.check('\tbuilding docker image ' + config.distro.name + '-' + version)
            image_tag = 'mdel-' + config.distro.name + '-' + version
            if (not pak.make_image(distro=config.distro.name,
                                   version=version,
                                   image_tag=image_tag)):
                continue

            logger.check('\tbuilding app and package ' + config.distro.name + '-' + version)
            if (not pak.build_and_install(image_tag=image_tag,
                                          version=version,
                                          distro_conf=config.distro,
                                          app_conf=config.app,
                                          pkg_conf=config.pkg)):
                continue
            logger.info()


if __name__ == '__main__':
    main()
