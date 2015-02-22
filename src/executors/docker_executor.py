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

from fabric.api import env,run,execute,hosts
from fabric.context_managers import cd
from pprint import pformat,pprint
from getpass import getuser
from datetime import datetime

import docker
import docker_utils as dutil
import utils

import subprocess
import os
import json
import exceptions

from streamlogger import use_logger
shell_logger = use_logger(__name__)

class TFBExecutor(object):
  """A base model that will use our MySQL database"""
  def __init__(self, commit, logger=None):    
    self.logger = logger or logging.getLogger(__name__)
    self.commit = commit

    global debug,warn,info
    debug = self.logger.debug
    warn = self.logger.warn
    info = self.logger.info

class DockerExecutor(TFBExecutor):

  def __init__(self, cli, host_ip, **kwargs):
    super(DockerExecutor, self).__init__(**kwargs)
    self.cli = cli
    self.host_ip = host_ip

    alive = len(self.cli.containers())
    if alive != 0:
      warn("%s containers are currently running, which will impact your results", alive)

  def __enter__(self):

    print("Building base SSH image")
    self.base_image = getuser() + '/tfb_base'
    self.build_container('docker/ssh', self.base_image)

    print("Building base TFB images")
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
      # Sets up fabric SSH library
      env.key_filename = 'docker/ssh/id_rsa'   # Use private key file
      env.abort_exception = exceptions.OSError # Do not throw SystemExit on non-zero command

      print("- Installing server software into base TFB server image %s" % self.server_id)
      print("- Using ssh -o StrictHostKeyChecking=no -p %s -i %s/docker/ssh/id_rsa root@%s" % (self.sport, os.path.dirname(os.path.realpath(__file__)), self.shost))
      execute(self.deploy_server, hosts=[self.server_fab])

      print("- Installing client software into base TFB client image %s" % self.client_id)
      print("- Using ssh -o StrictHostKeyChecking=no -p %s -i %s/docker/ssh/id_rsa root@%s" % (self.cport, os.path.dirname(os.path.realpath(__file__)), self.chost))
      execute(self.deploy_client, hosts=[self.server_fab])

      print("- Installing database software into base TFB database image %s" % self.databa_id)
      print("- Using ssh -o StrictHostKeyChecking=no -p %s -i %s/docker/ssh/id_rsa root@%s" % (self.dport, os.path.dirname(os.path.realpath(__file__)), self.dhost))
      execute(self.deploy_database, hosts=[self.server_fab])
    except Exception:
      self.logger.error("- Software Installation Failed, Unable to Continue!")
      self.__exit__(None, None, None)
      raise

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
    return self

  def __exit__(self, type, value, traceback):
    fabric.network.disconnect_all()

    ids=['server_id','client_id','databa_id']
    for id in ids:
      if hasattr(self, id):
        warn("Killing container %s", getattr(self,id))
        self.cli.kill(getattr(self,id))

  def deploy_server(self):
    run('apt-get update -qq && apt-get install -yqq git-core python2.7 python-pip', **shell_logger)
    run('git clone https://github.com/hamiltont/FrameworkBenchmarks.git /root/FrameworkBenchmarks', **shell_logger)

    # Create user to run the frameworks
    run('adduser --disabled-password --gecos "" tfbrunner')
    run('echo "tfbrunner ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers')

    with cd('/root/FrameworkBenchmarks'):
      run('pip install -r config/python_requirements.txt', **shell_logger)

      return
      command = 'python toolset/run-tests.py --install server --client-user root '
      command += '--runner-user tfbrunner --database-user root --install-only '
      command += '--test ""'
      run(command, **shell_logger)

  def deploy_client(self):
    with cd('/root/FrameworkBenchmarks'): 
      command = 'python toolset/run-tests.py --install client --verbose --install-only '
      command += '--client-user root --runner-user tfbrunner --database-user root '
      command += "--client-host client --client-identity-file /root/.ssh/id_rsa"
      run(command, **shell_logger)

  def deploy_database(self):
    '''Configues a database on self.dhost, requires SSH to be listening on port 22
    as we have no way to modify both the internal SFTP command and the internal SSH
    command'''
    # TODO the databases are restarted before each framework test, so eventually we 
    # would like to have that happen inside TFB in a manner that works inside Docker

    # If we could run login -f root as the "bash command" we could avoid all those 
    # nasty locale errors. See https://github.com/docker/docker/issues/2424

    with cd('/root/FrameworkBenchmarks'):
      command = 'python toolset/run-tests.py --install database --verbose --install-only '
      command += '--client-user root --runner-user tfbrunner --database-user root '
      command += "--database-host database --database-identity-file /root/.ssh/id_rsa"
      run(command, **shell_logger)

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
    debug("Started %s in %s", image, container['Id'])
    return container['Id']

  def build_container(self, dockerfile_path, container_tag):
    info("Building container %s", container_tag)
    build_start = datetime.now()
    for line in self.cli.build(path=dockerfile_path, 
      tag=container_tag, stream=True, 
      quiet=False, rm=True):
      debug("%s: %s", container_tag, json.loads(line)['stream'].rstrip())
    debug("Built container %s in %s", container_tag, datetime.now() - build_start)


def get_boot2docker_environ():
  boot = '$(/usr/local/bin/boot2docker shellinit 2>/dev/null)'
  host = subprocess.check_output(boot + ' && echo $DOCKER_HOST', shell=True)
  cert = subprocess.check_output(boot + ' && echo $DOCKER_CERT_PATH', shell=True)
  tls  = subprocess.check_output(boot + ' && echo $DOCKER_TLS_VERIFY', shell=True)
  os.environ['DOCKER_CERT_PATH'] = cert.rstrip()
  os.environ['DOCKER_HOST'] = host.rstrip()
  os.environ['DOCKER_TLS_VERIFY'] = tls.rstrip()

if __name__ == "__main__":
  c = utils.parse_log_config('../logging.yaml')
  logging.config.dictConfig(c)

  urllib3_logger = logging.getLogger('requests')
  urllib3_logger.setLevel(logging.CRITICAL)
  p_logger = logging.getLogger('paramiko')
  p_logger.setLevel(logging.INFO)

  get_boot2docker_environ()
  from docker.utils import kwargs_from_env
  client = docker.Client(**kwargs_from_env(assert_hostname=False))

  host_ip = subprocess.check_output('/usr/local/bin/boot2docker ip', shell=True).rstrip()
  with DockerExecutor(client, host_ip=host_ip, commit='c74b70c5cf67355073599a62ca396dd1e8eed6c3') as executor:
    print "doing stuff"

  executor.install_client_host()





  