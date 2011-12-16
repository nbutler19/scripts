#!/usr/bin/python

import boto
import argparse

def get_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--instance-id", dest="instanceid", required=True,
                      help="the instance-id, e.g i-1223456")
  parser.add_argument("-e", "--elastic-ip", dest="eip", required=True,
                      help="the elastic ipv4 address, e.g. 127.0.0.1")
  return parser.parse_args()

def get_conn():
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
  args = get_args()
  conn = get_conn()
  instance = get_instance(conn,args.instanceid)
  eip = get_eip(conn,args.eip)
  associate_eip(conn,eip,instance)

if __name__ == '__main__':
  run()

