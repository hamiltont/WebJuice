from flask import Flask
from flask import render_template

# For advanced debugging
from flask_debugtoolbar import DebugToolbarExtension
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

import models

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
  return render_template('about.jade', youAreUsingJade=True)

@app.route("/login")
@line_profile
def login(name=None):
  models.create_database()
  return render_template('login.jade', youAreUsingJade=True)
  
app.run()

