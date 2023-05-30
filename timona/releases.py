#!/usr/bin/env python3

import yaml
from threading import Thread
from pprint import pformat
import os
import itertools


def flatten_matrix(matrix):
    flat_matrix = []
    item_list = []
    for var_name, var_value_list in matrix.items():
        if type(var_value_list) is not list:
            var_value_list = [var_value_list]
        item = []
        for var_value in var_value_list:
            item.append([var_name, var_value])
        item_list.append(item)
    for item in list(itertools.product(*item_list)):
        flat_item = {}
        for (var_name, var_value) in item:
            flat_item[var_name] = var_value
        flat_matrix.append(flat_item)
    return flat_matrix


# Count the variables in a release
def count_vars(data, tpl):
    c = 0
    for var_name, var_value in data.items():
        if var_name != '__count__':
            if tpl.var_re:
                c = c + len(tpl.var_re.findall(var_value))
            else:
                for k in data.keys():
                    c = c + var_value.count(k)
    if c == 0 and not tpl.var_re:
        for var_name, var_value in data.items():
            if var_name != '__count__':
                try:
                    tpl.render(var_value, {})
                except Exception:
                    c = 999
                    break
    return c


def solve_vars(in_data, out_data, tpl):
    in_data['__count__'] = count_vars(in_data, tpl)
    while in_data['__count__'] > 0:
        tmp_data = {'__count__': 0}
        c = in_data['__count__']
        del(in_data['__count__'])
        err = None
        for var_name, var_value in in_data.items():
            try:
                tmp_data[var_name] = tpl.render(var_value, in_data).strip()
            except Exception as e:
                err = e
                tmp_data[var_name] = var_value
        tmp_data['__count__'] = count_vars(tmp_data, tpl)
        if c == tmp_data['__count__']:
            out_data['e']['last'] = in_data
            out_data['e']['err'] = err
            out_data['e']['count'] = c
            return
        in_data = tmp_data
    out_data['d'] = dict(in_data)


def get_releases(tpl, tmp, config):
    cache = '{}/releases.{}.yaml'.format(tmp, config['.hash'])
    if os.path.isfile(cache):
        with open(cache, 'r') as f:
            out = yaml.safe_load(f.read())
    else:
        # Flatten releases
        out = []
        for release_name, data in config['releases'].items():
            release_template = {'__name__': release_name}
            if 'variables' in config:
                for var_name, var_value in config['variables'].items():
                    release_template[var_name] = var_value
            if 'variables' in data:
                for var_name, var_value in data['variables'].items():
                    release_template[var_name] = var_value
            if 'matrix' in data:
                for matrix in data['matrix']:
                    flat_matrix = flatten_matrix(matrix)
                    for release_matrix in flat_matrix:
                        out.append({**release_template, **release_matrix})
            else:
                out.append(release_template)

        # Remove empty vars
        for release in out:
            to_del = []
            for var_name, var_value in release.items():
                if not var_value:
                    to_del.append(var_name)
            for var_name in to_del:
                del(release[var_name])

        # Solve vars, each release in a thread
        _releases = []
        threads = []
        for release in out:
            x = {
                't': None,    # thread
                'r': {        # solved vars release
                    'd': {},  # data
                    'e': {}   # err
                }
            }
            t = Thread(target=solve_vars,
                       args=(release, x['r'], tpl),
                       daemon=True)
            x['t'] = t
            threads.append(x)
            t.start()
        for x in threads:
            x['t'].join()
            if len(x['r']['e']) == 0:
                _releases.append(x['r']['d'])
            else:
                msg = ''
                msg = msg + 'Loop or template error\n'
                msg = msg + 'Latest data:\n'
                msg = msg + pformat(x['r']['e']['last']) + '\n'
                msg = msg + 'Error: {}\n'.format(x['r']['e']['err'])
                raise RuntimeError(msg)
        out = _releases

        # Cleanup variables staring with _
        # Check for duplicate names
        _releases = {}
        for release in out:
            n = release['__name__']
            if n not in _releases:
                to_del = []
                for k in release:
                    if k[0] == '_':
                        to_del.append(k)
                for k in to_del:
                    del(release[k])
                _releases[n] = release
            else:
                raise RuntimeError(
                    'Duplicate release name: {}\n{}\n{}'.format(
                        n, _releases[n], release)
                )
        out = _releases

        with open(cache, 'w') as f:
            f.write(yaml.safe_dump(out))

    return out
