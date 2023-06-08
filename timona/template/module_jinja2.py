import jinja2

version = 'jinja2 {}'.format(jinja2.__version__)
regex = None


def render(tpl, env):
    # rise an error if tpl contains variables which are not in env
    j2env = jinja2.Environment(undefined=jinja2.StrictUndefined)

    return j2env.from_string(tpl, env).render()
