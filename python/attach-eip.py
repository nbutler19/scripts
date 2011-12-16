#!/usr/bin/python

import boto
import argparse

def get_creds():

  # By default empty, boto will look for environment variables
  # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
  ACCESSKEY=''
  SECRETKEY=''

  return ACCESSKEY, SECRETKEY

def get_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--instance-id", dest="instanceid", required=True,
                      help="the instance-id, e.g i-1223456")
  parser.add_argument("-e", "--elastic-ip", dest="eip", required=True,
                      help="the elastic ipv4 address, e.g. 127.0.0.1")
  return parser.parse_args()

def get_conn(accesskey,secretkey):
  if accesskey and secretkey:
    return boto.connect_ec2(accesskey,secretkey)
  else:
    return boto.connect_ec2()

def get_instance(conn,instanceid):
  reservation = conn.get_all_instances(instanceid)[0]
  instances = reservation.instances

  for inst in instances:
    if inst.id == instanceid:
      return inst

def get_eip(conn,eip):
  addresses = conn.get_all_addresses()
  for address in addresses:
    if address.public_ip == eip:
      return address

def associate_eip(conn,eip,instance):
  eip.associate(instance.id) 

def run():
  (accesskey, secretkey) = get_creds()
  args = get_args()
  conn = get_conn(accesskey, secretkey)
  instance = get_instance(conn,args.instanceid)
  eip = get_eip(conn,args.eip)
  associate_eip(conn,eip,instance)

if __name__ == '__main__':
  run()
