import requests
import yaml
import hashlib

CFG_FILE = 'timona.yaml'


def load_config_file(c):
    _data = []

    def _load_config(c):
        if c.startswith('http://') or c.startswith('https://'):
            r = requests.get(c)
            cfg = r.text
        else:
            with open(c) as f:
                cfg = f.read()
        for ln in cfg.split('\n'):
            ln = ln.rstrip()
            if ln.startswith('#+'):
                _load_config(ln[2:])
            elif ln:
                _data.append(ln)
    _load_config(c)
    _data = '\n'.join(_data)
    return _data


def load_config(c=None):
    if c is None:
        c = CFG_FILE
    _data = {}

    def _load_config(c):
        f = load_config_file(c)
        f = yaml.safe_load(f)
        if 'include' in f:
            for g in f['include']:
                _load_config(g)
            del(f['include'])
        _data.update(f)
    _load_config(c)
    h = hashlib.sha256(
        yaml.safe_dump(_data).encode('utf-8')
    ).hexdigest()  # sha256(yaml(_data))
    _data['.hash'] = h
    return _data
