from .on_premises import OnPremises

def run(*, vars: dict, secrets: dict, config_file:str):
    on_premises = OnPremises(vars=vars, secrets=secrets, config_file=config_file)
    on_premises.execute()

__all__ = [run]
