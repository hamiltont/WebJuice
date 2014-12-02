from flask import Flask
from flask import render_template

# For advanced debugging
from flask_debugtoolbar import DebugToolbarExtension
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

import models

app = Flask(__name__)
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

list_in_py = range(10)

@app.route("/")
@app.route('/hello/<name>')
@line_profile
def hello(name=None):
  models.create_database()
  return render_template('hello.jade', youAreUsingJade=True, name=name, values=list_in_py, list_in_py=list_in_py) 

app.run()

