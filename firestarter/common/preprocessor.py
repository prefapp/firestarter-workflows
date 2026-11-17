import re
from dataclasses import dataclass
from typing import Callable

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


@dataclass(frozen=True)
class ContextPathRule:
    """Restriction on the config paths where a context may be used."""

    allowed: Callable[[tuple], bool]
    description: str


def interpolate_config_values(
    data,
    context: dict,
    allow_undefined=False,
    path='$',
    restricted_contexts: dict[str, ContextPathRule] | None = None,
):
    """Interpolate parsed config values, not shell commands or YAML source."""

    def walk(value, current_path, segments):
        def resolve_symbol(match):
            symbol = match.group(1).strip()
            var_context, separator, var_name = symbol.partition('.')
            if var_context not in context:
                raise ValueError(f"Unknown context '{var_context}' for symbol '{symbol}'")
            if not separator or not re.fullmatch(r'[A-Za-z0-9_-]+', var_name):
                raise ValueError(f"Invalid symbol '{symbol}'")

            rule = restricted_contexts.get(var_context) if restricted_contexts else None
            if rule is not None and not rule.allowed(segments):
                raise ValueError(
                    f"Context '{var_context}' is not allowed at '{current_path}'; "
                    f"it may only be used in {rule.description}"
                )

            try:
                return str(context[var_context](var_name))
            except ValueError as error:
                message = f"{error} at '{current_path}'"
                if not allow_undefined:
                    raise ValueError(message) from error
                print(f"::warning::{message}; replacing with an empty string")
                return ''

        if isinstance(value, dict):
            return {
                key: walk(item, f'{current_path}.{key}', segments + (key,))
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                walk(item, f'{current_path}[{index}]', segments + (index,))
                for index, item in enumerate(value)
            ]
        if isinstance(value, str):
            return re.sub(r'\{\{(.*?)\}\}', resolve_symbol, value)
        return value

    return walk(data, path, ())
