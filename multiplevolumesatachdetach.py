import oci

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
    backup_id = backup_response.data.id

    # Wait for the backup to become available (optional but recommended)
    backup = block_storage_client.get_volume_backup(backup_id).data
    if backup.lifecycle_state != oci.core.models.VolumeBackup.LIFECYCLE_STATE_AVAILABLE:
        block_storage_client.get_volume_backup(backup_id, wait_for_states=[oci.core.models.VolumeBackup.LIFECYCLE_STATE_AVAILABLE])

    # Create a block volume from the backup (image)
    create_volume_details = oci.core.models.CreateVolumeDetails(
        compartment_id=compartment_id,
        display_name=f'{volume.display_name}_New',
        source_volume_backup_id=backup_id,
        availability_domain=volume.availability_domain,
        size_in_gbs=backup.size_in_gbs  # Set the size of the new volume as needed
    )

    volume_response = block_storage_client.create_volume(create_volume_details)
    new_volume_id = volume_response.data.id
    new_volumes.append(new_volume_id)

    # Wait for the new volume to become available (optional but recommended)
    volume = block_storage_client.get_volume(new_volume_id).data
    if volume.lifecycle_state != oci.core.models.Volume.LIFECYCLE_STATE_AVAILABLE:
        block_storage_client.get_volume(new_volume_id, wait_for_states=[oci.core.models.Volume.LIFECYCLE_STATE_AVAILABLE])

# Attach the newly created volumes to the target instance
for volume_id in new_volumes:
    attach_volume_details = oci.core.models.AttachVolumeDetails(
        instance_id=target_instance_id,
        volume_id=volume_id
    )

    block_storage_client.attach_volume(attach_volume_details)

    # Wait for the volume to be attached (optional but recommended)
    block_storage_client.get_volume(volume_id, wait_for_states=[oci.core.models.Volume.LIFECYCLE_STATE_ATTACHED])
