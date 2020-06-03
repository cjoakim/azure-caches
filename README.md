# azure-caches

Example Cache implementations in Azure - Redis, CosmosDB, etc

## CosmosDB


### Partition Keys and Logical and Physical Partitions


## Provisioning - Azure CosmosDB/SQL and Azure Redis Cache

### Using Azure Portal

- Create a Resource Group (RG)
- Create an Azure Redis Cache within the RG.  Standard SKU, c1 VM size.
- Create a CosmosDB/SQL account within the RG.
  - Database: dev, Container: cache with partition key /pk

### Using the az CLI

- Edit file **automation/env.sh**; name the resource groups and resources as necessary
- Execute the following scripts; functionally equivalent to the above Azure Portal instructions.
```
$ cd automation
$ ./redis.sh create
$ ./cosmos_sql.sh
```

These instructions are for Linux or macOS, but the az commands are identical on Windows.

---



