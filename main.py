"""
Usage:
  python main.py populate_cosmos_npm      > data/results/populate_cosmos_npm.txt
  python main.py populate_cosmos_zipcodes > data/results/populate_cosmos_zipcodes.txt
  python main.py populate_redis_npm       > data/results/populate_redis_npm.txt
  python main.py populate_redis_zipcodes  > data/results/populate_redis_zipcodes.txt

  python main.py perf_test_cosmos > data/results/perf_test_cosmos.txt
  python main.py perf_test_redis  > data/results/perf_test_redis.txt
  python main.py produce_report

  python main.py create_files_list_json
  python main.py create_keys_file
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

__author__  = 'Chris Joakim'
__email__   = "chjoakim@microsoft.com"
__license__ = "MIT"
__version__ = "2020.06.03"


# https://docs.microsoft.com/en-us/azure/azure-cache-for-redis/cache-python-get-started

import json
import os
import sys
import time
import traceback

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.http_constants as http_constants
import azure.cosmos.documents as documents

from docopt import docopt

import redis


def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version=__version__)
    print(arguments)

def populate_cosmos_npm():
    cosmos_client, populate = create_cosmos_client(), True
    clink = container_link('dev', 'cache')
    files_list = read_json('data/npm_libs/files-list.json')
    sorted_filenames = sorted(files_list.keys())
    results = dict()
    for idx, filename in enumerate(sorted_filenames):
        key = filename.strip()
        infile = 'data/npm_libs/{}'.format(key)
        content = read_file(infile)
        content_size = len(content)
        doc = json.loads(content)
        doc['pk'] = doc['name']
        doc['doctype'] = 'npmlib'
        t1 = time.time()
        cosmos_client.UpsertItem(clink, doc)
        t2 = time.time()
        elapsed = t2 - t1
        print("=== filename: {} {} {}".format(infile, content_size, elapsed))
        result = dict()
        result['pk'] = doc['pk']
        result['size'] = content_size
        result['t1'] = t1
        result['t2'] = t2
        result['elapsed'] = elapsed
        result['doc'] = doc
        results[key] = result
    write('data/results/populate_cosmos_npm.json', json.dumps(results, sort_keys=True, indent=4))

def populate_cosmos_zipcodes():
    cosmos_client, populate = create_cosmos_client(), True
    clink = container_link('dev', 'cache')
    zipcodes = read_json('data/zipcodes/nc_zipcodes.json')
    results = dict()
    for doc in zipcodes:
        key = doc['postal_cd']
        doc['pk'] = key
        doc['doctype'] = 'zipcode'
        content = json.dumps(doc, sort_keys=False, indent=4)
        content_size = len(content)
        t1 = time.time()
        cosmos_client.UpsertItem(clink, doc)
        t2 = time.time()
        elapsed = t2 - t1
        print("=== zipcode: {} {} {}".format(key, content_size, elapsed))
        result = dict()
        result['pk'] = doc['pk']
        result['size'] = content_size
        result['t1'] = t1
        result['t2'] = t2
        result['elapsed'] = elapsed
        result['doc'] = doc
        results[key] = result
    write('data/results/populate_cosmos_zipcodes.json', json.dumps(results, sort_keys=True, indent=4))

def populate_redis_npm():
    redis_client = create_redis_client()
    files_list = read_json('data/npm_libs/files-list.json')
    sorted_filenames = sorted(files_list.keys())
    results = dict()
    for idx, basename in enumerate(sorted_filenames):
        infile = 'data/npm_libs/{}'.format(basename)
        content = read_file(infile)
        doc = json.loads(content)
        key = doc['name']
        json_content = json.dumps(doc)
        json_content_size = len(json_content)
        t1 = time.time()
        redis_client.set(key, json_content)
        t2 = time.time()
        elapsed = t2 - t1
        print("=== key: {} {} {}".format(key, json_content_size, elapsed))
        result = dict()
        result['key'] = key
        result['size'] = json_content_size
        result['t1'] = t1
        result['t2'] = t2
        result['elapsed'] = elapsed
        result['doc'] = doc
        results[key] = result

def populate_redis_zipcodes():
    redis_client = create_redis_client()
    zipcodes = read_json('data/zipcodes/nc_zipcodes.json')
    results = dict()
    for doc in zipcodes:
        key = doc['postal_cd']
        json_content = json.dumps(doc)
        json_content_size = len(json_content)
        t1 = time.time()
        redis_client.set(key, json_content)
        t2 = time.time()
        elapsed = t2 - t1
        print("=== key: {} {} {}".format(key, json_content_size, elapsed))
        result = dict()
        result['key'] = key
        result['size'] = json_content_size
        result['t1'] = t1
        result['t2'] = t2
        result['elapsed'] = elapsed
        result['doc'] = doc
        results[key] = result

def populate_redis():
    redis_client = create_redis_client()
    files_data = read_json('data/npm_libs/files-list.json')
    files_list = sorted(files_data.keys())
    results = dict()
    for filename in files_list:
        key = filename.strip()
        content = read_file(key)
        content_size = len(content)
        t1 = time.time()
        redis_client.set(key, content)
        t2 = time.time()
        elapsed = t2 - t1
        print("=== filename: {} {} {}\n{}".format(key, content_size, elapsed, content))
        result = dict()
        result['key'] = key
        result['size'] = content_size
        result['t1'] = t1
        result['t2'] = t2
        result['elapsed'] = elapsed
        result['metadata'] = files_data[key]
        results[key] = result
    write('data/results/populate_redis_results.json', json.dumps(results, sort_keys=True, indent=4))

def perf_test_cosmos():
    cosmos_client = create_cosmos_client()
    clink = container_link('dev', 'cache')
    keys_data = read_json('data/keys.json')
    keys_list = sorted(keys_data.keys())
    results = dict()

    for key in keys_list:
        key_obj = keys_data[key]
        result = dict()
        result['key'] = key
        result['key_obj'] = key_obj
        result['error'] = 0
        print("=== reading: {}".format(key))
        try:
            sql = "select * from c where c.pk = '{}' offset 0 limit 1".format(key)
            result['sql'] = sql
            # measured time is to read the datastore and get the result as a usable JSON document
            t1 = time.time()
            items = cosmos_client.QueryItems(clink, sql, {'enableCrossPartitionQuery': False})
            doc = None
            if items:
                for item in items:
                    doc = item
            if doc:
                t2 = time.time()
                elapsed = t2 - t1
                result['content_size'] = len(json.dumps(doc, sort_keys=False, indent=2))
                result['content_type'] = str(type(doc))
                result['doc'] = doc
                result['t1'] = t1
                result['t2'] = t2
                result['elapsed'] = elapsed
                result['message'] = 'ok'
            else:
                result['error'] = 1
                result['message'] = 'no data'
        except:
            result['error'] = 1
            result['message'] = 'EXCEPTION'
            traceback.print_exc(file=sys.stdout)
        results[key] = result
    write('data/results/perf_test_cosmos.json', json.dumps(results, sort_keys=True, indent=4))

def perf_test_redis():
    redis_client = create_redis_client()
    keys_data = read_json('data/keys.json')
    keys_list = sorted(keys_data.keys())
    results = dict()

    for key in keys_list:
        key_obj = keys_data[key]
        result = dict()
        result['key'] = key
        result['error'] = 0
        print("=== reading: {}".format(key))
        try:
            # measured time is to read the datastore and get the result as a JSON document
            t1 = time.time()
            content = redis_client.get(key)
            if content and (len(content) > 0):
                doc = json.loads(content)
                t2 = time.time()
                elapsed = t2 - t1
                result['content_size'] = len(content)
                result['content_type'] = str(type(content))
                result['doc'] = doc
                result['t1'] = t1
                result['t2'] = t2
                result['elapsed'] = elapsed
                result['message'] = 'ok'
            else:
                result['error'] = 1
                result['message'] = 'no data'
        except:
            result['error'] = 1
            result['message'] = 'exception'
            traceback.print_exc(file=sys.stdout)
        results[key] = result
    write('data/results/perf_test_redis.json', json.dumps(results, sort_keys=True, indent=4))

def produce_report():
    keys_data = read_json('data/keys.json')
    keys_list = sorted(keys_data.keys())
    cosmos_perf = read_json('data/results/perf_test_cosmos.json')
    redis_perf  = read_json('data/results/perf_test_redis.json')

    count, sum_cosmos, sum_redis, sum_size = 0, 0.0, 0.0, 0.0
    csv_lines = list()
    csv_lines.append('key,doctype,approx_size,cosmos_name,cosmos_elapsed,cosmos_size,redis_name,redis_elapsed,redis_size')
    
    for key in keys_list:
        key_obj = keys_data[key]
        doctype        = key_obj['type']
        approx_size    = key_obj['approx_size']
        cosmos_result  = cosmos_perf[key]
        cosmos_pk      = cosmos_result['doc']['pk']
        cosmos_elapsed = cosmos_result['elapsed']
        cosmos_size    = cosmos_result['content_size']
        redis_result   = redis_perf[key]
        redis_key      = redis_result['key']
        redis_elapsed  = redis_result['elapsed']
        redis_size     = redis_result['content_size']
        count = count + 1
        sum_cosmos = sum_cosmos + cosmos_elapsed
        sum_redis  = sum_redis  + redis_elapsed
        avg_size   = (cosmos_size + redis_size) / 2.0
        sum_size   = sum_size + avg_size

        csv_lines.append('{},{},{},{},{},{},{},{},{}'.format(
            key, doctype, approx_size,
            cosmos_pk, cosmos_elapsed, cosmos_size,
            redis_key, redis_elapsed, redis_size))

    print('doc count:    {}'.format(count))
    print('doc avg size: {}'.format(int(sum_size / float(count))))
    print('sum_cosmos:   {}'.format(sum_cosmos))
    print('sum_redis:    {}'.format(sum_redis))
    print('avg_cosmos:   {}'.format(sum_cosmos / float(count)))
    print('avg_redis:    {}'.format(sum_redis / float(count)))
    write('data/results/results.csv', "\n".join(csv_lines))

def redis_set(key, value):
    return redis_client.set(key, value)

def redis_get(key):
    return redis_client.get(key)

def container_link(dbname, cname):
    return 'dbs/{}/colls/{}'.format(dbname, cname)

def create_redis_client():
    host = os.environ['AZURE_REDIS_HOST']
    key  = os.environ['AZURE_REDIS_KEY']
    return redis.StrictRedis(host=host, port=6380, db=0, password=key, ssl=True)

def create_cosmos_client():
    uri = os.environ['AZURE_COSMOS_URI']
    key = os.environ['AZURE_COSMOS_KEY']
    return cosmos_client.CosmosClient(uri, {'masterKey': key})

def get_npm_libs_files_list():
    return read_lines('data/npm_libs/files-list.txt')

def create_files_list_json():
    files_dict = dict()
    # created with: l | cut -c53-999 > files-list.txt
    files_list = read_lines('data/npm_libs/files-list.txt')
    for filename in files_list:
        key = filename.strip()
        infile = 'data/npm_libs/{}'.format(key)
        content = read_file(infile)
        content_size = len(content)
        doc = json.loads(content)
        metadata = dict()
        if 'name' in doc:
            metadata['pk'] = doc['name']
            metadata['npm_name'] = doc['name']
            metadata['filename'] = infile
            metadata['size'] = len(content)
            files_dict[key] = metadata
            print("filename: {} {}".format(infile, json.dumps(metadata)))
        else:
            print('bypassing {}, no name key'.format(key))
    write('data/npm_libs/files-list.json', json.dumps(files_dict, sort_keys=True, indent=4))

def create_keys_file():
    data = dict()

    lines = read_lines('data/results/populate_redis_npm.txt')
    for line in lines:
        doc = dict()
        tokens = line.split(' ')
        key = tokens[2]
        doc['key'] = key
        doc['approx_size'] = tokens[3]
        doc['type'] = 'npm'
        data[key] = doc
    print('npm keys count: {}'.format(len(data.keys())))

    lines = read_lines('data/results/populate_redis_zipcodes.txt')
    for line in lines:
        doc = dict()
        tokens = line.split(' ')
        key = tokens[2]
        doc['key'] = key
        doc['approx_size'] = tokens[3]
        doc['type'] = 'zipcode'
        if key in data:
            print('overlaying key: {}'.format(key))
        data[key] = doc

    print('total keys count: {}'.format(len(data.keys())))
    write('data/keys.json', json.dumps(data, sort_keys=True, indent=4))
    # npm keys count: 639
    # total keys count: 1714
    # file written: data/keys.json

def read_lines(infile):
    lines = list()
    with open(infile, 'rt') as f:
        for line in f:
            lines.append(line)
    return lines

def read_file(infile):
    with open(infile, 'rt') as f:
        return f.read()

def read_json(infile):
    with open(infile, 'rt') as f:
        return json.loads(f.read())

def write(outfile, s, verbose=True):
    with open(outfile, 'w') as f:
        f.write(s)
        if verbose:
            print('file written: {}'.format(outfile))


def main_dispatch(func):

    if func == 'create_files_list_json':
        create_files_list_json()

    elif func == 'create_keys_file':
        create_keys_file()

    elif func == 'populate_cosmos_npm':
        populate_cosmos_npm()

    elif func == 'populate_cosmos_zipcodes':
        populate_cosmos_zipcodes()

    elif func == 'populate_redis_npm':
        populate_redis_npm()

    elif func == 'populate_redis_zipcodes':
        populate_redis_zipcodes()

    elif func == 'perf_test_cosmos':
        perf_test_cosmos()

    elif func == 'perf_test_redis':
        perf_test_redis()

    elif func == 'produce_report':
        produce_report()

    else:
        print_options('Error: invalid function: {}'.format(func))


if __name__ == "__main__":
    # dispatch to a main function based either on the first command-line arg,
    # or on the MAIN_PY_FUNCTION environment variable when run as a container.

    if len(sys.argv) > 1:
        main_dispatch(sys.argv[1].lower())
    else:
        main_dispatch(os.environ('MAIN_PY_FUNCTION', 'none').lower())
