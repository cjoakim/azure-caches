#!/bin/bash

# Bash shell that defines parameters and environment variables used 
# in this app, and is "sourced" by the other scripts in this repo.
# Chris Joakim, Microsoft, 2020/06/03

export subscription=$AZURE_SUBSCRIPTION_ID
export user=$USER
export primary_region="eastus"
export primary_rg="cjoakim-caches"

export cosmos_sql_region=$primary_region
export cosmos_sql_rg=$primary_rg
export cosmos_sql_acct_name="cjoakimcosmoscache"
export cosmos_sql_acct_consistency="Session"    # {BoundedStaleness, ConsistentPrefix, Eventual, Session, Strong}
export cosmos_sql_acct_kind="GlobalDocumentDB"  # {GlobalDocumentDB, MongoDB, Parse}
export cosmos_sql_dbname="dev"
export cosmos_sql_cache_collname="cache"
export cosmos_sql_cache_pk="/pk"
export cosmos_sql_cache_ru="1000"

export redis_region=$primary_region
export redis_rg=$primary_rg
export redis_name="cjoakimrediscache"
export redis_sku="Standard"      # {Basic, Premium, Standard}
export redis_vm_size="c1"        # {c0, c1, c2, c3, c4, c5, c6, p1, p2, p3, p4, p5}

arg_count=$#
if [ $arg_count -gt 0 ]
then
  for arg in $@
  do
    if [ $arg == "display" ]
    then
      echo "subscription:                      "$subscription
      echo "user:                              "$user
      echo "primary_region:                    "$primary_region
      echo "primary_rg:                        "$primary_rg
      echo "cosmos_sql_region:                 "$cosmos_sql_region
      echo "cosmos_sql_rg:                     "$cosmos_sql_rg
      echo "cosmos_sql_acct_name:              "$cosmos_sql_acct_name
      echo "cosmos_sql_acct_consistency:       "$cosmos_sql_acct_consistency
      echo "cosmos_sql_acct_kind:              "$cosmos_sql_acct_kind
      echo "cosmos_sql_dbname:                 "$cosmos_sql_dbname
      echo "cosmos_sql_cache_collname:         "$cosmos_sql_cache_collname
      echo "cosmos_sql_cache_pk:               "$cosmos_sql_cache_pk
      echo "cosmos_sql_cache_ru:               "$cosmos_sql_cache_ru
      echo "redis_rg:                          "$redis_rg
      echo "redis_name:                        "$redis_name
      echo "redis_sku:                         "$redis_sku
      echo "redis_vm_size:                     "$redis_vm_size
    fi
  done
fi
