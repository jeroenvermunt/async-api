import logging
import re
import sys
from importlib import resources
from typing import Union

import jinja2
import pydantic_core
from pydantic import BaseModel

MODEL_IMPORTS = []
MODEL_IMPORTS_2 = (
    []
)  # this is not used, but might be useful later for generation of a file


META_LOGGER = logging.getLogger("ApiMetaclass")


def _parse_base_model(model: BaseModel) -> dict[str, str]:
    """
    Parse a pydantic model to a dictionary of its fields and types

    Args:
        model (BaseModel): pydantic model to be parsed

    Returns:
        required_fields (dict): dictionary of the required fields of the model
    """

    # get fields of model
    fields = model.model_fields

    required_fields = {}

    for field_name, field_info in fields.items():
        # the field is required if it has the default value of PydanticUndefinedType
        if (
            field_info.default
            and type(field_info.default)
            is pydantic_core._pydantic_core.PydanticUndefinedType
        ):
            required_fields[field_name] = field_info.annotation.__name__

    return required_fields


def _parse_body(body: dict, body_jinja_template: jinja2.Template) -> tuple[list, dict]:
    """_summary_

    Args:
        body (dict): configuration of the body of the request
        body_jinja_template (jinja2.Template): jinja2 template for the body

    Returns:
        body_dict_template (list): list of dictionaries with the configuration of the body
        body_parameters (dict): dictionary of the parameters of the body
    """

    body_dict_template = []
    body_parameters = {}

    for k, v in body.items():
        match type(v).__name__:
            # if the value is a pydantic model, parse it to find its fields
            case "ModelMetaclass":
                # add model to list of imports
                MODEL_IMPORTS.append(v.__name__)
                # MODEL_IMPORTS_2.append((v._classline_, v._thisline_))

                parameters = _parse_base_model(v)
                body_parameters.update(parameters)

                template = {
                    "key": k,
                    "type": "model",
                    "model": v.__name__,
                    "parameters": [k for k in parameters.keys()],
                }

                body_dict_template.append(template)

            # if the value is a string, parse it to find its parameters or
            # use it as a default value
            case "str":
                # parse string to find parameter
                if v[0] == "{" and v[-1] == "}":
                    body_parameters[v[1:-1]] = "str"

                    template = {"key": k, "type": "parameter", "value": v[1:-1]}

                # use string as default value
                else:
                    template = {
                        "key": k,
                        "type": "default",
                        "python_type": type(v).__name__,
                        "value": v,
                    }

                body_dict_template.append(template)

            # if the value is a dictionary, parse it recursively
            case "dict":
                template, parameters = _parse_body(v, body_jinja_template)

                # pre-render the body string
                body_string = body_jinja_template.render(body_template=template)

                template = {
                    "key": k,
                    "type": "dict",
                    "value": body_string,
                }

                body_dict_template.append(template)
                body_parameters.update(parameters)

    return body_dict_template, body_parameters


def _create_method(
    name: str, config: Union[dict, str], environment: jinja2.Environment
):
    """
    TODO: Check if method exists in namespace, if not generate code for method

    """

    # load template for http method from template.jinja
    with resources.open_text("pysdk", "method_template.jinja") as f:
        http_template = environment.from_string(f.read())

    with resources.open_text("pysdk", "body_template.jinja") as f:
        body_jinja_template = environment.from_string(f.read())

    # if only a string is passed, transform it into a dictionary
    if isinstance(config, str):
        config = {"endpoint": config}

    # extract arguments from endpoint query parameters
    query_parameters = re.findall(r"\{(.+?)\}", config["endpoint"])
    query_parameters = set(query_parameters)

    body = config.get("body", None)

    if body:
        body_template, body_parameters = _parse_body(body, body_jinja_template)
        body_string = body_jinja_template.render(body_template=body_template)

    else:
        body_string = None
        body_parameters = {}

    code_string = http_template.render(
        http_method=config.get("method", "get"),
        method_name=name,
        endpoint=config["endpoint"],
        query_parameters=query_parameters,
        body_parameters=body_parameters.keys(),
        body=body_string,
    )

    return code_string


def _build_methods(cls, namespace):
    # set up jinja environment for code generation
    environment = jinja2.Environment()

    # store code to be executed in namespace
    code_strings = {}

    # generate method code for each endpoint
    for name, endpoint in namespace.get("endpoints", {}).items():
        code_strings[name] = _create_method(name, endpoint, environment)

    # if metaclasses are detected, we need to import them into the namespace
    if MODEL_IMPORTS:
        # load template for import statement from import_template.jinja
        with resources.open_text("pysdk", "import_template.jinja") as f:
            import_template = environment.from_string(f.read())

        # generate import statement
        cwd = sys.path[0]
        running_file = sys.argv[0]

        relative_import = (
            running_file.replace(cwd, "")
            .replace(".py", "")
            .replace("/", ".")
            .strip(".")
        )

        if " " in relative_import:
            raise ValueError("Spaces in path are not supported")

        import_statement = import_template.render(
            imports=[
                {"relative_import": relative_import, "model": model}
                for model in MODEL_IMPORTS
            ]
        )

        # execute import statement in namespace
        exec(import_statement, globals(), namespace)

    for name, code_string in code_strings.items():
        # if cls.verbose:
        #     print(code_string)

        # include the MODELS_IMPORTS models into the global namespace
        global_namespace = globals()

        for model in MODEL_IMPORTS:
            global_namespace[model] = namespace[model]

        # execute code string in namespace with the imported models
        exec(code_string, global_namespace, namespace)

        # add method to class
        setattr(cls, name, namespace[name])

        META_LOGGER.debug(f"Method {name} added to class")

    return cls


class ApiMetaclass(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        cls.authorization = namespace.get("authorization", None)

        # default to empty headers if not specified
        cls.headers = namespace.get("headers", {})
        print(f"Headers: {cls.headers}")

        if cls.authorization:
            cls.headers["Authorization"] = cls.authorization

        # default to empty base_url if not specified
        cls.base_url = namespace.get("base_url", "")

        cls.return_type = namespace.get("return_type", None)
        cls.verbose = namespace.get("verbose", True)
        cls.log_level = namespace.get("log_level", None)

        if cls.verbose and not cls.log_level:
            cls.log_level = "INFO"

        if cls.log_level:
            # get current log level
            current_log_level = logging.getLogger().getEffectiveLevel()
            logging.basicConfig(level=cls.log_level)

        # build methods and run in namespace if build is True
        if namespace.get("build", True):
            cls = _build_methods(cls, namespace)

        if cls.log_level:
            # reset log level to default
            logging.basicConfig(level=current_log_level)

        return cls

    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)
