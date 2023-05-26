import re
import os


REGEX: re.Pattern = re.compile(r"\$\{\{\s*([^}\s]+)\s*\}\}")

class Parser:

    def __init__(self, data: str) -> None:
        self.data = data

    def parse(self) -> str:
        for symbol in REGEX.findall(self.data):
            yield symbol

    def interpolate(self, symbol: str, value: str) -> None:
        reSub: re.Pattern = re.compile(r"\$\{\{\s*" + symbol + r"\s*\}\}")
        self.data = reSub.sub(value, self.data)

