import re


class PreProcessor:
    """Resolve expressions in parsed YAML values using the supplied context."""

    def __init__(self, data) -> None:
        self.data = data

    def preprocess(self, context: dict):
        if isinstance(self.data, dict):
            return {key: PreProcessor(value).preprocess(context)
                    for key, value in self.data.items()}
        if isinstance(self.data, list):
            return [PreProcessor(value).preprocess(context) for value in self.data]
        if isinstance(self.data, str):
            return re.sub(
                r'\$\{\{(.*?)\}\}',
                lambda match: self.resolve_symbol(match.group(1).strip(), context),
                self.data,
            )
        return self.data

    def resolve_symbol(self, symbol: str, context: dict) -> str:
        var_context, separator, var_name = symbol.partition('.')
        if var_context not in context:
            raise ValueError(f"Unknown context '{var_context}' for symbol '{symbol}'")
        if not separator or not re.fullmatch(r'[A-Za-z0-9_-]+', var_name):
            raise ValueError(f"Invalid symbol '{symbol}'")
        return str(context[var_context](var_name))
