import subprocess
import shlex


class Helm():

    def __init__(self, config, tpl, tmp):
        self.cmd = '{} {}'.format(config['command'], config['flags'])
        if 'wait' in config and config['wait']:
            self.atomic = '--atomic'
            self.wait = '--wait'
        else:
            self.atomic = ''
            self.wait = ''
        if 'timeout' in config:
            self.timeout = '--timeout {}'.format(config['timeout'])
        else:
            self.timeout = ''
        self.tpl = tpl
        self.tmp = tmp
        self.values = 'v.yaml'

        v = '{} version --short'.format(config['command'])
        v = subprocess.run(
            shlex.split(v),
            check=True, text=True, capture_output=True
        )
        self.version = v.stdout.strip()
        v = '{} diff version'.format(config['command'])
        v = subprocess.run(
            shlex.split(v),
            check=True, text=True, capture_output=True
        )
        self.version_diff = v.stdout.strip()

    def _render_v(self, env, values):
        with open(values, 'r') as f:
            v = self.tpl.render(f.read(), env)
        with open('{}/{}'.format(self.tmp, self.values), 'w') as f:
            f.write(v)

    def _run(self, env, args, hide_stdout=False):
        c = self.tpl.render(self.cmd, env).strip()
        c = '{} {}'.format(c, args)
        if hide_stdout:
            stdout = subprocess.DEVNULL
        else:
            stdout = None
        subprocess.run(shlex.split(c), check=True, text=True, stdout=stdout)

    def template(self, release, env, values):
        self._render_v(env, values)
        self._run(
            env,
            'template -f {}/{} {} .'
            .format(self.tmp, self.values, release)
        )

    def debug(self, release, env, values):
        self._render_v(env, values)
        self._run(
            env,
            'upgrade -i --debug --dry-run -f {}/{} {} .'
            .format(self.tmp, self.values, release)
        )

    def diff(self, release, env, values):
        self._render_v(env, values)
        self._run(
            env,
            'diff upgrade -f {}/{} {} .'
            .format(self.tmp, self.values, release)
        )

    def deploy(self, release, env, values):
        self._render_v(env, values)
        self._run(
            env,
            'upgrade --debug -i -f {}/{} {} {} {} .'
            .format(self.tmp,
                    self.values,
                    self.atomic,
                    self.timeout,
                    release),
            True
        )

    def status(self, release, env):
        self._run(
            env,
            'list -f "^{}$"'.format(release)
        )

    def delete(self, release, env):
        self._run(
            env,
            'uninstall --debug {} {} {}'
            .format(self.wait, self.timeout, release),
            True
        )
