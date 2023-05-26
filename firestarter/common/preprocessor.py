from .config_parser import Parser

import os

class PreProcessor:

    def __init__(self, data: str) -> None:
        self.data = data


    def preprocess(self, context: dict) -> str:
        parser: Parser = Parser(self.data)

        for symbol in parser.parse():
            value: str = self.resolve_symbol(symbol, context)
            parser.interpolate(symbol, value)

        return parser.data


    def resolve_symbol(self, symbol: str, context: dict) -> str:
        var_context, var_name = symbol.split(".")

        if var_context == "vars":
            return self.resolve_var(var_name, context)

        elif var_context == "env":
            return self.resolve_env(var_name, context)

        elif var_context == "secrets":
            return self.resolve_secret(var_name, context)

        else:
            raise ValueError(f"Unknown context {context} for symbol {symbol}")


    def resolve_var(self, var_name: str, context: dict) -> str:
        return context["resolve_var"](var_name)

    def resolve_env(self, var_name: str, context: dict) -> str:
        if not var_name in os.environ:
            raise ValueError(f'{var_name} not found in environment')

        return os.environ[var_name]


    def resolve_secret(self, var_name: str, context: dict) -> str:
        return context["resolve_secret"](var_name)

