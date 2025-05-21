from azure.cosmos import CosmosClient, exceptions
import os

def diagnose_cosmos_connection():
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    key = os.environ.get("COSMOS_KEY")

    if not all([endpoint, key]):
        raise ValueError("Please ensure COSMOS_ENDPOINT and COSMOS_KEY are set.")

    client = CosmosClient(endpoint, key)

    print("Attempting to connect to Cosmos DB...")
    try:
        # List databases
        print("Listing databases:")
        databases = list(client.list_databases())
        for db in databases:
            print(f"- {db['id']}")

            # Try to list containers for each database
            try:
                containers = list(client.get_database_client(db['id']).list_containers())
                print(f"  Containers in {db['id']}:")
                for container in containers:
                    print(f"  - {container['id']}")
            except exceptions.CosmosResourceNotFoundError:
                print(f"  Unable to list containers in {db['id']}")
            except Exception as e:
                print(f"  Error listing containers in {db['id']}: {str(e)}")

            print()  # Add a blank line for readability

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    diagnose_cosmos_connection()