#!/usr/bin/env python

import boto
import argparse, sys
import simplejson

def get_creds():

    # By default empty, boto will look for environment variables
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    ACCESSKEY=''
    SECRETKEY=''

    return ACCESSKEY, SECRETKEY

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--table", dest="table", required=True)
    parser.add_argument("-k", "--key", dest="hashkey", required=False)
    parser.add_argument("-r", "--range", dest="rangekey", required=False)
    parser.add_argument("-f", "--file", dest="filename", required=False)

    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--put", dest="action_put", action="store_true")
    action.add_argument("--get", dest="action_get", action="store_true")
    action.add_argument("--del", dest="action_del", action="store_true")

#    parser.add_argument("-a", "--action", dest="action", choices=["put", "del", "get"],
#        required=True, help="the action to perform, delete or add a table item by key")
#    parser.add_argument("-f", "--file", dest="filename", required=False,
#        help="the filename to import, must be valid json")
#    parser.add_argument("-t", "--table", dest="table", required=True,
#        help="the dynamo table to import to")
#    parser.add_argument("-k", "--key", dest="hashkey", required=True,
#        help="the dynamo hash key, needs to exist in the json file")
#    parser.add_argument("-r", "--range", dest="rangekey", required=False,
#        help="the dynamo hash range, necessary if you want to query dynamo")
#    parser.add_argument("-d", "--data", dest="data_attrib", required=False,
#        help="the dynamo data item attributes, must be a dict"
#    parser.add_argument("-u", "--update", dest="update", action="store_true", required=False,
#        help="whether to update an item if it already exists")
    return parser.parse_args()

def get_conn(accesskey, secretkey):
    if accesskey and secretkey:
        return boto.connect_dynamodb(accesskey, secretkey)
    else:
        return boto.connect_dynamodb()

def get_table(conn, table):
    return conn.get_table(table)

def load_json(file):
    return simplejson.load(file)

def read_in(filename):
    if filename:
        with open(filename, 'r') as f:
            input = load_json(f)
    
        return input
    else:
        input = load_json(sys.stdin)
        return input

def write_out(filename, raw):
    if filename:
        with open(filename, 'w') as f:
            f.write(raw)
    else:
        sys.stdout.write(str(raw) + "\n")

def validate_dict(key, dict):
    if key in dict:
        return True
    else:
        print "Key: %r not found" % key
        sys.exit(1)

def parse_json(hashkey, rangekey, jdict):
    if rangekey:
        validate_dict(hashkey, jdict)
        validate_dict(rangekey, jdict)
        item_key = jdict[hashkey]; del jdict[hashkey]
        item_range = jdict[rangekey]; del jdict[rangekey]
        item_data = jdict
    else:
        validate_dict(hashkey, jdict)
        item_key = jdict[hashkey]; del jdict[hashkey]
        item_range = False
        item_data = jdict

    return item_key, item_range, item_data

def convert_lists_to_sets(jdict):
    newdict = dict()
    for key in jdict.iterkeys():
        if isinstance(jdict[key], list):
            newdict[key] = set(jdict[key])
        else:
            newdict[key] = jdict[key]

    return newdict

def convert_sets_to_lists(jdict):
    newdict = dict()
    for key in jdict.iterkeys():
        if isinstance(jdict[key], set):
            newdict[key] = list(jdict[key])
        else:
            newdict[key] = jdict[key]

    return newdict 

def put_data(table, hashkey, rangekey, data):
    if isinstance(data, dict):
        data_list = [ data ]
    else:
        data_list = data

    for item in data_list:
        (item_key, item_range, item_data) = parse_json(hashkey, rangekey, item)
        converted_data = convert_lists_to_sets(item_data)
    
        if item_range:
            item = table.new_item(
                    hash_key = item_key, 
                    range_key = item_range,
                    attrs = converted_data
                    )
            item.put()
        else:
            item = table.new_item(hash_key = item_key, attrs = converted_data)
            item.put()

def del_data(table, hashkey, rangekey):
    item = get_data(table, hashkey, rangekey)
    item.delete()

def get_data(table, item_key, item_range):
    if item_range:
        item = table.get_item(
                hash_key = item_key, 
                range_key = item_range,
                consistent_read = True
                )
    else:
        item = table.get_item(hash_key = item_key, consistent_read = True)

    return item


def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    conn = get_conn(accesskey, secretkey)
    table = get_table(conn, args.table)

    if args.action_put:
        data = read_in(args.filename)
        put_data(table, args.hashkey, args.rangekey, data)
    elif args.action_del:
        del_data(table, args.hashkey, args.rangekey)
    elif args.action_get:
        item = get_data(table, args.hashkey, args.rangekey)
        write_out(args.filename, simplejson.dumps(convert_sets_to_lists(item), indent=True))
    else:
        print "This will never be executed"

if __name__ == '__main__':
    run()
