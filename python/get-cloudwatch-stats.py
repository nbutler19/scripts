#!/usr/bin/python

import boto
import argparse
import datetime
import logging

def get_creds():
    """
    By default empty, boto will look for environment variables
    AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    """
    ACCESSKEY=''
    SECRETKEY=''

    return ACCESSKEY, SECRETKEY

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--namespace", dest="namespace", 
            choices=["AWS/EC2", "AWS/RDS", "AWS/EBS", "AWS/ELB", "AWS/SNS", "AWS/SQS"], required=True)
    parser.add_argument("-m", "--metric", dest="metric", required=True,
            help="e.g. --metric RequestCount or --metric Latency")
    parser.add_argument("-d", "--dimensions", dest="dimensions", required=True,
            help="e.g. LoadBalancerName=www-prod or DBInstanceIdentifier=zabbix")
    parser.add_argument("-s", "--statistics", dest="statistics", 
            choices=["Average", "Sum", "SampleCount", "Maximum", "Minimum"], required=True)
    parser.add_argument("-l", "--log", dest="loglevel", default='ERROR',
            choices=['CRITICAL','FATAL','ERROR','WARN','WARNING','INFO','DEBUG','NOTSET'],
            help="the loglevel sets the amount of output you want",)
    return parser.parse_args()

def get_numeric_loglevel(loglevel):
    return getattr(logging, loglevel.upper())

def get_conn(accesskey, secretkey):
    if accesskey and secretkey:
        return boto.connect_cloudwatch(accesskey, secretkey)
    else:
        return boto.connect_cloudwatch()


def format_dimension_as_dict(dimension):
    dim = {}
    (key, value) = dimension.split('=')
    dim[key] = value
    return dim


def get_start_end_times():
    end = datetime.datetime.now()
    start = end - datetime.timedelta(minutes=1)
    return start, end


def get_metric_statistics(conn, start, end, metric, namespace, statistic, dimension):
    return conn.get_metric_statistics("60", start, end, metric, namespace, statistic, dimension)


def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    numeric_level = get_numeric_loglevel(args.loglevel)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=numeric_level)
    conn = get_conn(accesskey,secretkey)
    (start, end) = get_start_end_times()
    dimension = format_dimension_as_dict(args.dimensions)

    stats = get_metric_statistics(conn, start, end, args.metric, args.namespace, args.statistics, dimension)
    # Cloudwatch sometimes returns in scientific notation, Zabbix can't handle scientific notation :(
    if stats:
        print '%.15f' % stats[0][args.statistics]
    else:
        raise Exception('Invalid metric or dimension')

if __name__ == '__main__':
    run()

