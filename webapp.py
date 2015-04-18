from flask import Flask
from flask import render_template
from flask import Response

# For advanced debugging
from flask_debugtoolbar import DebugToolbarExtension
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

from src import models
print "Importing controller"
from src import controller

import sys
import os
import argparse
import logging
import pprint

from src.utils import *

# Setting static url means we use /js/filename.js 
# versus /static/js/filename.js
print "Creating flask app"
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'this is a very secret key :)'

# Enable JADE templates
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

from src.tasks import app as celeryapp
from src.tasks import add

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

from src.executors.executor import start_docker,add2

@app.route('/start')
def start_build():
  print "Starting remote command"

  start_docker.delay()
  print "Started remote command"
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
  return render_template('login.jade', youAreUsingJade=True)

@app.route("/die")
def die(name=None):
  sys.exit("Normal exit")
  
if __name__ == "__main__":

  logging.addLevelName(logging.ERROR, 'err')
  logging.addLevelName(logging.CRITICAL, 'crit')
  logging.addLevelName(logging.INFO, 'info')
  logging.addLevelName(logging.DEBUG, 'debug')
  logging.addLevelName(logging.WARN, 'warn')
  logging.basicConfig(level=logging.INFO, format='%(levelname)-4s:%(filename)-.9s:%(funcName)-.9s: %(message)s')
  log = logging.getLogger(__name__)
  
  parser = argparse.ArgumentParser(description='Run webserver')
  parser.add_argument('--broker', required=True, help='Celery Broker URL')
  parser.add_argument('--port', default=int(os.environ.get('PORT', 5000)), type=int, help='Flask HTTP Port')
  parser.add_argument('--debug', default=False, action='store_true', help='Run in Debug Mode and Reload on Code Changes')
  args = parser.parse_args()
  log.info("Started with: %s", pprint.pformat(args))

  celeryapp.conf.update(BROKER_URL = args.broker)
  celeryapp.conf.update(CELERY_RESULT_BACKEND = args.broker)
  celeryapp.conf.update(CELERY_TRACK_STARTED = True)
  
  # When we are in debug mode, expose a nice toolbar
  if args.debug:
    log.info("Setting up debug toolbar")

    toolbar = DebugToolbarExtension(app)
    app.config['DEBUG_TB_PANELS'] = [
        'flask_debugtoolbar.panels.timer.TimerDebugPanel',
        'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
        'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'flask_debugtoolbar.panels.template.TemplateDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel',
        'flask_debugtoolbar.panels.versions.VersionDebugPanel'
    ]

    # Work around stdout buffering caused by supervisord+flask combo
    # 
    # See https://github.com/mitsuhiko/flask/issues/1420
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

  log.info("My name is main, I'm creating a controller")
  c = controller.Controller()
  
  app.run(debug=args.debug, host='0.0.0.0', port=args.port)

