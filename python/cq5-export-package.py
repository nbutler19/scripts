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
    parser.add_argument(
        '-p',
        '--path',
        dest='path',
        required=True,
        help='The CQ5 Path, /content/something, /var/tmp, /home/users etc',
    )
    parser.add_argument(
        '--host',
        dest='hostname',
        default='localhost',
        help='The CQ5 hostname to connect to',
    )
    parser.add_argument(
        '--port',
        dest='port',
        default='4502',
        help='The CQ5 port to connect to',
    )
    parser.add_argument(
        '-u',
        '--user',
        dest='username',
        default='admin',
        help='The CQ5 username to connect with',
    )
    parser.add_argument(
        '--pass',
        dest='password',
        default='admin',
        help='The CQ5 password to connect with',
    )
    parser.add_argument(
        '--tmpdir',
        dest='tmpdir',
        default='/tmp',
        help='The location to store the temporary backup file',
    )
    parser.add_argument(
        '-n',
        '--name',
        dest='name',
        default=socket.gethostname(),
        help=
        """
        The name of the cq5 instance. Defaults to the current
        host.
        """
    )
    parser.add_argument(
        '-e',
        '--environment',
        dest='environ',
        required=True,
        help=
        """
        The name of the server environment.
        """
    )
    parser.add_argument(
        '-b',
        '--bucket',
        dest='bucket',
        default='my-bucket',
        help='The S3 bucket name, e.g my-backups',
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

def get_conn(accesskey, secretkey):
    if accesskey and secretkey:
        return boto.connect_s3(accesskey,secretkey)
    else:
        return boto.connect_s3()

def export(args):
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    safe_path = args.path.replace('/','_')
    tmpfile = '%s/%s-%s-%s.zip' % (args.tmpdir, args.name, safe_path, timestamp)

    command = ("crx export --output_file %s %s --host %s --port %s --username %s --password %s"  % 
        (tmpfile,
        args.path,
        args.hostname,
        args.port,
        args.username,
        args.password)
    )

    logging.debug("Executing: %s" % command)

    try:
        logging.info("Starting cq backup of %s" % args.path)
        subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        logging.info("Completed cq backup of %s" % args.path)
    except subprocess.CalledProcessError, e:
        logging.error("%s" % e.output.rstrip('\n'))
        logging.error("crx export: Execution failed with status: %s" % e.returncode)
        sys.exit(e.returncode)

    return tmpfile 

def to_s3(conn, args):
    tmpfile = export(args)

    key_name = "cq5/" + args.environ + "/" + tmpfile.split('/')[-1]
    bucket = conn.get_bucket(args.bucket)
    key = bucket.new_key(key_name=key_name)
    with open(tmpfile, 'r') as f:
           key.set_contents_from_file(f,md5=key.compute_md5(f))

    logging.info("Uploaded backup to s3:///%s/%s" % (args.bucket, key.name))
#    logging.info("Uploaded backup to s3:///%s/%s" % (args.bucket, key_name))
    logging.debug("Removing temporary file %s" % tmpfile)
    os.remove(tmpfile)

    return

def run():
    args = get_args()
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 
    (accesskey, secretkey) = get_creds()
    conn = get_conn(accesskey, secretkey)
    to_s3(conn, args)

    sys.exit()

if __name__ == '__main__':
    run()
