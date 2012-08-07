#!/usr/bin/env python

import boto
import argparse, os, string, random
import subprocess, time, datetime, sys, logging, socket, re
from dateutil.relativedelta import relativedelta
from dateutil import tz

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
    parser_file = subparsers.add_parser(
        'file',
        help='Backup to a file'
    )
    parser_file.add_argument(
        '-f',
        '--filename',
        dest='filename',
        required=False,
        help='The filename to backup to, e.g. /d0/backups/foo.sql',
    )
    parser_s3 = subparsers.add_parser(
        's3',
        help=
        """
        Backup to S3
        """
    )
    parser_s3.add_argument(
        '-b',
        '--bucket',
        dest='bucket',
        required=True,
        help='The AWS S3 bucketname, e.g my-bucket',
    )
    parser_s3.add_argument(
        '-p',
        '--path',
        dest='path',
        required=False,
        help='The AWS S3 pathname, e.g. DB/backups/',
    )
    parser_s3.add_argument(
        '-f',
        '--filename',
        dest='filename',
        required=False,
        help='The AWS S3 object name, e.g. test-backup.sql.gz',
    )
    parser.add_argument(
        '--host',
        dest='hostname',
        default='localhost',
        help='The MySQL hostname to connect to',
    )
    parser.add_argument(
        '--port',
        dest='port',
        default='3306',
        help='The MySQL port to connect to',
    )
    parser.add_argument(
        '-u',
        '--username',
        dest='username',
        default='root',
        help='The MySQL username to connect with',
    )
    parser.add_argument(
        '-p',
        '--password',
        dest='password',
        required=False,
        help='The MySQL password to connect with',
    )
    parser.add_argument(
        '-d',
        '--database',
        dest='database',
        default='test',
        help='The MySQL database to backup',
    )
    parser.add_argument(
        '-c',
        '--compress',
        dest='compress',
        action='store_true',
        help=
        """
        Whether to compress the backup.
        """
    )
    parser.add_argument(
        '-t',
        '--ttl',
        dest='ttl',
        default='2 months',
        help=
        """
        The time that the backup should stick around.
        ONLY FOR S3 BACKUPS!!
        The following are valid:
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
        1y,
        2 year(s),
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
                    'y',
                    'year',
                    'years',
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
      'y' : 'years',
      'year' : 'years',
      'years' : 'years',
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
    now = datetime.datetime.utcnow()
    expiration = now + relativedelta(**ttl)

    return expiration

def convert_to_utf8(string):
  return string.encode('utf8')

def get_conn(accesskey, secretkey):
    if accesskey and secretkey:
        return boto.connect_s3(accesskey,secretkey)
    else:
        return boto.connect_s3()

def get_meta_data(conn, bucket, key, ttl):
  ttl = ttl.strftime('%Y-%m-%dT%H:%M:%S%z')
  return ttl

def generate_id(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def get_mysqldump(args):
    filename = '/tmp/%s-%s.sql' % (args.database, generate_id())

    if args.password:
        mysql_command = ("mysqldump -h %s -P %s -u%s -p%s %s > %s" % 
            (args.hostname,
            args.port,
            args.username,
            args.password,
            args.database,
            filename)
        )
    else:
        mysql_command = ("mysqldump -h %s -P %s -u%s %s > %s" %
            (args.hostname,
            args.port,
            args.username,
            args.database,
            filename)
        )

    logging.debug("Executing: %s" % mysql_command)

    try:
        subprocess.check_output(mysql_command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError, e:
        logging.error("%s" % e.output.rstrip('\n'))
        logging.error("mysqldump: Execution failed with status: %s" % e.returncode)
        sys.exit(e.returncode)

    if args.compress:
        try:
            subprocess.check_output('gzip %s' % filename, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError, e:
            logging.error("%s" % e.output.rstrip('\n'))
            logging.error("mysqldump: Execution failed with status: %s" % e.returncode)
            sys.exit(e.returncode)

        return filename + '.gz'
    else:
        return filename

def dump_to_file(args):
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    dumpfile = get_mysqldump(args)
    
    if args.filename:
        filename = args.filename
    else:
        filename = '/tmp/%s-%s.sql' % (args.database, timestamp)

    if args.compress and not args.filename:
        filename = filename + '.gz'
      
    if not os.path.exists(os.path.dirname(filename)):
        logging.debug("Making parent directories of filename %s" % os.path.dirname(filename))
        os.makedirs(os.path.dirname(filename))

    logging.debug("Renaming temporary file %s to backup file %s" % (dumpfile, filename))
    os.rename(dumpfile, filename)

    logging.info("Dumped database %s to %s" % (args.database, filename))
    return filename

def dump_to_s3(conn, args):
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    dumpfile = get_mysqldump(args)
    ttl = convert_ttl(args.ttl)
    logging.debug("Expiration determined as: %s" % ttl.strftime('%Y-%m-%dT%H:%M:%SZ'))

    if args.path:
        path = args.path
    else:
        path = '/'

    if args.filename:
        filename = args.filename
    else:
        filename = '%s-%s.sql' % (args.database, timestamp)

    if args.compress and not args.filename:
        filename = filename + '.gz'

    key_name = path + '/' + filename
    bucket = conn.get_bucket(args.bucket)
    key = bucket.new_key(key_name=key_name)
    with open(dumpfile, 'r') as f:
           key.set_contents_from_file(f,md5=key.compute_md5(f))

    logging.info("Put file %s to s3:///%s/%s" % (dumpfile, args.bucket, key.name))
    logging.debug("Removing temporary file %s" % dumpfile)
    os.remove(dumpfile)

    return

def run():
    args = get_args()
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 

    if args.subparser_name == 'file':
      dump_to_file(args)

    if args.subparser_name == 's3':
      (accesskey, secretkey) = get_creds()
      conn = get_conn(accesskey, secretkey)
      dump_to_s3(conn, args)

    sys.exit()

if __name__ == '__main__':
    run()
