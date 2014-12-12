

'''
import docker
client = docker.Client('10.0.0.2:5555', version='1.15')
client.containers()[1]
'''

def is_image_being_run(client, image):
  for container in client.containers():
    if container['Image'].startswith(image):
      return (True, container)
  return (False,)

def container_str(container, detailed=False):
  cid = container['Id'][:8]
  image = container['Image']
  return "[%s %s]" % (cid, image)


      
