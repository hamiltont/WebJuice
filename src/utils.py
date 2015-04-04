import os
import yaml
import threading
import sys
import atexit
import json
import subprocess
import docker
from docker.utils import kwargs_from_env

def get_boot2docker():
  b2d = '/usr/local/bin/boot2docker '
  state = json.loads(subprocess.check_output(b2d + 'info', shell=True))['State']
  if state == 'saved' or state == 'aborted':
    print "Launching Boot2docker"
    p = subprocess.Popen(b2d + 'up', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    for line in iter(p.stdout.readline, b""):
      sys.stdout.write(line)
  elif state == 'running':
    print "Boot2docker running"

  boot = '$(%s shellinit 2>/dev/null)' % b2d
  host = subprocess.check_output(boot + ' && echo $DOCKER_HOST', shell=True)
  cert = subprocess.check_output(boot + ' && echo $DOCKER_CERT_PATH', shell=True)
  tls  = subprocess.check_output(boot + ' && echo $DOCKER_TLS_VERIFY', shell=True)
  os.environ['DOCKER_CERT_PATH'] = cert.rstrip()
  os.environ['DOCKER_HOST'] = host.rstrip()
  os.environ['DOCKER_TLS_VERIFY'] = tls.rstrip()

  client = docker.Client(**kwargs_from_env(assert_hostname=False))
  host_ip = subprocess.check_output(b2d + 'ip', shell=True).rstrip()
  return (host_ip, client)


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
