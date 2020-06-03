#!/bin/bash

# Bash script with AZ CLI to automate the creation/deletion of my
# Azure Redis Cache account.
# Chris Joakim, Microsoft, 2020/06/03
#
# See https://docs.microsoft.com/en-us/cli/azure/?view=azure-cli-latest

# az login

source ./env.sh

arg_count=$#
processed=0

delete() {
    processed=1
    echo 'deleting redis rg: '$redis_rg
    az group delete \
        --name $redis_rg \
        --subscription $subscription \
        --yes \
        > tmp/redis_rg_delete.json
}

create() {
    processed=1
    echo 'creating redis rg: '$redis_rg
    az group create \
        --location $redis_region \
        --name $redis_rg \
        --subscription $subscription \
        > tmp/redis_rg_create.json

    echo 'creating redis: '$redis_name
    az redis create \
        --location $redis_region \
        --name $redis_name \
        --resource-group $redis_rg \
        --sku $redis_sku \
        --vm-size $redis_vm_size \
        --enable-non-ssl-port \
        > tmp/redis_rg_create.json
}

recreate() {
    processed=1
    delete
    create
    info 
}

info() {
    processed=1
    echo 'redis show: '$redis_name
    az redis show \
        --name $redis_name \
        --resource-group $redis_rg \
        --subscription $subscription \
        > tmp/redis_show.json

    echo 'redis list-keys: '$redis_name
    az redis list-keys \
        --name $redis_name \
        --resource-group $redis_rg \
        --subscription $subscription \
        > tmp/redis_list_keys.json
}

display_usage() {
    echo 'Usage:'
    echo './redis.sh delete'
    echo './redis.sh create'
    echo './redis.sh recreate'
    echo './redis.sh info'
}

# ========== "main" logic below ==========

if [ $arg_count -gt 0 ]
then
    for arg in $@
    do
        if [ $arg == "delete" ];   then delete; fi 
        if [ $arg == "create" ];   then create; fi 
        if [ $arg == "recreate" ]; then recreate; fi 
        if [ $arg == "info" ];     then info; fi 
    done
fi

if [ $processed -eq 0 ]; then display_usage; fi

echo 'done'
