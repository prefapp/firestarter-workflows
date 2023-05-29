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

        if var_context not in context.keys():
            raise ValueError(f"Unknown context {context} for symbol {symbol}")

        return f'"{context[var_context](var_name)}"'

