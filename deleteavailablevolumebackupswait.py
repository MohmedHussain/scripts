import oci
import time

# Set up the authentication details
config = oci.config.from_file()
block_storage_client = oci.core.BlockstorageClient(config)

# Define the compartment ID where your resources reside
compartment_id = 'your_compartment_ocid'

# Function to delete block volume backups
def delete_volume_backups():
    # Get list of available volume backups in the compartment
    list_backups_response = block_storage_client.list_volume_backups(compartment_id=compartment_id, lifecycle_state='AVAILABLE')
    backups = list_backups_response.data

    # Delete each available backup
    for backup in backups:
        block_storage_client.delete_volume_backup(backup.id)
        print(f"Deleted backup: {backup.id}")
        # Optional: Add a small delay after deletion (wait for 5 seconds)
        time.sleep(5)

# Function to delete block volumes
def delete_volumes():
    # Get list of available volumes in the compartment
    list_volumes_response = block_storage_client.list_volumes(compartment_id=compartment_id, lifecycle_state='AVAILABLE')
    volumes = list_volumes_response.data

    # Delete each available volume
    for volume in volumes:
        block_storage_client.delete_volume(volume.id)
        print(f"Deleted volume: {volume.id}")
        # Optional: Add a small delay after deletion (wait for 5 seconds)
        time.sleep(5)

# Uncomment and use the function(s) you need to perform cleanup
# delete_volume_backups()
# delete_volumes()
