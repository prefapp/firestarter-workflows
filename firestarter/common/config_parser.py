import re
import os


class Parser:

    REGEX: re.Pattern = re.compile(r"\$\{\{\s*([^}\s]+)\s*\}\}")

    def __init__(self, data):
        self.data = data

    def parse(self):
        for symbol in REGEX.findall(self.data):
            yield symbol

    def interpolate(self, symbol, value):
        reSub = re.compile("\$\{\{\s*" + symbol + "\s*\}\}")
        self.data = reSub.sub(value, self.data)


# with open("./a.yaml", "r") as file:

#     data = file.read()

#     parser = Parser(data)

#     for symbol in parser.parse():

#         value = symbol.replace("foo", "lol")

#         # logica de resolucion de symbolo
#         parser.interpolate(symbol, value)

#     print (parser.data)

    # _env_dict: dict
    # _vars_dict: dict
    # _secrets_dict: dict

    # def __init__(self, path: str):
    #     _env_dict = _get_env_dict()
    #     _vars_dict = _get_vars_dict(path)
    #     _secrets_dict = _get_secrets_dict(path)


    # def _get_env_dict() -> dict:
    #     return os.environ

    # def _get_vars_dict():
    #     pass

    # def _get_secrets_dict():
    #     pass

    # def parse_vars(task_manager_vars: dict) -> dict:
    #     CONTEXT_PATTERN: re.Pattern = re.compile(r"\$\{\{.*\}\}")
    #     var_dict: dict = {}

    #     def parse_var_value(value: str) -> str:
    #         if not CONTEXT_PATTERN.match(value):
    #             return value

    #         value = value.replace("${{", "").replace("}}", "")
    #         context, var = map(str.strip, value.split("."))  # Trims both values

    #         if context == "env":
    #             return os.environ[var]
    #         elif context == "vars":
    #             return var_dict[var]
    #         elif context == "secrets":
    #             return ""
    #         else:
    #             raise ValueError("Variable context unknown (incorrect placeholder)")

    #     for name, value in task_manager_vars.items():
    #         var_dict[name] = parse_var_value(value)

    #     return var_dict
