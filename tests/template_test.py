from timona import template
import re
import pytest
import subprocess

CONFIG = {
    'command': {
        'render': 'esh -s /bin/bash -',
        'version': 'esh -V'
    }
}


def test_template_init_simple():
    t = template.Template(CONFIG)
    assert type(t.version) is str


def test_template_init_regex():
    c = dict(CONFIG)
    c['regex'] = r'\${?[a-zA-Z_][a-zA-Z0-9_]*}?'
    t = template.Template(c)
    assert type(t.var_re) is re.Pattern


def test_template_render():
    t = template.Template(CONFIG)
    assert t.render('<%= $FOO -%>', {'FOO': 'bar'}) == 'bar'


def test_template_render_error():
    t = template.Template(CONFIG)
    with pytest.raises(subprocess.SubprocessError):
        t.render('<% false %>', {})


def test_template_render_stderr_suppress(capsys):
    t = template.Template(CONFIG)
    t.render('<% sh -c "echo foo >&2" %>', {})
    captured = capsys.readouterr()
    assert captured.err == ''


def test_template_render_stderr_print(capsys):
    c = dict(CONFIG)
    c['command']['stderr'] = 'print'
    t = template.Template(c)
    t.render('<% sh -c "echo foo >&2" %>', {})
    captured = capsys.readouterr()
    assert captured.err.strip() == 'foo'


def test_template_render_stderr_error():
    c = {**CONFIG}
    c['command']['stderr'] = 'error'
    t = template.Template(c)
    with pytest.raises(subprocess.SubprocessError, match='Render error'):
        t.render('<% sh -c "echo foo >&2" %>', {})
