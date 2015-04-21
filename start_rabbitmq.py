'''
Helper script to launch RabbitMQ using Docker. Container will 
be terminated when this script is terminated
'''

import json
import subprocess
import sys
import os
from webjuice.utils import *

import signal
import time

def start_rabbit(port, mport):
  (host,cli) = get_boot2docker()
  container = cli.create_container(image='rabbitmq:3-management', hostname='WebJuice')
  cid = container.get('Id')
  cli.start(cid, port_bindings={5672: port, 15672: mport})

  print "Started RabbitMQ as %s" % cid
  broker_url = "amqp://guest:guest@%s:%s//" % (host, port)
  broker_api = "amqp://guest:guest@%s:%s/api" % (host, mport)
  print "RabbitMQ: " + broker_url
  print "RabbitMQ: Management http://%s:%s" % (host, mport)

  with open('.env','w') as f:
    f.write("RABBITMQ_BIGWIG_TX_URL=%s\n" % broker_url)
    f.write("RABBITMQ_BIGWIG_RX_URL=%s\n" % broker_url)
    f.write("BROKER_API=%s\n" % broker_api)

    # Setup arg flags for running webapp in development mode
    f.write("WEB_ARGS=--debug\n")
    print "RabbitMQ: Config written to .env"

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

  start_rabbit(port, mport)
