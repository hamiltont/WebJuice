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
#
# Initial simplification: Using port mapping, assume all computers are 
# on the same physical host. 
#
#   server is at localhost:2552
#   database is at localhost:2442
#   client is at localhost:2332

import docker
import docker_utils as dutil
import logging
import logging.config

from pprint import pformat
from getpass import getuser
from datetime import datetime


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

  def __init__(self, client, **kwargs):
    super(DockerExecutor, self).__init__(**kwargs)
    self.client = client
    self.cimage ="%s/tfb-client" % getuser()
    self.simage ="%s/tfb-server" % getuser()
    self.dimage ="%s/tfb-dbases" % getuser()

    self.ctag   = "%s:%s" % (self.cimage, self.commit)
    self.stag   = "%s:%s" % (self.simage, self.commit)
    self.dtag   = "%s:%s" % (self.dimage, self.commit)

    alive = len(self.client.containers())
    if alive != 0:
      warn("%s containers are currently running, which will impact your results", alive)

    if len(self.client.images(name=self.image)) != 0:
      warn("Container %s already exists, removing...", self.image)
      self.client.remove_image(image=self.tag, force=True)

  def setup_client_host(self): 
    client = self.client
  
    # Ensure container is built
    info("Building container %s", self.ctag)
    build_start = datetime.now()
    for line in client.build(path='docker/client', 
      tag=self.ctag, stream=True, 
      quiet=False, rm=True):
      debug("%s: %s", self.ctag, line.strip())
    info("Built container %s in %s", self.ctag, datetime.now() - build_start)

  def start_client_container(self): 
    client = self.client
  
    # Ensure tfb-client is not already being run
    running = dutil.is_image_being_run(client, self.cimage)
    if running[0]:
      warn("Container %s is already running the client image, halting", dutil.container_str(running[1]))


    '''

    # Run container
    #
    # Note: Container will vacuum up any public key files from /tmp/zz_ssh
    #       and set them up for passwordless SSH access, so all we have to 
    #       do here is mount the folder containing our public key files. We
    #       assume that's the folder where the client_identity_file is from
    #
    print "DOCKER: Starting %s" % repo
    client = c.create_container(repo, volumes=[ '/tmp/zz_ssh' ])
    key_dir = os.path.abspath(os.path.dirname(os.path.expanduser(self.client_identity_file)))
    print "DOCKER: Client will search %s for public keys" % key_dir
    mounts={
      key_dir : { 'bind': '/tmp/zz_ssh' }, 
    }
    
    lxc_options = {}
    if self.docker_client_cpuset:
      lxc_options['lxc.cgroup.cpuset.cpus'] = ",".join(str(x) for x in self.docker_client_cpuset)
      print "DOCKER: Client allowing processors [%s]" % lxc_options['lxc.cgroup.cpuset.cpus']
      
      # Update threads to be correct e.g. run wrk with threads == client logical processors
      self.threads = len(self.docker_client_cpuset)

      # Update max_threads (whcih is used only by frameworks) to be correct == logical processors 
      # allowed for this server
      self.max_threads = len(self.docker_server_cpuset)

      print "DOCKER: Updated `threads` to %s and `max_threads` to %s" % (self.threads, self.max_threads)
    if self.docker_client_ram:
      # Set (swap+ram)==(ram) to disable swap
      # See http://stackoverflow.com/a/26482080/119592
      if self.docker_client_ram < 800:
        print "DOCKER: ERROR: wrk requires at least 800MB of RAM. Increasing %s to 850" % self.docker_client_ram
        self.docker_client_ram = 850
        print "DOCKER: WARNING: If you are running wrk and the server on the same host, be sure you have enough mem for both!"
      lxc_options['lxc.cgroup.memory.max_usage_in_bytes']= "%sM" % self.docker_client_ram
      lxc_options['lxc.cgroup.memory.limit_in_bytes']    = "%sM" % self.docker_client_ram
      print "DOCKER: Client allowing %s MB real RAM" % self.docker_client_ram
    lxc = " ".join([ "--lxc-conf=\"%s=%s\""%(k,v) for k,v in lxc_options.iteritems()])
    d_command = "sudo docker run -d %s --net=host -v %s:/tmp/zz_ssh %s" % (lxc, key_dir, repo)
    
    print "DOCKER: Running client container using:"
    print "DOCKER: %s" % d_command
    c.start(client, binds=mounts, network_mode='host', lxc_conf=lxc_options)

    # Update SSH connection string 
    #   Client container uses u/p root:root and port 2332 
    self.client_ssh_string = "ssh -T -o StrictHostKeyChecking=no root@localhost -p 2332"
    self.client_ssh_string += " -i " + self.client_identity_file

    print "DOCKER: Master will use client SSH string %s" % self.client_ssh_string

    self.docker_client_container = client
    '''


  def setup_database_host(self):
    client = self.client

    self.image ="%s/tfb-db" % getuser()
    self.tag   = "%s:%s" % (self.image, self.commit)
  
    # Ensure container is built
    info("Building container %s", self.tag)
    build_start = datetime.now()
    for line in client.build(path='docker/database', 
      tag=self.tag, stream=True, 
      quiet=False, rm=True):
      debug("%s: %s", self.tag, line.strip())
    info("Built container %s in %s", self.tag, datetime.now() - build_start)

    pass

  def setup_server_host(self):

    self.image ="%s/tfb-server" % getuser()
    self.tag   = "%s:%s" % (self.image, self.commit)
  
    # Ensure container is built
    
    info("Building container %s", self.tag)
    build_start = datetime.now()
    for line in client.build(path='docker/server', 
      tag=self.tag, stream=True, 
      quiet=False, rm=True):
      debug("%s: %s", self.tag, line.strip())
    info("Built container %s in %s", self.tag, datetime.now() - build_start)

    pass


if __name__ == "__main__":
  c = utils.parse_log_config('../logging.yaml')
  logging.config.dictConfig(c)

  urllib3_logger = logging.getLogger('requests')
  urllib3_logger.setLevel(logging.CRITICAL)
  p_logger = logging.getLogger('paramiko')
  p_logger.setLevel(logging.INFO)

  client = docker.Client('127.0.0.1:5555', version='1.12')

  executor = DockerExecutor(client, commit=12)
  executor.setup_client_host()
  executor.setup_database_host()
  executor.setup_server_host()

  executor.install_client_host()





  