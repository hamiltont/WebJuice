
# For advanced debugging
from flask_debugtoolbar import DebugToolbarExtension

import sys
import os
import argparse
import logging
import pprint

logging.addLevelName(logging.ERROR, 'err')
logging.addLevelName(logging.CRITICAL, 'crit')
logging.addLevelName(logging.INFO, 'info')
logging.addLevelName(logging.DEBUG, 'debug')
logging.addLevelName(logging.WARN, 'warn')
logging.basicConfig(level=logging.INFO, format='%(levelname)-4s:%(filename)-.9s:%(funcName)-.9s: %(message)s')
log = logging.getLogger(__name__)

from webjuice import app
from webjuice import socketio
from webjuice import celeryapp
from webjuice import pubsub

from flask.ext.socketio import send, emit
import time

@socketio.on('my event', namespace='/test')
def wire_up_socketio(message):
  log.info("received message: %s", message)

def running_inside_heroku():
  return "DYNO" in os.environ.keys()
  
def my_handler(message):
  socketio.emit('data', "Output from Redis: %s\r\n" % message, namespace='/test')
  print "MY HANDLER: %s" % message

if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(description='Run webserver')
  parser.add_argument('--port', default=int(os.environ.get('PORT', 5000)), type=int, help='Flask HTTP Port')
  parser.add_argument('--debug', default=False, action='store_true', help='Run in Debug Mode and Reload on Code Changes')
  args = parser.parse_args()
  log.info("Started with: %s", pprint.pformat(args))
  
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
  print "Importing controller"
  #from webjuice import controller
  #c = controller.Controller()
  
  app.debug = args.debug
  
  # Setup server name
  sn = os.environ.get('SERVER_NAME', 'localhost')
  if not running_inside_heroku():
    sn += ':' + str(args.port)
  log.info("Using servername %s", sn)
  app.config['SERVER_NAME'] = sn

  log.info("Subscribing...")
  p = pubsub.pubsub()
  p.subscribe(**{'mq:wjlog': my_handler})
  p.run_in_thread(sleep_time=0.25)
  log.info("Subscribed")
  
  socketio.run(app, host='0.0.0.0', port=args.port)
