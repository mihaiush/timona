from timona import config

# /tmp/c.yaml
CFG = """
foo: bar
"""

# /tmp/c2.yaml
CFGC = """
#+/tmp/c.yaml
alpha: beta
foo: bozo
"""

# /tmp/c2.yaml
CFGY = """
include: [/tmp/c.yaml]
alpha: beta
foo: bozo
"""

# /tmp/c2.yaml
CFG2 = """
kama: sutra
"""

# /tmp/c3.yaml
CFGM = """
#+/tmp/c.yaml
alpha: beta
foo: bozo
include: [/tmp/c2.yaml]
"""


def test_load_config_file():
    with open('/tmp/c.yaml', 'w') as f:
        f.write(CFG)
    cfg = config.load_config_file('/tmp/c.yaml').strip()
    assert cfg == 'foo: bar'


def test_load_config_file_with_include():
    with open('/tmp/c.yaml', 'w') as f:
        f.write(CFG)
    with open('/tmp/c2.yaml', 'w') as f:
        f.write(CFGC)
    cfg = config.load_config_file('/tmp/c2.yaml').strip()
    assert cfg == 'foo: bar\nalpha: beta\nfoo: bozo'


def test_load_config():
    with open('/tmp/c.yaml', 'w') as f:
        f.write(CFG)
    cfg = config.load_config('/tmp/c.yaml')
    assert '.hash' in cfg
    del(cfg['.hash'])
    assert cfg == {'foo': 'bar'}


def test_load_config_with_file_include():
    with open('/tmp/c.yaml', 'w') as f:
        f.write(CFG)
    with open('/tmp/c2.yaml', 'w') as f:
        f.write(CFGC)
    cfg = config.load_config('/tmp/c2.yaml')
    assert '.hash' in cfg
    del(cfg['.hash'])
    assert cfg == {'alpha': 'beta', 'foo': 'bozo'}


def test_load_config_with_yaml_include():
    with open('/tmp/c.yaml', 'w') as f:
        f.write(CFG)
    with open('/tmp/c2.yaml', 'w') as f:
        f.write(CFGY)
    cfg = config.load_config('/tmp/c2.yaml')
    assert '.hash' in cfg
    del(cfg['.hash'])
    assert cfg == {'alpha': 'beta', 'foo': 'bozo'}


def test_load_config_mixt():
    with open('/tmp/c.yaml', 'w') as f:
        f.write(CFG)
    with open('/tmp/c2.yaml', 'w') as f:
        f.write(CFG2)
    with open('/tmp/c3.yaml', 'w') as f:
        f.write(CFGM)
    cfg = config.load_config('/tmp/c3.yaml')
    assert '.hash' in cfg
    del(cfg['.hash'])
    assert cfg == {'alpha': 'beta', 'foo': 'bozo', 'kama': 'sutra'}
