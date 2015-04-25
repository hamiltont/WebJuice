from flask import Flask
from flask.ext.socketio import SocketIO

from os import environ
import logging
import redis

log = logging.getLogger(__name__)

# Setting static url means we use /js/filename.js 
# versus /static/js/filename.js
log.info("Creating flask app with name %s", __name__)
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'this is a very secret key :)'

log.info("Creating socketio app")
socketio = SocketIO(app)

if 'REDISCLOUD_URL' not in environ.keys():
  log.critical("WebJuice requires you set the REDISCLOUD_URL environment variable")
  rdis = None
  redis_url = None
  pubsub = None
  celeryapp = None
else:
  # Initiate Redis connection and ensure we can communicate
  # (name redis is conflated with package redis)
  redis_url = environ['REDISCLOUD_URL']
  rdis = redis.from_url(redis_url)
  rdis.ping()
  log.info("Connected to Redis")

  # Open dedicated connection to Redis for publish-subscribe
  # To use this, create a thread-local PubSub object using 
  # `p = webjuice.pubsub.pubsub()`
  pubsub = redis.from_url(redis_url)
  pubsub.ping()
  log.info("Connected to Redis PubSub")

  log.info("Importing celery")
  from webjuice.tasks import app as celeryapp
  celeryapp.conf.update(BROKER_URL = redis_url)
  celeryapp.conf.update(CELERY_RESULT_BACKEND = redis_url)
  celeryapp.conf.update(CELERY_TRACK_STARTED = True)

# Enable JADE templates
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

log.info("Importing views")
import webjuice.views

log.info("Done with __init__ ")
