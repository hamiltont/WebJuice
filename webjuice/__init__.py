from flask import Flask
from flask.ext.socketio import SocketIO

import logging
log = logging.getLogger(__name__)

# Setting static url means we use /js/filename.js 
# versus /static/js/filename.js
log.info("Creating flask app with name %s", __name__)
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'this is a very secret key :)'
log.info("Creating socketio app")
socketio = SocketIO(app)

# Enable JADE templates
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

log.info("Importing celery")
from webjuice.tasks import app as celeryapp

log.info("Importing views")
import webjuice.views

log.info("Done with __init__ ")
