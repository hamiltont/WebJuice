"""
Business logic of pulling tasks off the queue and scheduling
them onto executors

Manages the lifecycle of executors

TODO examine https://pypi.python.org/pypi/Cobbler/0.6.3-2 for 
potential PXE executor
"""

import logging
import logging.config
import time

from executors.docker_executor import DockerExecutor

class Controller(object):
  def __init__(self, logger=None):
    print "Init is running"
    self.logger = logger or logging.getLogger(__name__)
    self.executors = []

if __name__ == "__main__":
  print "Main is running"
  c = Controller()
  print "C returned, sleeping for 10"
  time.sleep(60)
  print "quitting"





