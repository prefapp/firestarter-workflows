from firestarter.common.preprocessor import PreProcessor
import os

def load_yaml(file):
    with open(file, 'r') as f:
        return f.read()

def test_parser():
    pp = PreProcessor(load_yaml(os.path.join(
        os.path.dirname(__file__), 'fixtures/preprocess_workflow.yaml'
    )))

    pp.preprocess({
        'resolveVar': lambda v: f'VAR_{v}',
        'resolveSecret': lambda s: f'VAR_{s}',
    })
