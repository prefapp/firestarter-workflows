import re
from .config_parser import Parser


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


def interpolate_config_values(data, context: dict):
    """Interpolate parsed config values, not shell commands or YAML source."""
    def resolve_symbol(match):
        symbol = match.group(1).strip()
        var_context, separator, var_name = symbol.partition('.')
        if var_context not in context:
            raise ValueError(f"Unknown context '{var_context}' for symbol '{symbol}'")
        if not separator or not re.fullmatch(r'[A-Za-z0-9_-]+', var_name):
            raise ValueError(f"Invalid symbol '{symbol}'")
        return str(context[var_context](var_name))

    if isinstance(data, dict):
        return {key: interpolate_config_values(value, context) for key, value in data.items()}
    if isinstance(data, list):
        return [interpolate_config_values(value, context) for value in data]
    if isinstance(data, str):
        return re.sub(r'\$\{\{(.*?)\}\}', resolve_symbol, data)
    return data
