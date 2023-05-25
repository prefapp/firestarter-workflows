from config_parser import Parser

import os
import re

RE_IS_VAR = re.compile("^var\.(\w+)$")
RE_IS_ENV = re.compile("^env\.(\w+)$")
RE_IS_SECRET = re.compile("^secret\.(\w+)$")

class PreProcessor:

    def __init__(self, data):
        self.data = data


    def preprocess(self, context):

        parser = parser(self.data)

        for symbol in parser.parse():

            value = self.resolveSymbol(symbol, context)

            parser.interpolate(symbol, value)

        return parser.data


    def resolveSymbol(self, symbol, context):

        if RE_IS_VAR.match(symbol):
            return resolveVar(symbol, context)

        elif RE_IS_ENV.match(symbol):
            return resolveEnv(symbol, context)

        elif RE_IS_SECRET.match(symbol):
            return resolveSecret(symbol, context)


    def resolveVar(self, symbol, context):
        return 'var_' + symbol

    def resolveEnv(self, symbol, context):

        if not symbol in os.environ:
            raise f'{symbol} not found in environment'
        
        return os.environ[symbol]


    def resolveSecret(self, symbol, context):

        return context.resolveSecret(symbol)
