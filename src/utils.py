import os
import yaml

def parse_log_config(path='logging.yaml'):
  """Returns a dictionary that can be passed
  to logging.config.dictConfig
  """
  assert os.path.exists(path)

  config = {}
  with open(path, 'rt') as f:
    config = yaml.load(f.read())
  
  return config

