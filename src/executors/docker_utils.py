

'''
import docker
from threading import Thread
from pprint import pprint
client = docker.Client('127.0.0.1:5555', version='1.15')
pprint(client.containers()[1])
pprint(client.images())
remove_untagged_nonintermediate_images(client)
'''

import docker
import traceback
from threading import Thread

def is_image_being_run(client, image):
  for container in client.containers():
    if container['Image'].startswith(image):
      return (True, container)
  return (False,)

def container_str(container, detailed=False):
  cid = container['Id'][:8]
  image = container['Image']
  return "[%s %s]" % (cid, image)

# start the container, and then query the daemon to get the 
# entire container dict (instead of just Id and Warnings keys)
def start_then_query_container():
  pass

def containers_running_image(client,image_name):
  containers = [x for x in client.containers() if x['Image'].startswith(unicode(image_name))]
  return containers

# sudo docker images --filter "dangling=true"

def remove_untagged_nonintermediate_images(client):
  def remove_image(image):
    try:
      client.remove_image(image['Id'])  
      print "Removed %s" % image['Id']
    except docker.errors.APIError:
      print "API error for %s" % image['Id']
      print traceback.format_exc()
    except Exception:
      print "Unable to remove %s" % image['Id']
      print traceback.format_exc()
  threads = []
  for image in client.images(filters={'dangling': True}):
    # t = Thread(target=remove_image, args=(image,))
    # t.start()
    # print "Launched thread for %s" % image['Id']
    # threads.append(t)
    remove_image(image)
  for thread in threads:
    thread.join()
