from flask import Flask

# Setting static url means we use /js/filename.js 
# versus /static/js/filename.js
print "Creating flask app with name %s" % __name__
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'this is a very secret key :)'

# Enable JADE templates
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

print "Importing celery"
from webjuice.tasks import app as celeryapp

import webjuice.views
