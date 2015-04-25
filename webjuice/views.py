import os

from webjuice import app
from webjuice import models

from webjuice.executors.executor import start_docker,dump_fake_log

from flask import render_template

from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

@app.route("/")
@line_profile
def dash(name=None):
  models.create_database()
  return render_template('dashboard.jade', youAreUsingJade=True)

@app.route("/lang")
@line_profile
def lang(name=None):
  models.create_database()
  
  return render_template('lang.jade', youAreUsingJade=True)

@app.route('/start')
def start_build():
  print "Starting remote command"

  start_docker.delay()
  print "Started remote command"
  return render_template('queue.jade', youAreUsingJade=True)

@app.route('/logdump')
def start_logdump():
  print "Starting remote logdump"
  dump_fake_log.delay()
  print "Started logdump"
  return render_template('queue.jade', youAreUsingJade=True)

@app.route('/logs')
def read_log_file():
  def generate(logname):
    rootdir = os.path.dirname(os.path.realpath(__file__))
    output_f = "%s/logs/%s" % (rootdir, logname)
    
    # See http://www.html5rocks.com/en/tutorials/eventsource/basics/
    with open(output_f, 'r') as output:
      for line in iter(output.readline, 'MAGIC_END'):
        if line:
          yield 'data:' + line

  return Response(generate('docker.txt'), mimetype='text/event-stream')

@app.route("/logtest")
@line_profile
def print_log(name=None):
  return render_template('logs.jade', youAreUsingJade=True)

@app.route("/queue")
@line_profile
def queue(name=None):
  models.create_database()
  return render_template('queue.jade', youAreUsingJade=True)

@app.route("/admin")
@line_profile
def admin(name=None):
  models.create_database()
  return render_template('admin.jade', youAreUsingJade=True)

@app.route("/about")
@line_profile
def about(name=None):
  models.create_database()
  flower_url = 'http://localhost:5555'
  rabbitmq_url = "http://%s:15672" % host
  return render_template('about.jade', rabbitmq_url=rabbitmq_url, 
    flower_url=flower_url, youAreUsingJade=True)

@app.route("/login")
@line_profile
def login(name=None):
  models.create_database()
  return render_template('login.jade', youAreUsingJade=True, servername=app.config['SERVER_NAME'])



  