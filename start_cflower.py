'''
Helper script to launch RabbitMQ using Docker. Container will 
be terminated when this script is terminated
'''

import json
import subprocess
import sys
import os

import signal
import time
import threading

import docker
from docker.utils import kwargs_from_env
from src.utils import log_for_docker,start_container

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

def start_celery_flower_subprocess(port,mport,fport):
    (host,cli) = get_boot2docker()
    broker = "amqp://guest:guest@%s:%s//" % (host, port)

    print "Running Celery Flower process"
    command = "celery flower -A src.tasks --logging=info --log_to_stderr --broker=%s --broker_api=http://guest:guest@%s:%s/api --port=%s" % (broker, host, mport,fport)
    print " $ " + command

    # Thanks: http://www.saltycrane.com/blog/2009/10/how-capture-stdout-in-real-time-python/
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, bufsize=1, stderr=subprocess.STDOUT)
    while p.returncode is None:
      line = p.stdout.readline()
      if not line:
        time.sleep(0.5)
        continue
      sys.stdout.write("".join(['Flower: ', line]))
      sys.stdout.flush()

def start_celery_flower_direct(port,mport,fport):
  print "Celery flower direct running"
  from flower.command import FlowerCommand
  flower = FlowerCommand()

  from src.tasks import app
  (host,cli) = get_boot2docker()
  broker = "amqp://guest:guest@%s:%s//" % (host, port)

  argv = [
    '--app=src.tasks'
    '--broker=%s' % broker,
    '--broker_api=http://guest:guest@%s:%s/api' % (host, mport),
    '--port=5555'
  ]
  flower.execute_from_commandline(argv)

  print "Running Celery Flower process"
  print " $ celery flower --broker=%s --broker_api=http://guest:guest@%s:%s/api --port=5555" % (broker, host, mport)
  app.worker_main(argv)

# def start_celery_flower_docker(port,mport,fport):
#   (host,cli) = get_boot2docker()
#   container = cli.create_container(image='johncosta/flower')
#   cid = container.get('Id')
#   start_container(cli, cid, port_bindings={5555: fport})

#   print "Started Flower as %s" % container.get('Id')
#   #docker run -d -p=49555:5555 johncosta/flower flower --port=5555 --broker=amqp://guest:guest@192.168.59.103:5672// --broker_api=http://guest:guest@192.168.59.103:15672/api
#   print "Flower running on %s:%s" % (host, fport)
  
#   log_generator = cli.logs(container=cid, stream=True)
#   log_for_docker(log_generator, 'Flower: ', True)
    
def receive_int(signum, stack):
  sys.exit(0)

if __name__ == "__main__":
  print 'Celery Flower Bootstrapper online...'

  signal.signal(signal.SIGINT, receive_int)

  try:
    # Gather the port
    port = int(sys.argv[1])
    mport = int(sys.argv[2])
    fport = int(sys.argv[3])
    print "Using: python start_cflower.py %s %s %s" % (port,mport,fport)
  except: 
    print "Usage: python start_cflower.py <rabbitmq port> <management port> <flower port>"
    print "Using defaults - python start_cflower.py 5672 15672 5555"
    port = 5672
    mport = 15672
    fport = 5555

  # Loop until SIGINT received
  while True:
    print 'Celery Flower Bootstrapper Running...'
    
    # Give AMQP a moment to turn on (avoids excessive retry)
    time.sleep(2)

    #start_celery_flower_direct(port,mport,fport)
    start_celery_flower_subprocess(port,mport,fport)

    print 'ERROR: Flower has aborted. Restarting...'


