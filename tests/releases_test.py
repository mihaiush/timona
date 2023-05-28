from timona import releases
import pytest
import jinja2
import os
import re
from contextlib import suppress


class Template:
    var_re = re.compile('{{ *[a-zA-Z_][a-zA-Z0-9_]* *}}')

    def render(self, tpl, env):
        j2env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        return j2env.from_string(tpl, env).render()


def test_flatten_matrix():
    data = {
        'ALPHA': ['a', 'b'],
        'BETA': 'c'
    }
    assert releases.flatten_matrix(data) == [
        {'ALPHA': 'a', 'BETA': 'c'},
        {'ALPHA': 'b', 'BETA': 'c'}
    ]


def test_count_vars_simple():
    data = {
        'ALPHA': 'a',
        'BETA': '{{ ALPHA }}-{{ GAMMA }}',
        'GAMMA': 'b-{{ DELTA }}',
        'DELTA': 'x'
    }
    t = Template()
    assert releases.count_vars(data, t) == 3
    t.var_re = None
    assert releases.count_vars(data, t) == 3


def test_count_vars_err():
    data = {
        'BETA': 'x-{{ GAMMA }}-{{ DELTA }}'
    }
    t = Template()
    t.var_re = None
    assert releases.count_vars(data, t) == 999


def test_solve_vars_ok():
    in_data = {
        'ALPHA': 'a',
        'BETA': '{{ ALPHA }}-{{ GAMMA }}',
        'GAMMA': 'b-{{ DELTA }}',
        'DELTA': 'x'
    }
    in_data['__count__'] = releases.count_vars(in_data, Template())
    out_data = {'d': {}, 'e': {}}
    releases.solve_vars(in_data, out_data, Template())
    assert out_data == {
        'd': {
            'ALPHA': 'a',
            'BETA': 'a-b-x',
            'DELTA': 'x',
            'GAMMA': 'b-x',
            '__count__': 0
        },
        'e': {}
    }


def test_solve_vars_err():
    in_data = {
        'ALPHA': 'a',
        'BETA': '{{ ALPHA }}-{{ GA__A }}',
        'GAMMA': 'b-{{ DELTA }}',
        'DELTA': 'x'
    }
    t = Template()
    in_data['__count__'] = releases.count_vars(in_data, t)
    out_data = {'d': {}, 'e': {}}
    releases.solve_vars(in_data, out_data, t)
    assert ('err' in out_data['e']) and \
        (type(out_data['e']['err']) is jinja2.exceptions.UndefinedError)


def test_get_releases_ok():
    with suppress(Exception):
        os.remove('/tmp/releases.test.yaml')
    config = {
        '.hash': 'test',
        'variables': {
            'BETA': '{{ ALPHA }}-{{ GAMMA }}',
        },
        'releases': {
            '{{ BETA }}-x-{{ DELTA }}': {
                'variables': {
                    'GAMMA': 'y'
                },
                'matrix': [
                    {
                        'ALPHA': 'z',
                        'DELTA': ['foo', 'bar']
                    }
                ]
            }
        }
    }
    assert releases.get_releases(Template(), '/tmp', config) == {
        'z-y-x-bar': {
            'ALPHA': 'z', 'BETA': 'z-y', 'DELTA': 'bar', 'GAMMA': 'y'
        },
        'z-y-x-foo': {
            'ALPHA': 'z', 'BETA': 'z-y', 'DELTA': 'foo', 'GAMMA': 'y'
        }
    }


def test_get_releases_loop():
    with suppress(Exception):
        os.remove('/tmp/releases.test.yaml')
    config = {
        '.hash': 'test',
        'releases': {
            'ALPHA': {
                'variables': {
                    'BETA': 'x-{{ GAMMA }}',
                    'GAMMA': 'y-{{ BETA }}'
                },
            }
        }
    }
    with pytest.raises(RuntimeError, match='Loop or template error'):
        releases.get_releases(Template(), '/tmp', config)


def test_get_releases_err():
    with suppress(Exception):
        os.remove('/tmp/releases.test.yaml')
    config = {
        '.hash': 'test',
        'releases': {
            'ALPHA': {
                'variables': {
                    'BETA': 'x-{{ GAMMA }}-{{ DELTA }}',
                }
            }
        }
    }
    with pytest.raises(RuntimeError, match='Loop or template error'):
        releases.get_releases(Template(), '/tmp', config)


def test_get_releases_duplicate():
    with suppress(Exception):
        os.remove('/tmp/releases.test.yaml')
    config = {
        '.hash': 'test',
        'releases': {
            'foo-{{ BAR }}': {
                'matrix': [{
                    'BAR': [
                        'alpha',
                        'alpha'
                    ]
                }]
            }
        }
    }
    with pytest.raises(RuntimeError, match='Duplicate'):
        releases.get_releases(Template(), '/tmp', config)
