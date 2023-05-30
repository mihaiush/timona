from timona import template
import re
import pytest
import subprocess

CONFIG_CMD = {
    'command': {
        'render': 'esh -s /bin/bash -',
        'version': 'esh -V'
    }
}

CONFIG_MOD = {
    'module': 'jinja2'
}


def test_template_init_simple():
    t = template.Template(CONFIG_CMD, '/tmp')
    assert type(t.version) is str


def test_template_init_regex():
    c = dict(CONFIG_CMD)
    c['regex'] = r'\${?[a-zA-Z_][a-zA-Z0-9_]*}?'
    t = template.Template(c, '/tmp')
    assert type(t.var_re) is re.Pattern


def test_template_render():
    t = template.Template(CONFIG_CMD, '/tmp')
    assert t.render('<%= $FOO -%>', {'FOO': 'bar'}) == 'bar'


def test_template_render_error():
    t = template.Template(CONFIG_CMD, '/tmp')
    with pytest.raises(subprocess.SubprocessError):
        t.render('<% false %>', {})


def test_template_render_stderr_suppress(capsys):
    t = template.Template(CONFIG_CMD, '/tmp')
    t.render('<% sh -c "echo foo >&2" %>', {})
    captured = capsys.readouterr()
    assert captured.err == ''


def test_template_render_stderr_print(capsys):
    c = dict(CONFIG_CMD)
    c['command']['stderr'] = 'print'
    t = template.Template(c, '/tmp')
    t.render('<% sh -c "echo foo >&2" %>', {})
    captured = capsys.readouterr()
    assert captured.err.strip() == 'foo'


def test_template_render_stderr_error():
    c = {**CONFIG_CMD}
    c['command']['stderr'] = 'error'
    t = template.Template(c, '/tmp')
    with pytest.raises(subprocess.SubprocessError, match='Render error'):
        t.render('<% sh -c "echo foo >&2" %>', {})


def test_template_module_version():
    t = template.Template(CONFIG_MOD, '/tmp')
    assert t.version.startswith('module: jinja2')


def test_template_module_render():
    t = template.Template(CONFIG_MOD, '/tmp')
    assert t.render('{{ FOO }}', {'FOO': 'bar'}) == 'bar'
