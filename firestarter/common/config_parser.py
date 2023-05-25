import re
import os


REGEX: re.Pattern = re.compile("\$\{\{\s*([^}\s]+)\s*\}\}")

class Parser:

    def __init__(self, data):
        self.data = data

    def parse(self):
        for symbol in REGEX.findall(self.data):
            yield symbol

    def interpolate(self, symbol, value):
        reSub = re.compile("\$\{\{\s*" + symbol + "\s*\}\}")
        self.data = reSub.sub(value, self.data)

