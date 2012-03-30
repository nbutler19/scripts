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

def get_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
                    dest='subparser_name',
                    help='sub-command help'
                    )
    
    parser_put = subparsers.add_parser(
                    'put',
                    help='For inserting/updating items'
                    )
    parser_put.add_argument(
                    '-d',
                    '--domain',
                    dest='domain',
                    required=True,
                    help=
                    """
                    The domain is the simpledb table to access
                    """
                    )
    parser_put.add_argument(
                    '-f',
                    '--file',
                    dest='filename',
                    required=False,
                    help=
                    """
                    The file to read item data from. If no file is specified
                    stdin is read from. The structure of this file must be
                    valid json and must be in the form:



                    { "<item_name>" : "foo", 
                      "<attribute_name>" : { "attr1" : "val1", ... }
                    }
                    """
                    )
    parser_put.add_argument(
                    '-n',
                    '--item-name',
                    dest='item_name',
                    required=False,
                    default='name', 
                    help=
                    """
                    The name to use as the simpledb item name. The default
                    is 'name'
                    """
                    )
    parser_put.add_argument(
                    '-a',
                    '--attr-name',
                    dest='attribute_name',
                    required=False,
                    default='attributes',
                    help=
                    """
                    The name to use as the simpledb attribute name. The default
                    is 'attributes'
                    """
                    )

    parser_del = subparsers.add_parser(
                    'del',
                    help='For deleting items/attributes'
                    )
    parser_del.add_argument(
                    '-d',
                    '--domain',
                    dest='domain',
                    required=True,
                    help=
                    """
                    The domain is the simpledb table to access
                    """
                    )
    parser_del.add_argument(
                    '-n',
                    '--item-name',
                    dest='item_name',
                    required=False,
                    help=
                    """
                    The name of the simpledb item name.
                    """
                    )
    parser_del.add_argument(
                    '-q',
                    '--query',
                    dest='query', 
                    required=False,
                    help=
                    """
                    The query to use for searching, e.g. id=foo
                    """
                    )
    parser_del.add_argument(
                    '-f',
                    '--fuzzy',
                    dest='fuzzy',
                    action='store_true',
                    required=False, 
                    help=
                    """
                    A non-exact search, equivalent to id=*foo*
                    """)
    parser_del.add_argument(
                    '-a',
                    '--attributes',
                    dest='attributes',
                    nargs='+',
                    required=False,
                    help=
                    """
                    The attribute to delete from matched items, the default is 
                    to delete all found items
                    """
                    )


    parser_get = subparsers.add_parser(
                    'get',
                    help='For retrieving items/attributes'
                    )
    parser_get.add_argument(
                    '-d',
                    '--domain',
                    dest='domain',
                    required=True,
                    help=
                    """
                    The domain is the simpledb table to access
                    """
                    )
    parser_get.add_argument(
                    '-n',
                    '--item-name',
                    dest='item_name',
                    required=False,
                    help=
                    """
                    The name of the simpledb item name.
                    """
                    )
    parser_get.add_argument(
                    '-f',
                    '--file',
                    dest='filename',
                    required=False,
                    help=
                    """
                    The file to write item data to
                    """
                    )
    parser_get.add_argument(
                    '-q',
                    '--query',
                    dest='query',
                    required=False,
                    help=
                    """
                    The query to use for searching, e.g. id=foo
                    """
                    )
    parser_get.add_argument(
                    '--fuzzy',
                    dest='fuzzy',
                    action='store_true',
                    required=False, 
                    help=
                    """
                    A non-exact search, equivalent to id=*foo*
                    """
                    )
    parser_get.add_argument(
                    '-a', '--attributes',
                    dest='attributes',
                    nargs='+',
                    required=False,
                    help=
                    """
                    The attribute to return from a search, the default is 
                    to return all attributes
                    """
                    )

    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()

def get_conn(accesskey, secretkey):
    if accesskey and secretkey:
        return boto.connect_sdb(accesskey, secretkey)
    else:
        return boto.connect_sdb()

def get_domain(conn, domain):
    return conn.get_domain(domain)

def confirm(message="Are you sure?"):
    choice = raw_input("%s [yN] " % message)
    return choice and len(choice) > 0 and choice[0].lower() == "y"

def validate_query(query):
    try:
        (attr, val) = query.split('=')
    except ValueError:
        print "Invalid query parameter"
        sys.exit(1)
    
    return True

def load_json(file):
    return simplejson.load(file)

def load_file(args):
    if args.filename:
        with open(args.filename, 'r') as f:
            content = simplejson.load(file)
    
        return content
    else:
        content = simplejson.load(sys.stdin)
        return content

def dump_file(raw, args):
    if args.filename:
        with open(args.filename, 'w') as f:
            f.write(raw)
    else:
        sys.stdout.write(str(raw) + "\n")

def validate_dict(args, dict):
    if args.item_name in dict and args.attribute_name in dict:
        return True
    else:
        return False

def parse_json(args, dict):
    if validate_dict(args, dict):
        name = dict[args.item_name]
        attrs = dict[args.attribute_name]
        return name, attrs
    else:
        parser = get_parser()
        parser.error("Invalid input format")

def build_query(domain, args):
    validate_query(args.query)
    (key, value) = args.query.split('=')

    if args.attributes:
        attributes = ','.join(args.attributes)
    else:
        attributes = '*'

    if args.fuzzy:
        q = 'select %s from `%s` where %s like "%%%s%%"' % \
            (attributes, domain.name, key, value)
        return q
    else:
        q = 'select %s from `%s` where %s="%s"' % \
            (attributes, domain.name, key, value)
        return q

def search_items(domain, query):
    rs = domain.select(query)
    items = []
    for item in rs:
        items.append(item)

    return items

def put(data, domain, args):
    if isinstance(data, dict):
        data_list = [ data ]
    else:
        data_list = data

    for item in data_list:
        (item_name, item_attrs) = parse_json(args, item)
        print "Uploading item %s" % item_name
        domain.put_attributes(item_name, item_attrs)

def delete(domain, args):

    if args.item_name:
        items = []
        item = domain.get_item(args.item_name)
        items.append(item)
    elif args.query:
        q = build_query(domain, args)
        items = search_items(domain, q)
    else:
        if confirm("WARNING!!! Are you sure you want to delete all entries?:"):
            items = []
            for item in domain:
                items.append(item)
        else:
            print "Cancelling operations"
            sys.exit()

    for item in items:
        if args.attributes:
            print "Deleting item %s attribute %s" % (item.name, args.attributes)
            domain.delete_attributes(item.name, attributes=args.attributes)
        else:
            print "Deleting item %s" % item.name
            item.delete()

def get(domain, args):

    if args.item_name:
        items = []
        item = domain.get_item(args.item_name)
        items.append(item)
    elif args.query:
        q = build_query(domain, args)
        items = search_items(domain, q)
    else:
        items = []
        for item in domain:
            items.append(item)

    return items

def run():
    (accesskey, secretkey) = get_creds()
    args = get_args()
    conn = get_conn(accesskey, secretkey)
    domain = get_domain(conn, args.domain)

    if args.subparser_name == 'put':
        data = load_file(args)
        put(data, domain, args)

    if args.subparser_name == 'del':
        delete(domain, args)

    if args.subparser_name == 'get':
        items = get(domain, args)
        dump_file(simplejson.dumps(items, indent=True), args)

if __name__ == '__main__':
    run()
