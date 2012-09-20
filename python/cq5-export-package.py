#!/usr/bin/env python

import boto
import argparse, os, sys, string, random
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
        '-e',
        '--exclude',
        dest="exclude",
        required=False,
        help='A filter definition to exclude nodes under the path specified',
    )
    parser.add_argument(
        '-i',
        '--include',
        dest="include",
        required=False,
        help='A filter definition to include nodes under the path specified',
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
        default='account_backup',
        help='The name of the cq5 package to create.',
    )
    parser.add_argument(
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
    tmpfile = '%s/%s-%s-%s.zip' % (args.tmpdir, args.hostname, args.name, timestamp)

    create_package = ("curl -f -u admin:%s -X POST http://%s:%s/crx/packmgr/service/.json/etc/packages/%s.zip?cmd=create -d packageName=%s -d groupName=%s" %
        (args.password, args.hostname, args.port, args.name, args.name, args.group) )

    update_package = ("curl -f -u admin:%s -F'path=/etc/packages/%s/%s.zip' -F'filter=[{\"root\":\"%s\",\"rules\":[{\"modifier\":\"exclude\",\"pattern\":\"%s\"}]}]' http://%s:%s/crx/packmgr/update.jsp" %
        (args.password, args.group, args.name, args.path, args.exclude, args.hostname, args.port) )

    build_package = ("curl -f -u admin:%s -F'name=%s' -F'group=%s' -F'cmd=build' http://%s:%s/crx/packmgr/service.jsp" %
        (args.password, args.name, args.group, args.hostname, args.port) )

    download_package = ("curl -f -u admin:%s -o %s http://%s:%s/etc/packages/%s/%s.zip" %
        (args.password, tmpfile, args.hostname, args.port, args.group, args.name) )

    try:
        logging.info("Creating cq package %s" % args.name)
        logging.debug("Executing: %s" % repr(create_package))
        subprocess.check_output(create_package, stderr=subprocess.STDOUT, shell=True)
        logging.info("Completed package creation of %s" % args.name)
        logging.info("Updating package %s with filter %s and excludes %s" % (args.name, args.path, args.exclude) )
        logging.debug("Executing: %s" % repr(update_package))
        subprocess.check_output(update_package, stderr=subprocess.STDOUT, shell=True)
        logging.info("Completed package update")
        logging.info("Building package %s" % args.name)
        logging.debug("Executing: %s" % repr(build_package))
        subprocess.check_output(build_package, stderr=subprocess.STDOUT, shell=True)
        logging.info("Completed package build")
        logging.info("Downloading package /etc/packages/%s.zip to %s" % (args.name, tmpfile) )
        logging.debug("Executing: %s" % repr(download_package))
        subprocess.check_output(download_package, stderr=subprocess.STDOUT, shell=True)
        logging.info("Completed download")
    except subprocess.CalledProcessError, e:
        logging.error("%s" % e.output.rstrip('\n'))
        logging.error("cq5 export: Execution failed with status: %s" % e.returncode)
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
    logging.debug("Removing temporary file %s" % tmpfile)
    os.remove(tmpfile)

    return

def run():
    args = get_args()
    args.group = 'backups'
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level) 
    (accesskey, secretkey) = get_creds()
    conn = get_conn(accesskey, secretkey)
    to_s3(conn, args)

    sys.exit()

if __name__ == '__main__':
    run()
