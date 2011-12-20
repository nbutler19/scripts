#!/usr/bin/python

import boto
import argparse
import time, sys, logging

def get_creds():

  # By default empty, boto will look for environment variables
  # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
  ACCESSKEY=''
  SECRETKEY=''

  return ACCESSKEY, SECRETKEY

def get_args():
  parser = argparse.ArgumentParser()
  ebs_filter_group = parser.add_mutually_exclusive_group(required=True)
  ebs_filter_group.add_argument("-v", "--volume-id", dest="volumeid", 
                      help="the volume-id, e.g. vol-1223456")
  ebs_filter_group.add_argument("-s", "--snapshot-id", dest="snapshotid",
                      help="the snapshot-id, e.g. snap-1223456")
  parser.add_argument("-i", "--instance-id", dest="instanceid", required=True,
                      help="the instance-id, e.g i-1223456")
  parser.add_argument("-d", "--device", dest="device", required=True,
                      help="the device, e.g /dev/sdj")
  parser.add_argument("-l", "--log", dest="loglevel", default='CRITICAL',
                      choices=['CRITICAL','FATAL','ERROR','WARN','WARNING','INFO','DEBUG','NOTSET'],
                      help="the loglevel sets the amount of output you want")
  return parser.parse_args()

def get_numeric_loglevel(loglevel):
  return getattr(logging, loglevel.upper())

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

def get_snapshot(conn, snapshotid):
  return conn.get_all_snapshots(snapshotid)[0]

def get_volume(conn, volumeid):
  return conn.get_all_volumes(volumeid)[0]

def create_volume_from_snapshot(conn, snapshot, instance):
  volume = conn.create_volume(snapshot.volume_size, instance.placement, snapshot)

  while volume.status != 'available':
    volume.update()
    time.sleep(1)

  return volume

def attach_volume(conn,volume, instance, device):
  conn.attach_volume(volume.id, instance.id, device)

  while volume.status != 'in-use':
    volume.update()
    time.sleep(1)

  instance.update()

  if instance.block_device_mapping[device].status != 'attached':
    logging.info("Waiting for volume %s to become attached", volume.id),
    counter = 0
    while instance.block_device_mapping[device].status != 'attached' and counter < 30:
      instance.update()
      time.sleep(1)
      counter = counter + 1

    instance.update()

    if instance.block_device_mapping[device].status == 'attached':
      logging.info("Succeeded")
      return
    else:
      logging.error("Failed to attach volume. Volume '%s' in state '%s'", volume.id, instance.block_device_mapping[device].status)
      return 1

def run():
  (accesskey, secretkey) = get_creds()
  args = get_args()
  numeric_level = get_numeric_loglevel(args.loglevel)
  logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 
  conn = get_conn(accesskey, secretkey)
  instance = get_instance(conn, args.instanceid)
  if args.volumeid:
    volume = get_volume(conn, args.volumeid)
    retval = attach_volume(conn, volume, instance, args.device)
    sys.exit(retval)
  else:
    snapshot = get_snapshot(conn, args.snapshotid)
    volume = create_volume_from_snapshot(conn, snapshot, instance)
    retval = attach_volume(conn, volume, instance, args.device)
    sys.exit(retval)


if __name__ == '__main__':
  run()
