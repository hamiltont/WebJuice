from celery import Celery
import sys
import time

app = Celery('tasks')

@app.task(bind=True)
def add(self, x, y, filename):
  
  filename = 'somelog4.txt'
  self.update_state(state='RUNNING', meta={'log': filename})
  self.send_event('RUNNING', meta={'log': filename})
  with self.app.events.default_dispatcher() as dispatcher:
    dispatcher.send('task-custom_state', field1='value1', field2='value2')

  print "Writing to %s" % filename

  with open(filename, 'w') as output:
    self.update_state(state='RUNNING', meta={'log': filename})
    time.sleep(10)
    for i in range(0,100):
      time.sleep(1)
      output.write("Waited %s seconds\n" % i)
      output.flush()
    output.write("MAGIC_END")
    output.flush()

  return x + y


@app.task
def add21234(self, x, y):
  
  return x + y
