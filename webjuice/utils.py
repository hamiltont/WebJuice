import os
import errno
import yaml
import threading
import sys
import atexit
import json
import subprocess
import logging
import atexit

import webjuice

import docker

from os.path import dirname,join,abspath
from urllib2 import urlopen

import socket
import platform
import stat

from docker.utils import kwargs_from_env

from requests.exceptions import ConnectionError

log = logging.getLogger(__name__)

def which(program):
  '''Checks if executable exists and is on the path. 
  Thanks http://stackoverflow.com/a/377028/119592 '''
  def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

  fpath, fname = os.path.split(program)
  if fpath:
    if is_exe(program):
      return program
  else:
    for path in os.environ["PATH"].split(os.pathsep):
      path = path.strip('"')
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file

  return None

def terminate_docker_machine(machine):
  log.info("Terminating docker-machine webjuice")
  subprocess.call([machine, 'rm', 'webjuice'])

def get_docker_machine():
  '''Gets the full path to docker-machine binary, downloading binary if necessary'''
  m_path = abspath(join(dirname(webjuice.__file__),'bin','docker-machine'))
  if which('docker-machine'):
    log.info("Found docker-machine on PATH")
    return which('docker-machine')
  elif which(m_path):
    log.info("Found docker-machine in custom location")
    return m_path

  log.warn("Did not find docker-machine on PATH, downloading...")
  system = platform.system().lower()
  arch = platform.machine().lower()
  if system == "darwin" and (arch == "x86_64" or arch == "amd64"):
    url = "https://github.com/docker/machine/releases/download/v0.2.0/docker-machine_darwin-amd64"
  elif system == "linux" and (arch == "x86_64" or arch == "amd64"):
    url = "https://github.com/docker/machine/releases/download/v0.2.0/docker-machine_linux-amd64"
  elif system == "linux" and arch == "i386":
    url = "https://github.com/docker/machine/releases/download/v0.2.0/docker-machine_linux-386"
  elif system == "windows" and (arch == "x86_64" or arch == "amd64"):
    url = "https://github.com/docker/machine/releases/download/v0.2.0/docker-machine_windows-amd64.exe"
  elif system == "windows" and arch == "i386":
    url = "https://github.com/docker/machine/releases/download/v0.2.0/docker-machine_windows-386.exe"
  else:
    log.critical("Unable to download docker-machine for system %s %s", system, arch)
    raise EnvironmentError('Unable to download docker-machine for system %s %s' % (system, arch))

  # Ensure binary directory exists
  try:
    os.makedirs(dirname(m_path))
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      raise
  
  # Download to binary directory and chmod +x
  try:
    log.info("Downloading docker-machine from %s", url)
    f = urlopen(url)
    
    with open(m_path, "wb") as local_file:
      local_file.write(f.read())
    os.chmod(m_path, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return m_path
  except OSError:
    log.exception("Unable to download docker-machine and make executable") 
  except Exception:
    log.exception("Unable to download docker-machine for %s %s from %s", system, arch, url)

  raise EnvironmentError('Unable to download docker-machine from %s' % url)

def setup_docker_host():
  '''Uses docker-machine to setup a host that can run Docker and fills current 
  os.environ with variables from `docker-machine env`, which normally include
  `DOCKER_HOST`, `DOCKER_CERT_PATH`, and `DOCKER_TLS_VERIFY`

  Searches for environment variables starting with `DM_` and passes them as 
  command line flags to docker-machine create. This allows using any flag. 
  Example: `DM_DRIVER=digitalocean` and `DM_DIGITALOCEAN_ACCESS_TOKEN=...`
  is equvalent to calling

  `docker-machine create --driver digitalocean --digitalocean-access-token ...`
   '''
  machine = get_docker_machine()

  # Check if there is an active machine and we can get the
  # environment from it
  retcode = subprocess.call([machine, 'env'], stdout=open(os.devnull, 'w'), 
    stderr=subprocess.STDOUT)
  
  # Do we need to create a new machine? 
  if retcode != 0:
    flags = [machine, 'create']
    
    # Ensure there is a driver
    if 'DM_DRIVER' not in os.environ.keys():
      flags.append('--driver')
      flags.append('virtualbox')
    
    # Setup any passed flags
    for key,value in os.environ.iteritems():
      if key.startswith('DM_'):
        flag = key[3:].lower().replace('_','-')
        flags.append('--' + flag)
        if value != "":
          flags.append(value)

    # Give the machine a name
    flags.append('webjuice')
    log.info("Creating docker machine using '%s'", " ".join(flags))
    output = subprocess.check_output(flags)
    for line in output.split('\n'): 
      log.info(line)

    # Ensure the machine is started (some drivers separate create from start)
    log.info("Starting machine")
    output = subprocess.check_output([machine,'start','webjuice'])
    for line in output.split('\n'): 
      log.info(line)

    # Ensure there is now an active machine we can get env from
    if 0 != subprocess.call([machine, 'env'], 
      stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT):
      raise EnvironmentError("Failed to construct docker machine")

    # Setup exit handler so we are not massively billed
    # Automatically exit if we are not using a virtual machine and 
    # there is no environment key telling us to persist the host
    if 'virtualbox' not in flags and 'WJ_PERSIST_DOCKERHOST' not in os.environ.keys():
      log.info("Registering docker-machine cleanup handler")
      atexit.register(terminate_docker_machine, machine)

  # Machine exists, load all environment variables
  # TODO: Once docker/machine#1041 is closed, use 'docker-machine inspect' 
  #       instead of this hack
  output = subprocess.check_output([machine,'env','webjuice'])
  for line in output.split('\n'): 
    if line.startswith('export'): 
      k,v=line[len('export '):].split('=')
      os.environ[k] = v.strip('"')
      log.debug("Adding environment from docker-machine (%s=%s)", k, v.strip('"'))

def get_docker():
  '''Connect to docker daemon. Create host using docker-machine if needed. 
  Returns 2-tuple with `(host_ip, docker_client)` of type `(<str>, <docker.Client>)`
  Raises `EnvironmentError` if unable to establish connection to docker host
  '''

  # Ensure a docker host is created and we can connect to it
  setup_docker_host()
  client = docker.Client(**kwargs_from_env(assert_hostname=False))

  # Warn about insecure docker usage
  if os.environ.get('DOCKER_TLS_VERIFY') is None or os.environ.get('DOCKER_CERT_PATH') is None:
    log.warn('Insecure docker usage detected. We recommend setting DOCKER_TLS_VERIFY and DOCKER_CERT_PATH')

  # Confirm that we are actually connected
  try:
    client.info()
  except ConnectionError:
    log.exception('Unable to connect to docker, cannot use docker for running tests')
    log.exception('Check value of DOCKER_HOST, DOCKER_TLS_VERIFY, and DOCKER_CERT_PATH environment variables')
    raise EnvironmentError("Unable to connect to Docker")

  host_ip = os.environ.get('DOCKER_HOST_IP')  
  if host_ip is None:
    log.error("Environment variable DOCKER_HOST_IP is required")
    try:
      d_host = os.environ.get('DOCKER_HOST')
      log.debug("Trying to guess using %s", d_host)
      host_ip = d_host.split('//')[1].split(':')[0]
      log.debug("Guessed %s, ensuring we can connect", host_ip)
      
      # Ask if this is a valid IPv4
      socket.inet_pton(socket.AF_INET, host_ip)

      log.warn("Guessing DOCKER_HOST_IP=%s by parsing DOCKER_HOST=%s", host_ip, d_host)
    except (IndexError, socket.error) as e:
      log.exception("Unable to guess DOCKER_HOST_IP, cannot use docker for running tests")
      raise EnvironmentError("Unable to connect to Docker")

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
