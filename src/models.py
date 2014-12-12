#
# Define ORM models for main components
#
# Note: Peewee ensures every table has a primary key, and will
# create a field `id` if you don't set a primary key
#
# Note: If you need to update these, peewee comes with 
# a schema migration API allowing you to do things like add columns

from peewee import *

# Keep an eye on the raw queries
import logging
logger = logging.getLogger('peewee')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

mysql_db = MySQLDatabase('foobarb', host='127.0.0.1', user='root', password='')

class BaseModel(Model):
  """A base model that will use our MySQL database"""
  class Meta:
    database = mysql_db

class Trigger(BaseModel):
  category = CharField()

class Benchmark(BaseModel):
  entered = DateTimeField()
  started = DateTimeField()
  trigger = ForeignKeyField(Trigger, related_name='benchmark')

def create_database():
  tables = [Trigger, Benchmark]
  mysql_db.drop_tables(tables, safe=True, cascade=True)    

  for table in tables:
    try:
      table.create_table()
    except peewee.OperationalError:    
      print "Unable to create table %s" % table

if __name__ == "__main__":
  create_database()
  