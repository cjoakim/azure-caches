#!/bin/bash

# Bash script with AZ CLI to automate the creation/deletion of my
# Azure CosmosDB/SQL
# Chris Joakim, Microsoft, 2020/06/03
#
# See https://docs.microsoft.com/en-us/cli/azure/?view=azure-cli-latest

# az login

source ./env.sh

arg_count=$#
processed=0

delete() {
    processed=1
    echo 'deleting cosmos rg: '$cosmos_sql_rg
    az group delete \
        --name $cosmos_sql_rg \
        --subscription $subscription \
        --yes \
        > tmp/cosmos_sql_rg_delete.json
}

create() {
    processed=1
    echo 'creating cosmos rg: '$cosmos_sql_rg
    az group create \
        --location $cosmos_sql_region \
        --name $cosmos_sql_rg \
        --subscription $subscription \
        > tmp/cosmos_sql_rg_create.json

    echo 'creating cosmos acct: '$cosmos_sql_acct_name
    az cosmosdb create \
        --name $cosmos_sql_acct_name \
        --resource-group $cosmos_sql_rg \
        --subscription $subscription \
        --locations regionName=$cosmos_sql_region failoverPriority=0 isZoneRedundant=False \
        --default-consistency-level $cosmos_sql_acct_consistency \
        --enable-multiple-write-locations true \
        --kind $cosmos_sql_acct_kind \
        > tmp/cosmos_sql_acct_create.json

    create_db   
    create_collections
}

recreate_all() {
    processed=1
    delete
    create
    info 
}

recreate_dev_db() {
    processed=1
    delete_db
    create_db  
    create_collections
    info   
}

delete_db() {
    processed=1
    echo 'deleting cosmos db: '$cosmos_sql_dbname
    az cosmosdb database delete \
        --name $cosmos_sql_acct_name \
        --resource-group $cosmos_sql_rg \
        --db-name $cosmos_sql_dbname \
        > tmp/cosmos_sql_db_delete.json
}

create_db() {
    processed=1
    echo 'creating cosmos db: '$cosmos_sql_dbname
    az cosmosdb database create \
        --name $cosmos_sql_acct_name \
        --resource-group $cosmos_sql_rg \
        --db-name $cosmos_sql_dbname \
        > tmp/cosmos_sql_db_create.json
}

create_collections() {
    processed=1
    echo 'creating cosmos collection: '$cosmos_sql_cache_collname
    az cosmosdb collection create \
        --collection-name $cosmos_sql_cache_collname \
        --db-name $cosmos_sql_dbname \
        --name $cosmos_sql_acct_name \
        --resource-group $cosmos_sql_rg \
        --subscription $subscription \
        --partition-key-path $cosmos_sql_cache_pk \
        --throughput $cosmos_sql_cache_ru \
        > tmp/cosmos_sql_db_create_cache.json


    # This command has been deprecated and will be removed in a future release.
    # Use 'cosmosdb sql container, cosmosdb mongodb collection, cosmosdb cassandra table, cosmosdb gremlin graph or cosmosdb table' instead.

    # This command is implicitly deprecated because command group 'cosmosdb collection' is deprecated and will be removed in a future release. 
    # Use 'cosmosdb sql container, cosmosdb mongodb collection, cosmosdb cassandra table, cosmosdb gremlin graph or cosmosdb table' instead.
}

info() {
    processed=1
    echo 'az cosmosdb show ...'
    az cosmosdb show \
        --name $cosmos_sql_acct_name \
        --resource-group $cosmos_sql_rg \
        > tmp/cosmos_sql_db_show.json

    echo 'az cosmosdb list-keys ...'
    az cosmosdb list-keys \
        --name $cosmos_sql_acct_name \
        --resource-group $cosmos_sql_rg \
        --subscription $subscription \
        > tmp/cosmos_sql_db_keys.json

    # This command has been deprecated and will be removed in a future release. Use 'cosmosdb keys list' instead.
}

display_usage() {
    echo 'Usage:'
    echo './cosmos_sql.sh delete'
    echo './cosmos_sql.sh create'
    echo './cosmos_sql.sh recreate'
    echo './cosmos_sql.sh recreate_dev_db'
    echo './cosmos_sql.sh info'
}

# ========== "main" logic below ==========

if [ $arg_count -gt 0 ]
then
    for arg in $@
    do
        if [ $arg == "delete" ];   then delete; fi 
        if [ $arg == "create" ];   then create; fi 
        if [ $arg == "recreate" ]; then recreate_all; fi 
        if [ $arg == "recreate_dev" ]; then recreate_dev_db; fi 
        if [ $arg == "info" ];     then info; fi 
    done
fi

if [ $processed -eq 0 ]; then display_usage; fi

echo 'done'
