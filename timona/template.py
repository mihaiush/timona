import subprocess
import shlex
import os
import sys
import re


class Template():

    def __init__(self, config):
        self.cmd = None
        if 'command' in config:
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
        if self.cmd:
            p = subprocess.run(
                shlex.split(self.cmd),
                input=tpl, env={**env, **os.environ},
                capture_output=True, check=True, text=True,
            )
            if p.stderr.strip():
                if self.stderr == 'print':
                    print(p.stderr, file=sys.stderr)
                elif self.stderr == 'error':
                    raise RuntimeError('Render error:\n{}'.format(p.stderr))
            return p.stdout
