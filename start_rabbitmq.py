'''
Helper script to launch RabbitMQ using Docker. Container will 
be terminated when this script is terminated
'''

import json
import subprocess
import sys
import os
import docker
from docker.utils import kwargs_from_env
from src.utils import log_for_docker,start_container

import signal
import time

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

def start_rabbit(port, mport):
  (host,cli) = get_boot2docker()
  container = cli.create_container(image='rabbitmq:3-management', hostname='WebJuice')
  cid = container.get('Id')
  start_container(cli, cid, port_bindings={5672: port, 15672: mport})

  print "Started RabbitMQ as %s" % container.get('Id')
  print "RabbitMQ running on port %s (Management @ %s:%s)" % (port, host, mport)
  
  log_generator = cli.logs(container=cid, stream=True)
  log_for_docker(log_generator, 'RabbitMQ: ', True)

def receive_int(signum, stack):
  sys.exit(0)

if __name__ == "__main__":

  try:
    # Gather the ports we want to use on the host
    port = int(sys.argv[1])
    mport = int(sys.argv[2])
    print "Using: python start_rabbitmq.py %s %s" % (port, mport)
  except: 
    print "Usage: python start_rabbitmq.py <rabbitmq port> <web management port>"
    print "Using defaults - python start_rabbitmq.py 5672 15672"
    port = 5672
    mport = 15672

  signal.signal(signal.SIGINT, receive_int)
  start_rabbit(port, mport)

  # Loop until SIGINT received
  while True:
    print 'RabbitMQ Bootstrapper Running...'
    sys.stdout.flush()
    time.sleep(5)
