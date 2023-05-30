#!/usr/bin/env python3

import yaml
import sys
import os

from .__version__ import __version__ as version
from .config import load_config
from .template import Template
from .helm import Helm
from .releases import get_releases


def usage():
    print()
    print("timona COMAND [RELEASE]")
    print()
    print("COMMANDS:")
    print("  releases         - list releases")
    print("  env RELEASE      - show environment")
    print("  template RELEASE - render template")
    print("  debug RELEASE    - dry-run")
    print("  diff RELEASE     - diff between running and config")
    print("  deploy RELEASE   - deploy")
    print("  status RELEASE   - status")
    print("  delete RELEASE   - delete")
    print("  version          - show version(s)")
    print()
    sys.exit(2)


def main():
    if len(sys.argv) == 1:
        usage()
    CMD = sys.argv[1]
    valid_commands = [
        'releases',
        'env',
        'template',
        'debug',
        'diff',
        'deploy',
        'status',
        'delete',
        'version'
    ]
    if CMD not in valid_commands:
        usage()
    R = None
    if CMD != 'releases' and CMD != 'version':
        if len(sys.argv) == 2:
            usage()
        R = sys.argv[2]

    CONFIG = load_config()

    TMP = '{}/.timona'.format(CONFIG['config']['tmp'])
    os.makedirs(TMP, exist_ok=True)
    T = Template(CONFIG['config']['template'], TMP)
    H = Helm(CONFIG['config']['helm'], T, TMP)

    if CMD == 'version':
        print('timona: {}'.format(version))
        print('template: {}'.format(T.version))
        print('helm: {}'.format(H.version))
        print('helm: diff: {}'.format(H.version_diff))
        sys.exit()

    RELEASES = get_releases(T, TMP, CONFIG)
    if not RELEASES:
        sys.exit(1)

    if R and R not in RELEASES:
        raise RuntimeError('Unknown release: {}'.format(R))

    def env():
        print()
        e = {R: {'values': CONFIG['values'], 'variables': RELEASES[R]}}
        print(yaml.safe_dump(e))

    if CMD == 'releases':
        print()
        for r in RELEASES.keys():
            print('  {}'.format(r))
        print()
        sys.exit()

    if CMD == 'env':
        env()
        sys.exit()

    if CMD == 'template':
        H.template(R, RELEASES[R], CONFIG['values'])
        sys.exit()

    if CMD == 'debug':
        env()
        H.debug(R, RELEASES[R], CONFIG['values'])
        sys.exit()

    if CMD == 'diff':
        H.diff(R, RELEASES[R], CONFIG['values'])
        sys.exit()

    if CMD == 'deploy':
        H.deploy(R, RELEASES[R], CONFIG['values'])
        sys.exit()

    if CMD == 'status':
        env()
        H.status(R, RELEASES[R])
        sys.exit()

    if CMD == 'delete':
        H.delete(R, RELEASES[R])
        sys.exit()
