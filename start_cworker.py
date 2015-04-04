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

import docker
from docker.utils import kwargs_from_env
from src.utils import *

def start_celery_worker_subprocess(port):
    (host,cli) = get_boot2docker()
    broker = "amqp://guest:guest@%s:%s//" % (host, port)

    print "Running Celery Worker process"
    command = "celery worker --app=src.tasks --loglevel=INFO --broker=%s --concurrency=1" % broker
    print " $ " + command
  
    # Thanks: http://www.saltycrane.com/blog/2009/10/how-capture-stdout-in-real-time-python/
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, bufsize=1, stderr=subprocess.STDOUT)
    while p.returncode is None:
      line = p.stdout.readline()
      if not line:
        time.sleep(0.5)
        continue
      sys.stdout.write("".join(['Worker: ', line]))
      sys.stdout.flush()

    
def receive_int(signum, stack):
  sys.exit(0)

if __name__ == "__main__":
  signal.signal(signal.SIGINT, receive_int)

  try:
    # Gather the port
    port = int(sys.argv[1])
    print "Using: python start_cworker.py %s" % port
  except: 
    print "Usage: python start_cworker.py <rabbitmq port>"
    print "Using defaults - python start_cworker.py 5672"
    port = 5672

  # Loop until SIGINT received
  while True:
    print 'Celery Worker Bootstrapper Running...'
    
    # Give AMQP a moment to turn on (avoids excessive retry)
    time.sleep(2)

    start_celery_worker_subprocess(port)

    print 'ERROR: Celery Worker has aborted. Restarting...'
