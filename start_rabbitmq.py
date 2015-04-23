'''
Helper script to launch RabbitMQ using Docker. Container will 
be terminated when this script is terminated
'''

import json
import subprocess
import sys
import os
from webjuice.utils import get_docker

import signal
import time
import logging
log = logging.getLogger(__name__)

def start_rabbit(port, mport):
  (host,cli) = get_docker()
  for line in cli.pull('rabbitmq:3-management', stream=True):
    print json.dumps(json.loads(line), indent=4)

  container = cli.create_container(image='rabbitmq:3-management', hostname='WebJuice')
  cid = container.get('Id')
  cli.start(cid, port_bindings={5672: port, 15672: mport})

  log.info("Started RabbitMQ as %s", cid)
  broker_url = "amqp://guest:guest@%s:%s//" % (host, port)
  broker_api = "amqp://guest:guest@%s:%s/api" % (host, mport)
  log.info("RabbitMQ: %s", broker_url)
  log.info("RabbitMQ: Management http://%s:%s", host, mport)

  with open('.env','w') as f:
    f.write("RABBITMQ_BIGWIG_TX_URL=%s\n" % broker_url)
    f.write("RABBITMQ_BIGWIG_RX_URL=%s\n" % broker_url)
    f.write("BROKER_API=%s\n" % broker_api)

    # Setup arg flags for running webapp in development mode
    f.write("WEB_ARGS=--debug\n")
    log.info("RabbitMQ: Config written to .env")

if __name__ == "__main__":

  logging.addLevelName(logging.ERROR, 'err')
  logging.addLevelName(logging.CRITICAL, 'crit')
  logging.addLevelName(logging.INFO, 'info')
  logging.addLevelName(logging.DEBUG, 'debug')
  logging.addLevelName(logging.WARN, 'warn')
  logging.basicConfig(level=logging.DEBUG, format='%(levelname)-4s:%(filename)-.9s:%(funcName)-.9s: %(message)s')
  
  try:
    # Gather the ports we want to use on the host
    port = int(sys.argv[1])
    mport = int(sys.argv[2])
    log.info("Using: python start_rabbitmq.py %s %s", port, mport)
  except: 
    log.info("Usage: python start_rabbitmq.py <rabbitmq port> <web management port>")
    log.info("Using defaults - python start_rabbitmq.py 5672 15672")
    port = 5672
    mport = 15672

  start_rabbit(port, mport)
