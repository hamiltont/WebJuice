
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

@socketio.on('my event')
def handle_message(message):
  log.info("received message: %s", message)
  
if __name__ == "__main__":
  
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
  print "Importing controller"
  #from webjuice import controller
  #c = controller.Controller()
  
  app.debug = args.debug
  socketio.run(app, host='0.0.0.0', port=args.port)
