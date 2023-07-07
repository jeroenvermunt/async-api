from typing import Union
import jinja2
import re
from importlib import resources


def _create_method(
    method_name: str,
    parameters: Union[dict, str],
    template: jinja2.Template
):

    # convert string to dict if necessary, defaults to get method later
    if isinstance(parameters, str):
        parameters = {'endpoint': parameters}

    # extract arguments from endpoint
    arguments = re.findall(r'\{(.+?)\}', parameters['endpoint'])

    code_string = template.render(
        http_method=parameters.get('method', 'get'),
        method_name=method_name,
        endpoint=parameters['endpoint'],
        arguments=arguments
    )

    return code_string


class ApiMetaclass(type):

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # default to empty headers if not specified
        cls.headers = namespace.get('headers', {})

        # default to empty base_url if not specified
        cls.base_url = namespace.get('base_url', '')

        cls.return_type = namespace.get('return_type', None)
        cls.verbose = namespace.get('verbose', True)

        # set up jinja environment for code generation
        environment = jinja2.Environment()

        # load template for http method from template.txt
        with resources.open_text('pysdk', 'method_template.txt') as f:
            http_template = environment.from_string(f.read())

        # generate method code for each endpoint
        for name, endpoint in namespace.get('endpoints', {}).items():
            code_string = _create_method(name, endpoint, http_template)

            # execute code string in namespace
            exec(code_string, globals(), namespace)

            # add method to class
            setattr(cls, name, namespace[name])

        return cls

    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)
