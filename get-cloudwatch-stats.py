#!/usr/bin/python

import boto
import argparse
import datetime

def get_creds():

  # By default empty, boto will look for environment variables
  # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
  ACCESSKEY=''
  SECRETKEY=''

  if ACCESSKEY and SECRETKEY:
    return ACCESSKEY, SECRETKEY
  else:
    return None, None

def get_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("-n", "--namespace", dest="namespace", required=True)
  parser.add_argument("-m", "--metric", dest="metric", required=True)
  parser.add_argument("-d", "--dimensions", dest="dimensions", required=True)
  parser.add_argument("-s", "--statistics", dest="statistics", 
                      choices=["Average", "Sum", "SampleCount", "Maximum", "Minimum"], required=True)
  return parser.parse_args()

def get_conn(accesskey,secretkey):
  if accesskey and secretkey:
    return boto.connect_cloudwatch(accesskey,secretkey)
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
  conn = get_conn(accesskey,secretkey)
  (start, end) = get_start_end_times()
  dimension = format_dimension_as_dict(args.dimensions)
  stats = get_metric_statistics(conn, start, end, args.metric, args.namespace, args.statistics, dimension)
  # Cloudwatch sometimes returns in scientific notation, Zabbix can't handle scientific notation :(
  print '%.15f' % stats[0][args.statistics]

if __name__ == '__main__':
  run()
