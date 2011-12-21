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
    parser.add_argument("-e", "--elb", dest="elb", required=True,
                                            help="the elastic load balancer name, e.g. www-prod")
    return parser.parse_args()

def get_conn(accesskey,secretkey):
    if accesskey and secretkey:
        return boto.connect_elb(accesskey,secretkey)
    else:
        return boto.connect_elb()

def get_load_balancer(conn, elbname):
    elbs = conn.get_all_load_balancers()
    for elb in elbs:
        if elb.name == elbname:
            return elb

def get_instance_state(elb):
    instances_health = elb.get_instance_health()
    for instance in instances_health:
        if instance.state != 'InService':
            return 1

    return 0

def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    conn = get_conn(accesskey,secretkey)
    elb = get_load_balancer(conn, args.elb)
    health = get_instance_state(elb)
    print health

if __name__ == '__main__':
    run()
