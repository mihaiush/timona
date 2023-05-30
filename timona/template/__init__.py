import subprocess
import shlex
import os
import sys
import re
import importlib
import requests

class Template():

    def __init__(self, config, tmp):
        self.tmp = tmp
        self.cmd = None
        self.module = None
        if 'module' in config:
            if not config['module'].endswith('.py'):
                self.module = importlib.import_module('timona.template.module_{}'.format(config['module']))
            else:
                sys.path = [tmp] + sys.path
                if config['module'].startswith('http://') or config['module'].startswith('https://'):
                    r = requests.get(config['module'], timeout=(0.5, 5))
                    r.raise_for_status()
                    module = r.text
                else:
                    with open(config['module']) as f:
                        module = f.read()
                with open ('{}/module_template.py'.format(tmp), 'w') as f:
                    f.write(module)
                self.module = importlib.import_module('module_template')
            v = 'module: {}'.format(self.module.version)
        elif 'command' in config:
            self.cmd = config['command']['render']
            p = subprocess.run(
                shlex.split(config['command']['version']),
                capture_output=True, check=True, text=True
            )
            v = p.stdout.strip()
            v = 'command: {}'.format(v)
            self.stderr = config['command'].get('stderr')
        self.version = v
        self.var_re = config.get('regex')
        if self.var_re:
            self.var_re = re.compile(self.var_re)

    def render(self, tpl, env):
        if self.module:
            return self.module.render(tpl, env)
        elif self.cmd:
            try:
                p = subprocess.run(
                    shlex.split(self.cmd),
                    input=tpl, env={**env, **os.environ},
                    capture_output=True, check=True, text=True,
                )
            except subprocess.CalledProcessError as e:
                raise subprocess.SubprocessError(e.stderr) from e
            if p.stderr.strip():
                if self.stderr == 'print':
                    print(p.stderr, file=sys.stderr)
                elif self.stderr == 'error':
                    raise subprocess.SubprocessError(
                        'Render error:\n{}'.format(p.stderr)
                    )
            return p.stdout
