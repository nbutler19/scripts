#!/usr/bin/env python

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
    parser.add_argument("-v", "--volume-id", dest="volumeid", 
                                            help="the volume-id, e.g. vol-1223456")
    parser.add_argument("-i", "--instance-id", dest="instanceid", required=True,
                                            help="the instance-id, e.g i-1223456")
    parser.add_argument("-d", "--device", dest="device", required=True,
                                            help="the device, e.g /dev/sdj")
    parser.add_argument("-f", "--force", action="store_true", dest="force", default=False,
                                            help="whether to force the detachment if the os isn't responding. VERY DANGEROUS")
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

def get_volume(conn, volumeid):
    return conn.get_all_volumes(volumeid)[0]

def detach_volume(conn,volume, instance, device, force):
    conn.detach_volume(volume.id, instance.id, device)

    if volume.status != 'available':
        logging.info("Waiting for volume %s to be detached", volume.id)

        counter = 0 
        while volume.status != 'available' and counter < 10:
            volume.update()
            time.sleep(1)
            counter = counter + 1

        if volume.status != 'available':
            logging.error("Failed to detach volume %s", volume.id)
        else:
            logging.info("Succeeded in detaching volume %s", volume.id)
            return

    else:
        logging.info("Succeeded in detaching volume %s", volume.id)
        return

    if volume.status != 'available' and force:
        logging.info("Volume %s still detaching, trying to force the detachment", volume.id)
        conn.detach_volume(volume.id, instance.id, device, force)

        counter = 0
        while volume.status != 'available' and counter < 10:
            volume.update()
            time.sleep(1)
            counter = counter + 1
        
        volume.update()

        if volume.status != 'available':
            instance.update()
            logging.error("Failed to force detachment of volume %s currently in state %s", volume.id, instance.block_device_mapping[device].status)
            return 1
        else:
            logging.info("Succeeded in detaching volume %s", volume.id)
            return
    
    elif volume.status != 'available':
        instance.update()
        logging.info("Volume %s in state %s, not forcing detachment, check if the volume is still mounted on the instance", volume.id, instance.block_device_mapping[device].status)
        return 1
    else:
        logging.info("Succeeded in detaching volume %s", volume.id)
        return

def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 
    conn = get_conn(accesskey, secretkey)
    instance = get_instance(conn, args.instanceid)
    volume = get_volume(conn, args.volumeid)
    retval = detach_volume(conn, volume, instance, args.device, args.force)
    sys.exit(retval)

if __name__ == '__main__':
    run()
