import oci
import time

# Set up the authentication details
config = oci.config.from_file()
block_storage_client = oci.core.BlockstorageClient(config)
compute_client = oci.core.ComputeClient(config)

# Define the OCIDs and other details
source_instance_id = 'your_source_instance_ocid'
target_instance_id = 'your_target_instance_ocid'
compartment_id = 'your_compartment_ocid'

# Get the details of the compute instance to retrieve the attached block volumes
instance = compute_client.get_instance(source_instance_id).data

# Retrieve the attached block volumes' details for the instance
attached_volumes = []
for attachment in instance.block_volume_attachments:
    volume_id = attachment.volume_id
    volume_details = block_storage_client.get_volume(volume_id).data
    attached_volumes.append(volume_details)

# Define a function to check the state of a resource within a given timeout
def wait_until(resource, timeout, target_state):
    start_time = time.time()
    while time.time() - start_time < timeout:
        resource = block_storage_client.get_volume_backup(resource.id).data if isinstance(resource, oci.core.models.VolumeBackup) else block_storage_client.get_volume(resource.id).data
        if resource.lifecycle_state == target_state:
            return resource
        time.sleep(10)  # Wait for 10 seconds before checking again
    raise TimeoutError(f"Timed out waiting for {resource.id} to reach state {target_state}")

# Create block volume images from the attached volumes and then create volumes from those images
new_volumes = []
for volume in attached_volumes:
    # Create a block volume backup (image) from the source volume
    create_volume_backup_details = oci.core.models.CreateVolumeBackupDetails(
        volume_id=volume.id,
        display_name=f'{volume.display_name}_Backup',
        compartment_id=compartment_id
    )

    backup_response = block_storage_client.create_volume_backup(create_volume_backup_details)
    backup = wait_until(backup_response.data, timeout=900, target_state=oci.core.models.VolumeBackup.LIFECYCLE_STATE_AVAILABLE)
    backup_id = backup.id

    # Create a block volume from the backup (image)
    create_volume_details = oci.core.models.CreateVolumeDetails(
        compartment_id=compartment_id,
        display_name=f'{volume.display_name}_New',
        source_volume_backup_id=backup_id,
        availability_domain=volume.availability_domain,
        size_in_gbs=backup.size_in_gbs  # Set the size of the new volume as needed
    )

    volume_response = block_storage_client.create_volume(create_volume_details)
    new_volume = wait_until(volume_response.data, timeout=900, target_state=oci.core.models.Volume.LIFECYCLE_STATE_AVAILABLE)
    new_volume_id = new_volume.id
    new_volumes.append(new_volume_id)

# Attach the newly created volumes to the target instance
for volume_id in new_volumes:
    attach_volume_details = oci.core.models.AttachVolumeDetails(
        instance_id=target_instance_id,
        volume_id=volume_id
    )

    block_storage_client.attach_volume(attach_volume_details)

    # Wait for the volume to be attached
    wait_until(volume_id, timeout=600, target_state=oci.core.models.Volume.LIFECYCLE_STATE_ATTACHED)
