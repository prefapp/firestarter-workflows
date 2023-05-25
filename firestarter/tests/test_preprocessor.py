
import os

def loadYaml(file):
    with open(file, 'r') as f:
        return f.read()

from firestarter.common.preprocessor import PreProcessor

def test_parser():

    pp = PreProcessor(loadYaml(os.path.join(os.path.dirname(__file__), 'fixtures/preprocess_workflow.yaml')))
    
    pp.preprocess({

        resolveSecret

    })
