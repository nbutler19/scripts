#!/usr/bin/env python

import boto
import argparse
import time, sys, logging, re

def get_creds():

    # By default empty, boto will look for environment variables
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    ACCESSKEY=''
    SECRETKEY=''

    return ACCESSKEY, SECRETKEY

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--secgrp", dest="secgrp",
        help="the Security Group, e.g default")
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

def acl_check(args):
    for group in args.groups:
        logging.info("Working on Security Group: %s" % group)
        check_questionable_acls(group)

def check_questionable_acls(group):
    for perm in group.rules:
        from_port = int(perm.from_port)
        to_port = int(perm.to_port)
        distance = (to_port - from_port)
        if distance > 1000:
            logging.warn("Found Permission: %s with a large port range allowed" % perm)
            grants = get_vulnerable_grants(perm)
            if grants:
                logging.critical("'%s': has wide open %s with IP grant %s" % (group,perm,grants))

def get_vulnerable_grants(perm):
    r = re.compile('^(?:\d{1,3}\.){3}\d{1,3}')
    grants = []
    for grant in perm.grants:
        if grant.cidr_ip and r.match(grant.cidr_ip):
            grants.append(grant)

    return grants

def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 
    conn = get_conn(accesskey, secretkey)
    if args.secgrp:
        args.groups = conn.get_all_security_groups(groupnames=args.secgrp.split(','))
    else:
        args.groups = conn.get_all_security_groups()
    acl_check(args)

if __name__ == '__main__':
    run()
