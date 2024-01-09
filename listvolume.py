import oci

# Set up the authentication details
config = oci.config.from_file()

# Initialize the Blockstorage and Compute clients
block_storage_client = oci.core.BlockstorageClient(config)
compute_client = oci.core.ComputeClient(config)

# Define the OCID of the compute instance
instance_id = 'your_compute_instance_ocid'

# Get the details of the compute instance to retrieve the attached block volumes
instance = compute_client.get_instance(instance_id).data

# Retrieve the attached block volumes' details for the instance
attached_volumes = []
for attachment in instance.block_volume_attachments:
    volume_id = attachment.volume_id
    volume_details = block_storage_client.get_volume(volume_id).data
    attached_volumes.append(volume_details)

# Display information about the attached block volumes
for volume in attached_volumes:
    print(f"Volume ID: {volume.id}")
    print(f"Display Name: {volume.display_name}")
    print(f"Size (in GBs): {volume.size_in_gbs}")
    print(f"Lifecycle State: {volume.lifecycle_state}")
    print("---------------------------")
