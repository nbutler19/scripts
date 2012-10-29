#!/usr/bin/env python

import boto
import argparse

def get_creds():

    # By default empty, boto will look for environment variables
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    ACCESSKEY=None
    SECRETKEY=None

    return ACCESSKEY, SECRETKEY

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--instance-id", dest="instanceid", required=True,
                                            help="the instance-id, e.g i-1223456")
    parser.add_argument("-e", "--elastic-ip", dest="eip", required=True,
                                            help="the elastic ipv4 address, e.g. 127.0.0.1")
    parser.add_argument("-r", "--region", dest="region", default="us-east-1",
                                            help="the region to use, e.g. us-east-1/us-west-2")
    return parser.parse_args()

def get_conn(args):
    region = get_region(args)
    conn = boto.connect_ec2(args.accesskey, args.secretkey, region=region)
    return conn
 
def get_region(args):
    import boto.ec2
    regions = boto.ec2.regions(aws_access_key_id=args.accesskey,aws_secret_access_key=args.secretkey)
    for region in regions:
        if args.region == region.name:
            return region

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
    args.accesskey = accesskey
    args.secretkey = secretkey
    conn = get_conn(args)
    instance = get_instance(conn,args.instanceid)
    eip = get_eip(conn,args.eip)
    associate_eip(conn,eip,instance)

if __name__ == '__main__':
    run()
