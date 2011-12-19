#!/usr/bin/python

import boto
import argparse
import time

def get_creds():

  # By default empty, boto will look for environment variables
  # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
  ACCESSKEY=''
  SECRETKEY=''

  return ACCESSKEY, SECRETKEY

def get_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--volume-id", dest="volumeid", 
                      help="the volume-id, e.g. vol-1223456")
  parser.add_argument("-i", "--instance-id", dest="instanceid", required=True,
                      help="the instance-id, e.g i-1223456")
  parser.add_argument("-d", "--device", dest="device", required=True,
                      help="the device, e.g /dev/sdj")
  parser.add_argument("-f", "--force", action="store_false", dest="force", default=False,
                      help="whether to force the detachment if the os isn't responding. VERY DANGEROUS")
  return parser.parse_args()

def get_conn(accesskey, secretkey):
  if accesskey and secretkey:
    return boto.connect_ec2(accesskey,secretkey)
  else:
    return boto.connect_ec2()

def get_instance(conn, instanceid):
  reservation = conn.get_all_instances(instanceid)[0]
  instances = reservation.instances

  for inst in instances:
    if inst.id == instanceid:
      return inst

def get_volume(conn, volumeid):
  return conn.get_all_volumes(volumeid)[0]

def detach_volume(conn,volume, instance, device, force):
  if force:
    conn.detach_volume(volume.id, instance.id, device, force)
  else:
    conn.detach_volume(volume.id, instance.id, device)

  print "Waiting for volume to be detached",
  while volume.status != 'available':
    volume.update()
    print ".",
    time.sleep(1)

def run():
  (accesskey, secretkey) = get_creds()
  args = get_args()
  conn = get_conn(accesskey, secretkey)
  instance = get_instance(conn, args.instanceid)
  volume = get_volume(conn, args.volumeid)
  detach_volume(conn, volume, instance, args.device, args.force)

if __name__ == '__main__':
  run()
