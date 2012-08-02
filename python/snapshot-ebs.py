#!/usr/bin/env python

import boto
import argparse
import datetime, sys, logging, socket, re
from dateutil.relativedelta import relativedelta

def get_creds():

    # By default empty, boto will look for environment variables
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    ACCESSKEY=''
    SECRETKEY=''

    return ACCESSKEY, SECRETKEY

def get_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest='subparser_name',
        help='sub-command help'
    )
    parser_device  = subparsers.add_parser(
        'device',
        help='Snapshot a specific device'
    )
    parser_device.add_argument(
        '-d',
        '--device',
        dest='device',
        required=True,
        help='The filesystem device name, e.g /dev/sdj',
    )
    parser_device.add_argument(
        '-i',
        '--instance-id',
        dest='instanceid',
        required=True,
        help='The AWS InstanceId, e.g i-1223456',
    )
    parser_instance = subparsers.add_parser(
        'instance',
        help=
        """
        Snapshot all attached ebs volumes on a specific instance
        """
    )
    parser_instance.add_argument(
        '-i',
        '--instance-id',
        dest='instanceid',
        required=True,
        help='The AWS InstanceId, e.g i-1223456',
    )
    parser_volume = subparsers.add_parser(
        'volume',
        help='Snapshot a specific volume',
    )
    parser_volume.add_argument(
        '-v',
        '--volumeid',
        dest='volumeid',
        required=True,
        help='The AWS VolumeId, e.g. vol-1223456',
    )
    parser.add_argument(
        '-n',
        '--name',
        dest='name',
        default=socket.gethostname(),
        help=
        """
        The name of the ebs volume or instance. Defaults to the current
        host.
        """
    )
    parser.add_argument(
        '-t',
        '--ttl',
        dest='ttl',
        default='2 weeks',
        help=
        """
        The time that the snapshot should stick around. The following are valid:
        1s,
        1 second(s),
        5M,
        5 minute(s),
        1H,
        2 hour(s),
        1d,
        2 day(s),
        1w,
        1 week(s),
        2m,
        2 months(s),
        """
    )
    parser.add_argument(
        '-l',
        '--log',
        dest='loglevel',
        default='ERROR',
        choices=['CRITICAL','FATAL','ERROR','WARN','WARNING','INFO','DEBUG','NOTSET'],
        help="the loglevel sets the amount of output you want",
    )
    return parser.parse_args()

def get_numeric_loglevel(loglevel):
    return getattr(logging, loglevel.upper())

def validate_period(period):
    valid_names = [ 's',
                    'second',
                    'seconds',
                    'M',
                    'minute',
                    'minutes',
                    'H',
                    'hour',
                    'hours',
                    'd',
                    'day',
                    'days',
                    'w',
                    'week',
                    'weeks',
                    'm',
                    'month',
                    'months',
                  ]

    for name in valid_names:
      if len(period) > 1:
        if name.lower() == period.lower():
          return
      else:
        if name == period:
          return

    logging.error("Invalid time unit specified: %s" % period)
    sys.exit(1)

def normalize_period(period):
    normal_period = {
      's' : 'seconds',
      'second' : 'seconds',
      'seconds' : 'seconds',
      'M' : 'minutes',
      'minute' : 'minutes',
      'minutes' : 'minutes',
      'H' : 'hours',
      'hour' : 'hours',
      'hours' : 'hours',
      'd' : 'days',
      'day' : 'days',
      'days' : 'days',
      'w' : 'weeks',
      'week' : 'weeks',
      'weeks' : 'weeks',
      'm' : 'months',
      'month' : 'months',
      'months' : 'months',
    }

    if len(period) > 1:
      return normal_period[period.lower()]
    else:
      return normal_period[period]

def convert_ttl(ttl):
    r = re.compile('(\d+)\s*(.*)')
    m = r.match(ttl)

    num = m.group(1)
    period = m.group(2)

    validate_period(period)
    period = normalize_period(period)

    ttl = { period : int(num) }
    now = datetime.datetime.now()
    expiration = now + relativedelta(**ttl)

    return expiration

def get_conn(accesskey, secretkey):
    if accesskey and secretkey:
        return boto.connect_ec2(accesskey,secretkey)
    else:
        return boto.connect_ec2()

def get_instance(conn, instanceid):
    return conn.get_all_instances(instanceid)[0].instances[0]

def get_volume(conn, volumeid):
    return conn.get_all_volumes(volumeid)[0]

def get_volumes_attached_to_instance(conn, instance):
    volumes = []
    block_devices = instance.block_device_mapping

    for dev, vol in block_devices.items():
      if isinstance(vol.volume_id, unicode):
        volumeid = vol.volume_id.encode('utf8')
      else:
        volumeid = vol.volume_id

      volume = get_volume(conn, volumeid)
      volumes.append(volume)

    return volumes

def create_snapshot(conn, volume, name, ttl):
  dev = volume.attach_data.device

  if dev is None:
    dev = 'None'

  ttl = ttl.isoformat()
  desc = "%s-snap-%s-%s" % (name, volume.id, dev)

  print dev
  print ttl
  print desc
  
def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 
    conn = get_conn(accesskey, secretkey)

    ttl = convert_ttl(args.ttl)

    logging.debug("Expiration determined to be: %s" % ttl.isoformat())

    if args.subparser_name == 'instance':
      instance = get_instance(conn, args.instanceid)
      volumes = get_volumes_attached_to_instance(conn, instance)
      for volume in volumes:
        retval = create_snapshot(conn, volume, args.name, ttl)
#        print retval

    if args.subparser_name == 'device':
      instance = get_instance(conn, args.instanceid)
      volumes = get_volumes_attached_to_instance(conn, instance)

      for volume in volumes:
        if volume.attach_data.device == args.device:
          retval = create_snapshot(conn, volume, args.name, ttl)
#          print retval
      
    if args.subparser_name == 'volume':
      volume = get_volume(conn, args.volumeid)
      retval = create_snapshot(conn, volume, args.name, ttl)
#      print retval

    sys.exit()

if __name__ == '__main__':
    run()
