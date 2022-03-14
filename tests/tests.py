#!/usr/bin/env python3

import sys
import subprocess
# import tempfile
import yaml

NORMAL = '\033[0;37;40m'
RED = '\033[1;31;40m'
GREEN = '\033[1;32;40m'


def default_manifest():
    with open('tests/default_manifest.yaml') as file:
        return yaml.full_load(file)


def app_source_dir(path):
    return {
        'type': 'dir',
        'path': path
    }


def app_source_dir(path):
    return {
        'type': 'dir',
        'path': path
    }


def app_source_archive(url=None, path=None):
    dic = {
        'type': 'archive'
    }
    if url is not None:
        dic.update({'url': url})
    if path is not None:
        dic.update({'path': path})
    return dic


def app_source_git(url=None, path=None, tag=None, commit=None):
    dic = {
        'type': 'git'
    }
    if url is not None:
        dic.update({'url': url})
    if path is not None:
        dic.update({'path': path})
    if tag is not None:
        dic.update({'tag': tag})
    if commit is not None:
        dic.update({'commit': commit})
    return dic


def build_custom(script):
    return {'type': 'custom', 'script': script}


def generate_yaml(dat):
    # file = tempfile.NamedTemporaryFile(mode='w+')
    with open('test_manifest.yaml', 'w+') as file:
        yaml.dump(dat, file, allow_unicode=True, default_flow_style=False)
        file.close()
        return file.name


def test_app_source_dir():
    dat = default_manifest()
    dat['app']['source'] = app_source_dir('/home/louis/Development/rpn')
    dat['build'] = build_custom('ls -l\n')
    test_path = generate_yaml(dat)
    return subprocess.run(['./deliver.py', './'+test_path], stdout=subprocess.PIPE)


def main():

    # app source dir
    print('test_app_source_dir .. ', end='')
    sys.stdout.flush()
    if (test_app_source_dir() == 0):
        print(GREEN + 'ok' + NORMAL)
    else:
        print(RED + 'failed' + NORMAL)


if __name__ == '__main__':
    main()
