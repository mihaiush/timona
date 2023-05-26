#!/usr/bin/env python3

import yaml
from threading import Thread
import subprocess
from pprint import pprint
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
def count_vars(data, var_re):
    c = 0
    for var_name, var_value in data.items():
        if var_name != '__count__':
            if var_re:
                c = c + len(var_re.findall(var_value))
            else:
                for k in data.keys():
                    c = c + var_value.count(k)
    return c


def solve_vars(in_data, out_data, tpl):
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
        tmp_data['__count__'] = count_vars(tmp_data, tpl.var_re)
        if c == tmp_data['__count__']:
            out_data['e']['last'] = in_data
            out_data['e']['err'] = err
            return
        in_data = tmp_data
    out_data['d'] = {**in_data}


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

        # Add __count__
        _releases = []
        for release in out:
            c = {'__count__': count_vars(release, tpl.var_re)}
            _releases.append({**release, **c})
        out = _releases

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
                print('Loop or template error')
                print('Latest data:')
                pprint(x['r']['e']['last'])
                print('Error: {}'.format(x['r']['e']['err']))
                if type(x['r']['e']['err']) is subprocess.CalledProcessError:
                    print('  stderr: {}'.format(x['r']['e']['err'].stderr))
                return None
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
                    'Duplicate release name: {}\n{}\n{}'
                    .format(n, _releases[n], release)
                )
        out = _releases

        with open(cache, 'w') as f:
            f.write(yaml.safe_dump(out))

    return out
