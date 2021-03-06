"""
An executor for benchmarking TFB using Docker containers. 

Discards containers after using (future work may save containers
for brief periods to enable rapidly gathering many trials)
"""

# Normal executors have provision (allow executor reuse), deploy, run, gather, parse
# Docker's p+d stage has (build container,start container,install)
#
# Build base containers (same for all commits)
# Start containers      (test strategy)
#   - choose link strategy (localhost == linking, host network, port mapping)
#                          (remote == host network, port mapping)
# Install s/w on containers (needs remote conn info)
#   - SSH into server, install onto remotes
# Run s/w
# Extract resutls
#   - strategy where interesting file paths are based on commit
# Parse results
#   - Ensure 'standard' set of results and then extras
#     - plan for NA!
#   - strategy where results are based on commit
#
# Consider using docker run --add-hosts eventually
#
#
# Initial simplification: Using port mapping, assume all computers are 
# on the same physical host. 
#
#   server is at localhost:2552
#   database is at localhost:2442
#   client is at localhost:2332

import logging
import logging.config
import fabric

from fabric.api import env,run,execute,hosts,sudo
from fabric.context_managers import cd
from pprint import pformat,pprint
from getpass import getuser
from datetime import datetime

import docker
import docker_utils as dutil

from webjuice.utils import get_docker

import subprocess
import os

from os.path import dirname,abspath,join
import json
import exceptions
import time

from webjuice import socketio
from webjuice import rdis

from flask.ext.socketio import send, emit

fabric_log = logging.getLogger("fabric-system")
fabric_log.addHandler(logging.FileHandler('fab_temp.log'))

from streamlogger import use_logger
shell_logger = use_logger(__name__)
log = logging.getLogger(__name__)

from celery import current_app


def broadcast(db, channel, event_name, content):
  """
  Push relevant details to Redis pub/sub channel 
  and save to replay log.
  """
  timestamp = int(time.time() * 1000)
  # flatten data to put on queue
  flattened = json.dumps({'event_name': event_name, 'content': content, 
                          'timestamp': timestamp})
  # Notify realtime server that new message is ready.
  db.publish("mq:{0}".format(channel), flattened)
  # Save message to replay log
  db.zadd("replay:{0}".format(channel), flattened, timestamp)


@current_app.task(name='webjuice.executors.executor.dump_fake_log')
def dump_fake_log():
  log.info("Running rdis dump from background process")
  log.info("Using redis %s", rdis)
  for i in xrange(100):
    broadcast(rdis, 'wjlog', 'somename', "value %s" % i)
    time.sleep(1)
  log.info("done running rdis dump from background process")

@current_app.task(name='webjuice.executors.executor.start_docker')
def start_docker():

  (host,cli) = get_docker()
  log.info("Got docker as %s,%s", host, cli)

  #d = DockerExecutor(cli, host_ip=host, commit='c74b70c5cf67355073599a62ca396dd1e8eed6c3')
  #d.create_base_images()

  def framework_run():
    with cd('~/FrameworkBenchmarks'):
      command = 'python toolset/run-tests.py --install server --verbose --test haywire --runner-user tfbrunner '
      command += '--client-user root   --client-host client     --client-identity-file ~/.ssh/id_rsa '
      command += '--database-user root --database-host database --database-identity-file ~/.ssh/id_rsa '
      run(command, **shell_logger)

  with DockerExecutor(cli, host_ip=host, commit='c74b70c5cf67355073599a62ca39s6dd1e8eed6c3') as executor:
    print "Base images constructed"
    execute(framework_run, hosts=[executor.server_fab])
    


class TFBExecutor(object):
  """A base model that will use our MySQL database"""
  def __init__(self, commit):
      self.commit = commit

class DockerExecutor(TFBExecutor):

  def __init__(self, cli, host_ip, **kwargs):
    super(DockerExecutor, self).__init__(**kwargs)
    self.cli = cli
    self.host_ip = host_ip

    alive = len(self.cli.containers())
    if alive != 0:
      log.warn("%s containers are currently running, which will impact your results", alive)

  def __enter__(self):
    base_path = abspath(join(dirname(__file__),'docker','ssh'))
    log.info("Building base SSH image from %s", base_path)
    self.base_image = getuser() + '/tfb_base'
    self.build_container(base_path, self.base_image)

    # Sets up fabric SSH library
    # - Specify RSA private key location for passwordless SSH
    # - Do not throw SystemExit on non-zero return code
    env.key_filename = abspath(join(dirname(__file__),'docker','ssh','id_rsa'))
    env.abort_exception = exceptions.OSError 

    # TODO Utilize the tag to ensure they are the correct base image
    server = len(self.cli.images(name=getuser()+'/tfb_server')) > 0
    client = len(self.cli.images(name=getuser()+'/tfb_client')) > 0
    databa = len(self.cli.images(name=getuser()+'/tfb_databa')) > 0

    '''
    # Just start the base images, they are already built
    if server and client and databa:
      # start things
      info("Base images already exist, starting containers")
      self.sport_internal = 22
      self.cport_internal = 22
      self.dport_internal = 22
      self.client_id = self.start_container(getuser()+'/tfb_client:' + self.commit)
      self.databa_id = self.start_container(getuser()+'/tfb_databa:' + self.commit)
      self.server_id = self.start_container(getuser()+'/tfb_server:' + self.commit,
        links=[(self.client_id, 'client'),(self.databa_id, 'database')])
      self.sport = self.cli.port(self.server_id, self.sport_internal)[0]['HostPort']
      self.cport = self.cli.port(self.client_id, self.cport_internal)[0]['HostPort']
      self.dport =  self.cli.port(self.databa_id, self.dport_internal)[0]['HostPort']
      (self.shost, self.dhost, self.chost) = (self.host_ip, self.host_ip, self.host_ip)

      self.server_fab = "root@%s:%s" % (self.shost, self.sport)
      self.client_fab = "root@%s:%s" % (self.chost, self.cport)
      self.databa_fab = "root@%s:%s" % (self.dhost, self.dport)
      try:
        print("Turning database container on by running installation")
        execute(self.deploy_database, hosts=[self.server_fab])
      except OSError:
        self.logger.error("turning on databases failed")
    else:
      '''
    self.create_base_images()

    return self

  def create_base_images(self):
    log.info("Building base TFB images")
    self.sport_internal = 22
    self.cport_internal = 22
    self.dport_internal = 22
    self.client_id = self.start_container(self.base_image)
    self.databa_id = self.start_container(self.base_image)
    self.server_id = self.start_container(self.base_image,
      links=[(self.client_id, 'client'),(self.databa_id, 'database')])
    self.sport = self.cli.port(self.server_id, self.sport_internal)[0]['HostPort']
    self.cport = self.cli.port(self.client_id, self.cport_internal)[0]['HostPort']
    self.dport =  self.cli.port(self.databa_id, self.dport_internal)[0]['HostPort']

    (self.shost, self.dhost, self.chost) = (self.host_ip, self.host_ip, self.host_ip)

    self.server_fab = "root@%s:%s" % (self.shost, self.sport)
    self.client_fab = "root@%s:%s" % (self.chost, self.cport)
    self.databa_fab = "root@%s:%s" % (self.dhost, self.dport)

    try:
      log.info("- Installing server software into base TFB server image %s", self.server_id)
      log.debug("- Manual Login: ssh -o StrictHostKeyChecking=no -p %s -i %s/docker/ssh/id_rsa tfb@%s",
        self.sport, abspath(dirname(__file__)), self.shost)
      execute(self.deploy_server, hosts=[self.server_fab])

      log.info("- Installing client software into base TFB client image %s", self.client_id)
      log.debug("- Manual Login: ssh -o StrictHostKeyChecking=no -p %s -i %s/docker/ssh/id_rsa root@%s",
        self.cport, abspath(dirname(__file__)), self.chost)
      execute(self.deploy_client, hosts=[self.server_fab])

      log.info("- Installing database software into base TFB database image %s", self.databa_id)
      log.debug("- Manual Login: ssh -o StrictHostKeyChecking=no -p %s -i %s/docker/ssh/id_rsa root@%s", 
        self.dport, abspath(dirname(__file__)), self.dhost)
      execute(self.deploy_database, hosts=[self.server_fab])
    except Exception:
      log.exception("- Software Installation Failed, Unable to Continue!")
      self.__exit__(None, None, None)
      raise

    # Premature optimization fool
    '''
    print "Base software installation complete, saving containers as images"

    self.cli.commit(container=self.server_id, 
      repository=getuser()+'/tfb_server',
      tag=self.commit,
      message='Autogenerated by TFB Looper',
      author='Hamilton Turner')
    self.cli.commit(container=self.client_id, 
      repository=getuser()+'/tfb_client',
      tag=self.commit,
      message='Autogenerated by TFB Looper',
      author='Hamilton Turner')
    self.cli.commit(container=self.databa_id, 
      repository=getuser()+'/tfb_databa',
      tag=self.commit,
      message='Autogenerated by TFB Looper',
      author='Hamilton Turner')
    '''

  def __exit__(self, type, value, traceback):
    fabric.network.disconnect_all()

    ids=['server_id','client_id','databa_id']
    for id in ids:
      if hasattr(self, id):
        log.warn("Killing container %s", getattr(self,id))
        # self.cli.kill(getattr(self,id))

  def deploy_server(self):    
    # Create user to run the toolset
    run('adduser --disabled-password --gecos "" tfb')
    run('echo "tfb ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers')
    
    run('''mkdir /home/tfb/.ssh && \
      for k in `ls /tmp/ssh/*.pub`; do \
        cat $k >> /home/tfb/.ssh/authorized_keys; \
      done && \
      cp /tmp/ssh/* /home/tfb/.ssh && \
      chown -R tfb:tfb /home/tfb/.ssh && \
      chmod 700 /home/tfb/.ssh && \
      chmod 600 /home/tfb/.ssh/authorized_keys && \
      chmod 600 /home/tfb/.ssh/id_rsa''')

    # Update server connection info now that we no longer need root
    self.server_fab = "tfb@%s:%s" % (self.shost, self.sport)
    execute(self.deploy_server_as_tfb, hosts=[self.server_fab])

  def deploy_server_as_tfb(self):
    run('echo "export DEBIAN_FRONTEND=noninteractive" | cat - ~/.bashrc > /tmp/temp && mv /tmp/temp ~/.bashrc')

    sudo('apt-get update -qq && apt-get install -yqq git-core python2.7 python-pip > /dev/null', user='root', pty=False)

    # Provide killall command
    sudo('apt-get install -qq psmisc > /dev/null', user='root', pty=False)
    
    run('git clone https://github.com/hamiltont/FrameworkBenchmarks.git ~/FrameworkBenchmarks', pty=False)

    # Create user to run the applications
    sudo('adduser --disabled-password --gecos "" tfbrunner', user='root')
    run('echo "tfbrunner ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers')

    # User tfbrunner needs read access to files owned by tfb e.g. the toolset
    sudo('usermod -a -G tfb tfbrunner', user='root')

    # User tfbrunner needs read write access to all framework folders owned by tfb e.g. the toolset
    run('mkdir ~/FrameworkBenchmarks/results && chmod -R g+w ~/FrameworkBenchmarks/frameworks ~/FrameworkBenchmarks/results')

    # Just a convenience thing - Currently TFB chown's the installs folder to tfbrunner
    sudo('usermod -a -G tfbrunner tfb', user='root')

    with cd('~/FrameworkBenchmarks'):
      run('pip install --user -r requirements.txt')

      command = 'python toolset/run-tests.py --install server --client-user root '
      command += '--runner-user tfbrunner --database-user root --install-only '
      command += '--test ""'
      run(command, pty=False)

  def deploy_client(self):
    with cd('~/FrameworkBenchmarks'): 
      command = 'python toolset/run-tests.py --install client --verbose --install-only '
      command += '--client-user root --runner-user tfbrunner --database-user root '
      command += '--client-host client --client-identity-file ~/.ssh/id_rsa'
      run(command, pty=False)

  def deploy_database(self):
    '''Configues a database on self.dhost, requires SSH to be listening on port 22
    as we have no way to modify both the internal SFTP command and the internal SSH
    command'''
    # TODO the databases are restarted before each framework test, so eventually we 
    # would like to have that happen inside TFB in a manner that works inside Docker

    # If we could run login -f root as the "bash command" we could avoid all those 
    # nasty locale errors. See https://github.com/docker/docker/issues/2424

    with cd('~/FrameworkBenchmarks'):
      command = 'python toolset/run-tests.py --install database --verbose --install-only '
      command += '--client-user root --runner-user tfbrunner --database-user root '
      command += '--database-host database --database-identity-file ~/.ssh/id_rsa'
      run(command, pty=False)

      # Manually start mongo, it uses Upstart and that's not available inside
      # Docker
      # See https://github.com/docker-library/mongo/blob/d9fb48dbdb0b9c35d35902429fe1a28527959f25/2.4/Dockerfile
      
      # Start mysql, because "sudo start mysql" uses Upstart
      # run('service mysql start', **shell_logger)
      
  def start_container(self, image, port=22, network='bridge', links=[]):
    # env = {"SSH_PORT": str(port)}
    env = {"SSH_PORT": str(22)}
    container = self.cli.create_container(image=image, detach=True, 
      environment=env, tty=True, ports=[port])
    self.cli.start(container=container['Id'],
      publish_all_ports=True, network_mode=network,
      links=links)
    log.debug("Started %s in %s", image, container['Id'])
    return container['Id']

  def build_container(self, dockerfile_path, container_tag):
    log.info("Building container %s", container_tag)
    build_start = datetime.now()
    for line in self.cli.build(path=dockerfile_path, 
      tag=container_tag, stream=True, 
      quiet=False, rm=True):
      if 'stream' in line:
        log.debug("%s: %s", container_tag, json.loads(line)['stream'].rstrip())
      else:
        log.debug("%s: %s", container_tag, line.rstrip())
      print line.rstrip()
    log.debug("Built container %s in %s", container_tag, datetime.now() - build_start)

  def unprovision_hosts(self, remove=True):
    def halt_and_rm(image):
      for container in dutil.containers_running_image(self.client, image):
        log.warn("Halting container %s", dutil.container_str(container))
        self.client.stop(container['Id'])
        if remove:
          self.client.remove_container(container['Id'])
    halt_and_rm(self.cimage)
    halt_and_rm(self.simage)
    halt_and_rm(self.dimage)

    def safe_rm(image_name):
      for image in self.client.images(name=image_name):
        try:
          self.client.remove_image(image)
        except Exception:
          log.exception("Failed to remove %s", image)
    safe_rm(self.cimage)
    safe_rm(self.dimage)
    safe_rm(self.simage)

if __name__ == "__main__":
  c = utils.parse_log_config('../logging.yaml')
  logging.config.dictConfig(c)

  urllib3_logger = logging.getLogger('requests')
  urllib3_logger.setLevel(logging.CRITICAL)
  p_logger = logging.getLogger('paramiko')
  p_logger.setLevel(logging.INFO)

  (host_ip,client) = get_docker()

  def framework_run():
    with cd('~/FrameworkBenchmarks'):
      command = 'python toolset/run-tests.py --install server --verbose --test haywire --runner-user tfbrunner '
      command += '--client-user root   --client-host client     --client-identity-file ~/.ssh/id_rsa '
      command += '--database-user root --database-host database --database-identity-file ~/.ssh/id_rsa '
      run(command, **shell_logger)

  with DockerExecutor(client, host_ip=host_ip, commit='c74b70c5cf67355073599a62ca396dd1e8eed6c3') as executor:
    execute(framework_run, hosts=[executor.server_fab])


  # Run TFB installation inside the containers
  # executor.deploy()

  # Actually run the benchmark




  