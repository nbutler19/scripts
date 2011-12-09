#!/usr/bin/python

import sys
import boto
import argparse


parser = argparse.ArgumentParser(description="Manages Tags in EC2")

ec2_filter_group = parser.add_mutually_exclusive_group(required=False)
ec2_filter_group.add_argument("--filter", metavar="KEY=VALUE", dest="filter",
                  help="Filter on tag name in the format KEY=VALUE")
ec2_filter_group.add_argument("--filter-id", dest="filter_id",
                  help="Filter specifically on an EC2 id")

parser.add_argument("-t", "--type", dest="type", choices=["volume", "instance", "snapshot", "ami"], required=True)
parser.add_argument("-a", "--action", dest="action", choices=["add", "remove", "print"], required=True)
parser.add_argument("--tags", metavar="KEY=VALUE", nargs="+", dest="tags", default=["Name=Value"])
parser.add_argument("-d", "--dry-run", action="store_true", dest="dryrun", default=False,
                  help="don't do anything")
parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")

args = parser.parse_args()

#print args

def validate_filter(filter):
  try:
    (t1, t2) = filter.split('=')
  except ValueError:
    return False
  
  return True

def get_ec2_conn():
  conn = boto.connect_ec2()
  return conn

def get_reservations(conn):
  res_set = conn.get_all_instances()
  return res_set

def does_tag_exist(filter, tags):
  (key, value) = filter.split('=')
  try:
    if tags[key] and tags[key] == value:
      return True
      print "Tag found in %r" % tags
    else:
      return False
  except KeyError:
    return False

def get_instances(reservation_set, filter, instanceid):
  reservations = reservation_set
  instances = []
  if filter:
    for res in reservations:
      inst = res.instances[0]
      tags = inst.tags
      if does_tag_exist(filter, tags):
        #print "Instance found!: %r" % inst
        instances.append(inst)
      else:
        pass
        #print "INFO: %s is not tagged with %s" % (inst, filter)
  elif instanceid:
    for res in reservations:
      inst = res.instances[0]
      if instanceid == inst.id:
        #print "Instance found!: %r" % inst
        instances.append(inst)
      else:
        pass
        #print "DEBUG: Instance with id: %s doesn't match %s" % (inst.id, instanceid)
  else:
    for res in reservations:
      instances.append(res.instances[0])

  return instances

def get_volumes():
  #TODO
  pass

def get_snapshots():
  #TODO
  pass

def get_amis():
  #TODO
  pass

def remove_tags(ec2_object, tags, dryrun):
  if dryrun:
    print "Performing dryrun of action"
    for k in tags:
      print "Removing Tag: { %s : %s } from %s" % (k, tags[k], ec2_object.id)
      print "ec2_object.remove_tag(k, tags[k])"
  else:
    for k in tags:
      print "Removing Tag: { %s : %s } from %s" % (k, tags[k], ec2_object.id)
      ec2_object.remove_tag(k, tags[k])

def add_tags(ec2_object, tags, dryrun):
  if dryrun:
    print "Performing dryrun of action"
    for k in tags:
      print "Adding Tag: { %s : %s } to %s" % (k, tags[k], ec2_object.id) 
      print "ec2_object.add_tag(k, tags[k])"
  else:
    for k in tags:
      print "Adding Tag: { %s : %s } to %s" % (k, tags[k], ec2_object.id) 
      ec2_object.add_tag(k, tags[k])

def print_tags(ec2_object):
  print "Instance %s has the following tags: %r" % (ec2_object.id, ec2_object.tags)

def swap(ec2_objects, tag1, tag2, dryrun):
  #TODO
  pass

def do_action(ec2_objects, tags, action, dryrun):
    for obj in ec2_objects:
      #print "DEBUG: Tags are %r" % tags
      if action == "add":
        add_tags(obj, tags, dryrun)
      elif action == "remove": 
        remove_tags(obj, tags, dryrun)  
      else:
        print_tags(obj)

def get_tags(tags):
  tag_dict = {}
  for tag in tags:
    (tagname, tagval) = tag.split('=')
    tag_dict[tagname] = tagval

  return tag_dict

def run():
  conn = get_ec2_conn()
  if args.type == "instance":
    reservations = get_reservations(conn)
    if args.filter and validate_filter(args.filter):
      print "Trying to locate instances marked with filter: %s" % args.filter
      instances = get_instances(reservations, args.filter, args.filter_id)
      tags = get_tags(args.tags)
      res = do_action(instances, tags, args.action, args.dryrun)
    elif args.filter_id:
      print "Trying to locate instance matching id: %s" % args.filter_id
      instances = get_instances(reservations, args.filter, args.filter_id)
      tags = get_tags(args.tags)
      res = do_action(instances, tags, args.action, args.dryrun)
    elif not args.filter and not args.filter_id:
      print "No filter, acting on all instances"
      instances = get_instances(reservations, args.filter, args.filter_id)
      tags = get_tags(args.tags)
      res = do_action(instances, tags, args.action, args.dryrun)
    else:
      print "ERROR: Invalid options" + "\n"
      parser.print_usage()

  elif args.type == "volume":
    #TODO
    pass
  elif args.type == "snapshot":
    #TODO
    pass
  elif args.type == "ami":
    #TODO
    pass
  else:
    #TODO
    pass
   

if __name__ == '__main__':
  run()
