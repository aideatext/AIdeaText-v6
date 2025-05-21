from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os

def update_cosmos_indexing():
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    key = os.environ.get("COSMOS_KEY")
    database_name = "user_database"  # Cambiado de "sqllink" a "user_database"
    container_name = "users"

    if not all([endpoint, key, database_name, container_name]):
        raise ValueError("Please ensure all required parameters are set.")

    client = CosmosClient(endpoint, key)
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    print(f"Updating indexing policy for container {container_name}...")

    indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/*"}
        ],
        "excludedPaths": [
            {"path": "/_etag/?"}
        ]
    }

    try:
        container_def = container.read()
        container_def['indexingPolicy'] = indexing_policy
        partition_key_path = container_def['partitionKey']['paths'][0]

        database.replace_container(
            container_def,
            partition_key=PartitionKey(path=partition_key_path)
        )
        print("Indexing policy updated successfully")
    except exceptions.CosmosResourceNotFoundError as e:
        print(f"Error: Container not found. {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    update_cosmos_indexing()