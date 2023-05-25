from .config_parser import Parser

import os
import re

RE_IS_VAR = re.compile("^var\.(\w+)$")
RE_IS_ENV = re.compile("^env\.(\w+)$")
RE_IS_SECRET = re.compile("^secret\.(\w+)$")

class PreProcessor:

    def __init__(self, data):
        self.data = data


    def preprocess(self, context):
        parser = Parser(self.data)

        for symbol in parser.parse():
            value = self.resolveSymbol(symbol, context)
            parser.interpolate(symbol, value)

        return parser.data


    def resolveSymbol(self, symbol, context):
        if RE_IS_VAR.match(symbol):
            return self.resolveVar(symbol, context)

        elif RE_IS_ENV.match(symbol):
            return self.resolveEnv(symbol, context)

        elif RE_IS_SECRET.match(symbol):
            return self.resolveSecret(symbol, context)


    def resolveVar(self, symbol, context):
        return context["resolveVar"](symbol)

    def resolveEnv(self, symbol, context):
        var_name: str = symbol.split(".")[1]

        if not var_name in os.environ:
            raise ValueError(f'{symbol} not found in environment')

        return os.environ[var_name]


    def resolveSecret(self, symbol, context):
        return context["resolveSecret"](symbol)
