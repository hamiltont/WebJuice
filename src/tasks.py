from celery import Celery
import sys
import time

app = Celery('tasks')

@app.task
def add(x, y, filename):
  print "Writing to %s" % filename
  with open(filename, 'w') as output:
    for i in range(0,100):
      time.sleep(1)
      output.write("Waited %s seconds\n" % i)
      output.flush()
    output.write("MAGIC_END")
    output.flush()

  return x + y
