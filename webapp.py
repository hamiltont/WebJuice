from flask import Flask
from flask import render_template
from flask import Response

# For advanced debugging
from flask_debugtoolbar import DebugToolbarExtension
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

from src import models
print "Importing controller"
from src import controller
from src.tasks import add

import sys
import os

from src.utils import *

# Setting static url means we use /js/filename.js 
# versus /static/js/filename.js
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'this is a very secret key :)'

# When we are in debug mode, expose a nice toolbar
app.debug = True
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

# Enable JADE templates
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

from src.tasks import app as celeryapp

(host,cli) = get_boot2docker()
broker = "amqp://guest:guest@%s:%s//" % (host, 5672)
celeryapp.conf.update(BROKER_URL = broker)
celeryapp.conf.update(CELERY_RESULT_BACKEND = broker)

@app.route("/")
@line_profile
def dash(name=None):
  models.create_database()
  return render_template('dashboard.jade', youAreUsingJade=True)

@app.route("/lang")
@line_profile
def lang(name=None):
  models.create_database()

  from src.tasks import app
  

  rootdir = os.path.dirname(os.path.realpath(__file__))
  if not os.path.exists(rootdir + '/logs'):
    os.makedirs(rootdir + '/logs')

  output_f = rootdir + "/logs/somelog.txt"
  output = open(output_f, 'w+')
  print "created outputfile: %s" % output_f
  output.close()

  task = add.delay(10,10, output_f)
  
  '''while True:
    new_printable_output = output.readline()
    if new_printable_output:
      sys.stdout.write(new_printable_output)
      sys.stdout.flush()
    if task.state not in ['PENDING', 'STARTED']:
      break
  print "*** Fabric task has finished ***"
  '''

  return render_template('lang.jade', youAreUsingJade=True)

@app.route('/logs')
def read_log_file():
  def generate():
    rootdir = os.path.dirname(os.path.realpath(__file__))
    output_f = rootdir + "/logs/somelog.txt"
    
    # See http://www.html5rocks.com/en/tutorials/eventsource/basics/
    with open(output_f, 'r') as output:
      for line in iter(output.readline, 'MAGIC_END'):
        yield 'data:' + line + '\n\n'

  return Response(generate(), mimetype='text/event-stream')


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
  print "My name is main, I'm creating a controller"
  c = controller.Controller()

  # Unfortunately you can't easily use multiprocessing and 
  # Flask's reloading, they confuse each other
  app.run(debug=True) #, use_reloader=False)

