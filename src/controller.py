"""
Business logic of pulling tasks off the queue and scheduling
them onto executors

Manages the lifecycle of executors

TODO examine https://pypi.python.org/pypi/Cobbler/0.6.3-2 for 
potential PXE executor
"""

import logging
import logging.config
import fabric
import os
import json
import sys
import atexit
import time
import multiprocessing

import docker
from docker.utils import kwargs_from_env
import subprocess

from utils import log_for_docker,start_container

from executors.docker_executor import DockerExecutor

from tasks import app

class Controller(object):
  def __init__(self, logger=None):
    print "Init is running"
    self.logger = logger or logging.getLogger(__name__)
    self.executors = []

    # (host_ip, client) = self._get_boot2docker()
    # d_executor = DockerExecutor(client, host_ip=host_ip, commit='c74b70c5cf67355073599a62ca396dd1e8eed6c3')
    # d_executor.start()
    (host,cli) = self._get_boot2docker()
    broker = "amqp://guest:guest@%s:%s//" % (host, 5672)
    app.conf.update(BROKER_URL = broker)
    app.conf.update(CELERY_RESULT_BACKEND = broker)

  def _get_boot2docker(self):
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

  def _enable_celery(self):
    (host,cli) = self._get_boot2docker()
    container = cli.create_container(image='rabbitmq:3-management', hostname='WebJuice')
    cid = container.get('Id')
    start_container(cli, cid, publish_all_ports=True)
    port = cli.port(container.get('Id'), 5672)[0]['HostPort']
    mport = cli.port(container.get('Id'), 15672)[0]['HostPort']
    print "Started RabbitMQ as %s" % container.get('Id')
    print "RabbitMQ running on port %s (Management @ %s:%s)" % (port, host, mport)
    
    log_generator = cli.logs(container=cid, stream=True)
    log_for_docker(log_generator, 'RabbitMQ: ', True)

    broker = "amqp://guest:guest@%s:%s//" % (host, port)
    app.conf.update(BROKER_URL = broker)
    app.conf.update(CELERY_RESULT_BACKEND = broker)
    #from pprint import pprint
    #print "Conf inside controller"
    #pprint(dict(app.conf))
    
    def start_celery_worker():
      from tasks import app
      argv = [
        'worker',
        '--broker=%s' % broker,
        '--loglevel=WARNING',
        '--concurrency=1'
      ]
      p = multiprocessing.current_process()
      print "Running Celery Worker process"
      print " $ celery worker --app=tasks --broker=%s --concurrency=1 --loglevel=DEBUG" % broker
      print " - PID %s; %s" % (p.pid, p.name)
      sys.stdout.flush()
      app.worker_main(argv)

    # You can also utilize the 'multiprocessing' name in logging configuration
    # logger = multiprocessing.get_logger()
    # logger.setLevel(logging.DEBUG)
    p = multiprocessing.Process(name='cworker_1', target=start_celery_worker)
    p.daemon = True
    p.start()

    def stop_celery_worker(process):
      process.terminate()
      print "Terminating celery worker process"
      print " - SIGTERM to PID %s; %s" % (process.pid, process.name)
      process.join()
      print " - Process join complete"
    atexit.register(stop_celery_worker, p)

    def start_celery_flower():
      from flower.command import FlowerCommand
      flower = FlowerCommand()

      from tasks import app
      argv = [
        '--broker=%s' % broker,
        '--broker_api=http://guest:guest@%s:%s/api' % (host, mport),
        '--port=5555'
      ]
      flower.execute_from_commandline(argv)

      p = multiprocessing.current_process()
      print "Running Celery Flower process"
      print " $ celery flower --broker=%s --broker_api=http://guest:guest@%s:%s/api --port=5555" % (broker, host, mport)
      print " - PID %s; %s" % (p.pid, p.name)
      sys.stdout.flush()
      app.worker_main(argv)

    pf = multiprocessing.Process(name='cflower_1', target=start_celery_flower)
    pf.daemon = True
    pf.start()

    def stop_celery_flower(process):
      process.terminate()
      print "Terminating celery flower process"
      print " - SIGTERM to PID %s; %s" % (process.pid, process.name)
      process.join()
      print " - Process join complete"
    atexit.register(stop_celery_flower, pf)

if __name__ == "__main__":
  print "Main is running"
  c = Controller()
  print "C returned, sleeping for 10"
  time.sleep(60)
  print "quitting"





