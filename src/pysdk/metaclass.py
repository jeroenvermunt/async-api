from typing import Union
import jinja2
import re
from importlib import resources


# def _parse_body(body: dict):

#     # regex for matching arguments in string
#     argument_regex = '\{(.+?)\}'

#     for k, v in body.items():

#         match v:

#             # matches pydantic attribute with default value
#             case type(v).__name__ == 'property':
#                 pass

#             # matches pydantic attribute without default value
#             case type(v).__name__ == 'property':
#                 pass

#             # matches pydantic model
#             case type(v).__name__ == 'type':
#                 # nested pydantic model
#                 pass

#             # matches string with regex
            
#             # matches string without regex


def _create_method(
    method_name: str,
    method_parameters: Union[dict, str],
    template: jinja2.Template
):

    # convert string to dict if necessary, defaults to get method later
    if isinstance(method_parameters, str):
        method_parameters = {'endpoint': method_parameters}

    # extract arguments from endpoint
    query_parameters = re.findall(r'\{(.+?)\}', method_parameters['endpoint'])
    query_parameters = set(query_parameters)

    body = method_parameters.get('body', None)

    code_string = template.render(
        http_method=method_parameters.get('method', 'get'),
        method_name=method_name,
        endpoint=method_parameters['endpoint'],
        query_parameters=query_parameters
    )

    return code_string


class ApiMetaclass(type):

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        cls.authorization = namespace.get('authorization', None)

        # default to empty headers if not specified
        cls.headers = namespace.get('headers', {})

        if cls.authorization:
            cls.headers['Authorization'] = cls.authorization

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
            
            print(code_string)

            # add method to class
            setattr(cls, name, namespace[name])

        return cls

    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)

