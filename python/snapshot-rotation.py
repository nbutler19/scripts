#!/usr/bin/env python

import boto
import argparse
import time, sys, logging, datetime

def get_creds():

    # By default empty, boto will look for environment variables
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    ACCESSKEY=''
    SECRETKEY=''

    return ACCESSKEY, SECRETKEY

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--log",
        dest="loglevel",
        default='ERROR',
        choices=['CRITICAL','FATAL','ERROR','WARN','WARNING','INFO','DEBUG','NOTSET'],
        help="the loglevel sets the amount of output you want"
    )
    return parser.parse_args()

def get_numeric_loglevel(loglevel):
    return getattr(logging, loglevel.upper())

def get_conn(accesskey, secretkey):
    if accesskey and secretkey:
        return boto.connect_ec2(accesskey,secretkey)
    else:
        return boto.connect_ec2()

def convert_iso_to_datetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%f")

def expired(current_time, expires_time):
    delta = expires_time - current_time
    if delta.total_seconds() > 0:
      return False
    else:
      return True

def get_snapshots(conn):
    return conn.get_all_snapshots(owner='self')

def purge_snapshots(snapshots):
    for snapshot in snapshots:
      now = datetime.datetime.now()
      try:
        iso_time = snapshot.tags['Expires']
        expires = convert_iso_to_datetime(iso_time)
        if expired(now, expires):
          # do someting
          logging.info("Purging expired snapshot %s %s" % (snapshot.id, iso_time)) 
          if snapshot.delete():
            logging.info("SUCCESS")
          else:
            logging.info("FAILURE")
        else:
          logging.debug("%s not expired yet: %s" % (snapshot.id, iso_time))
      except KeyError:
        logging.debug("No Expires for %s %s...skipping" % (snapshot.id, snapshot.description))
        next

def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 
    conn = get_conn(accesskey, secretkey)
    snapshots = get_snapshots(conn)
    purge_snapshots(snapshots)

if __name__ == '__main__':
    run()
