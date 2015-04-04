import os
import yaml
import threading
import sys
import atexit

def parse_log_config(path='logging.yaml'):
  """Returns a dictionary that can be passed
  to logging.config.dictConfig
  """
  assert os.path.exists(path)

  config = {}
  with open(path, 'rt') as f:
    config = yaml.load(f.read())
  
  return config

def start_container(client, *args, **kwargs):
  def container_cleanup(client, cid):
    print "Stopping container %s" % cid
    # client.stop(cid)
    client.kill(cid)

  client.start(*args, **kwargs)
  if len(args) == 1:
    print "Detected container %s in args" % args[0]
    atexit.register(container_cleanup, client, args[0])
  else:
    print "Detected container %s in kwargs" % kwargs['container']
    atexit.register(container_cleanup, client, kwargs['container'])

def log_for_docker(generator, line_prefix='', print_empty=False):
  '''
  To get generator, use `cli.logs(container=cid, stream=True)`
  It's perfectly acceptable to use this method once for STDOUT and 
  once for STDERR

  TODO: Make this a proper stoppable thread using http://stackoverflow.com/a/325528/119592
  and add an atexit handler
  '''
  def log_docker(generator, print_empty, line_prefix):
    for line in generator:
      if print_empty or line.strip():
        sys.stdout.write(line_prefix)
        sys.stdout.write(line)
        sys.stdout.flush()
  r_log = threading.Thread(target=log_docker, args=(generator, print_empty, line_prefix))
  r_log.daemon = True
  r_log.start()
