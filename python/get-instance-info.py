#!/usr/bin/python

import boto
import argparse, sys, logging
#import dnspython

def get_creds():

    # By default empty, boto will look for environment variables
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    ACCESSKEY=''
    SECRETKEY=''

    return ACCESSKEY, SECRETKEY

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", dest="hostname", required=True)
    parser.add_argument("--id", action="store_true", dest="getid", default=False)
    parser.add_argument("--pubdns", action="store_true", dest="pubdns", default=False)
    parser.add_argument("--volumes", action="store_true", dest="volumes", default=False)
    parser.add_argument("--all", action="store_true", dest="all", default=False)
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

def get_reservations(conn):
    return conn.get_all_instances()

def get_instances(reservations):
    instance_list = []
    for reservation in reservations:
        instances = reservation.instances
        for instance in instances:
            instance_list.append(instance)

    return instance_list

def does_tag_exist(tag, instance_tags):
    try:
        if instance_tags[tag]:
            logging.debug("Tag found in %r", instance_tags)
            return True
        else:
            return False
    except KeyError:
        return False

def get_instances_matching_tag(instance_list, tagname, tagvalue):
    matching_instances = []
    for instance in instance_list:
        instance_tags = instance.tags
        if does_tag_exist(tagname, instance_tags):
            if instance.tags[tagname] == tagvalue:
                matching_instances.append(instance)  
    
    return matching_instances

def get_block_device_mapping(instance):
    block_device_mapping = instance.block_device_mapping
    volumes_dict = {}
    for device in block_device_mapping:
        mapping_obj = block_device_mapping[device]
        volume = mapping_obj.volume_id
        volumes_dict[device] = volume

    return volumes_dict

def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 
    conn = get_conn(accesskey, secretkey)
    reservations_list = get_reservations(conn)
    instances = get_instances(reservations_list)
    instances = get_instances_matching_tag(instances, 'Name', args.hostname)

    if len(instances) > 1:
        logging.error("found more than one instance found with that hostname: %s", instances)
        sys.exit(1)
    else:
        logging.info("found instance: %s", instances)

    if args.getid:
        print instances[0].id
    elif args.pubdns and instances[0].state == 'running':
        print instances[0].public_dns_name
    elif args.volumes:
        volumes = get_block_device_mapping(instances[0])
        print volumes
    elif args.all:
        for k in instances[0].__dict__.iteritems():
            print k
    else:
        sys.exit(1)

if __name__ == '__main__':
    run()
