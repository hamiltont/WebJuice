'''
Helper script to launch Redis server using Docker. Container will 
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

def start_redis(port):
  (host,cli) = get_docker()
  for line in cli.pull('redis:3.0.0', stream=True):
    print line

  container = cli.create_container(image='redis:3.0.0', hostname='WebJuice')
  cid = container.get('Id')
  cli.start(cid, port_bindings={6379: port})

  log.info("Started Redis as %s", cid)
  redis_url = "redis://%s:%s/" % (host, port)
  log.info("Redis: %s", redis_url)

  with open('.env','w') as f:
    f.write("REDISCLOUD_URL=%s\n" % redis_url)

    # Setup arg flags for running webapp in development mode
    f.write("WEB_ARGS=--debug\n")
    log.info("Redis: Config written to .env")

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
    log.info("Using: python start_redis.py %s", port)
  except: 
    log.info("Usage: python start_redis.py <redis port>")
    log.info("Using defaults - python start_redis.py 6379")
    port = 6379

  start_redis(port)
