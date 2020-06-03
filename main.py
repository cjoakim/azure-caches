"""
Usage:
  python main.py create_files_list_json
  python main.py populate_cosmos  > data/results/populate_cosmos.txt
  python main.py populate_redis   > data/results/populate_redis.txt
  python main.py perf_test_cosmos > data/results/perf_test_cosmos.txt
  python main.py perf_test_redis  > data/results/perf_test_redis.txt
  python main.py produce_report
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

__author__  = 'Chris Joakim'
__email__   = "chjoakim@microsoft.com"
__license__ = "MIT"
__version__ = "2020.06.02"


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

def populate_cosmos():
    cosmos_client = create_cosmos_client()
    clink = container_link('dev', 'cache')
    files_data = read_json('data/npm_libs/files-list.json')
    files_list = sorted(files_data.keys())
    results = dict()
    for filename in files_list:
        key = filename.strip()
        content = read_file(key)
        content_size = len(content)
        doc = json.loads(content)
        doc['pk'] = key
        print(doc)
        t1 = time.time()
        cosmos_client.UpsertItem(clink, doc)
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
    write('data/results/populate_cosmos.json', json.dumps(results, sort_keys=True, indent=4))

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
    files_data = read_json('data/npm_libs/files-list.json')
    files_list = sorted(files_data.keys())
    results = dict()

    for filename in files_list:
        key = filename.strip()
        result = dict()
        result['key'] = key
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
            result['message'] = 'exception'
            traceback.print_exc(file=sys.stdout)
        results[key] = result
    write('data/results/perf_test_cosmos.json', json.dumps(results, sort_keys=True, indent=4))

def perf_test_redis():
    redis_client = create_redis_client()
    files_data = read_json('data/npm_libs/files-list.json')
    files_list = sorted(files_data.keys())
    results = dict()

    for filename in files_list:
        key = filename.strip()
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
    files_data  = read_json('data/npm_libs/files-list.json')
    files_list  = sorted(files_data.keys())
    cosmos_perf = read_json('data/results/perf_test_cosmos.json')
    redis_perf  = read_json('data/results/perf_test_redis.json')

    count, sum_cosmos, sum_redis, sum_size = 0, 0.0, 0.0, 0.0

    print('metadata_name,metadata_size,cosmos_name,cosmos_elapsed,cosmos_size,redis_name,redis_elapsed,redis_size')
    for filename in files_list:
        key = filename.strip()
        metadata = files_data[key]
        metadata_name  = metadata['name']
        metadata_size  = metadata['size']
        cosmos_result  = cosmos_perf[key]
        cosmos_name    = cosmos_result['doc']['name']
        cosmos_elapsed = cosmos_result['elapsed']
        cosmos_size    = cosmos_result['content_size']
        redis_result   = redis_perf[key]
        redis_name     = redis_result['doc']['name']
        redis_elapsed  = redis_result['elapsed']
        redis_size     = redis_result['content_size']
        count = count + 1
        sum_cosmos = sum_cosmos + cosmos_elapsed
        sum_redis  = sum_redis  + redis_elapsed
        sum_size   = sum_size + metadata_size

        print('{},{},{},{},{},{},{},{}'.format(
            metadata_name, metadata_size,
            cosmos_name, cosmos_elapsed, cosmos_size,
            redis_name, redis_elapsed, redis_size))

    print('doc count:    {}'.format(count))
    print('doc avg size: {}'.format(int(sum_size / float(count))))
    print('sum_cosmos:   {}'.format(sum_cosmos))
    print('sum_redis:    {}'.format(sum_redis))
    print('avg_cosmos:   {}'.format(sum_cosmos / float(count)))
    print('avg_redis:    {}'.format(sum_redis / float(count)))

def redis_set(key, value):
    return redis_client.set(key, value)

def redis_get(key):
    return redis_client.get(key)

def container_link(dbname, cname):
    return 'dbs/{}/colls/{}'.format(dbname, cname)

def create_redis_client():
    host = os.environ['AZURE_REDISCACHE_HOST']
    key  = os.environ['AZURE_REDISCACHE_KEY']
    return redis.StrictRedis(host=host, port=6380, db=0, password=key, ssl=True)

def create_cosmos_client():
    uri = os.environ['AZURE_COSMOSDB_SQLDB_URI']
    key = os.environ['AZURE_COSMOSDB_SQLDB_KEY']
    return cosmos_client.CosmosClient(uri, {'masterKey': key})

def get_npm_libs_files_list():
    return read_lines('data/npm_libs/files-list.txt')

def create_files_list_json():
    files_dict = dict()
    files_list = read_lines('data/npm_libs/files-list.txt')
    for filename in files_list:
        key = filename.strip()
        content = read_file(key)
        content_size = len(content)
        doc = json.loads(content)
        metadata = dict()
        metadata['name'] = doc['name']
        metadata['size'] = len(content)
        files_dict[key] = metadata
        print("filename: {} {}".format(key, json.dumps(metadata)))
    write('data/npm_libs/files-list.json', json.dumps(files_dict, sort_keys=True, indent=4))

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

    elif func == 'populate_cosmos':
        populate_cosmos()

    elif func == 'populate_redis':
        populate_redis()

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
