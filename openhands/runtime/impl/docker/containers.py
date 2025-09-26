import docker

from openhands.core.logger import openhands_logger as logger


def stop_all_containers(prefix: str) -> None:
    """Stop all containers that match the given prefix.
    
    Args:
        prefix: Container name prefix to match (e.g., 'openhands-runtime-')
    """
    docker_client = docker.from_env()
    try:
        containers = docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name and container.name.startswith(prefix):
                    container.stop()
            except docker.errors.APIError:
                pass
            except docker.errors.NotFound:
                pass
    except docker.errors.NotFound:  # yes, this can happen!
        pass
    finally:
        docker_client.close()


def stop_and_remove_all_containers(prefix: str) -> None:
    """Stop and remove all containers that match the given prefix.
    
    This ensures containers are completely cleaned up rather than left in 'exited' state.
    
    Args:
        prefix: Container name prefix to match (e.g., 'openhands-runtime-')
    """
    docker_client = docker.from_env()
    try:
        containers = docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name and container.name.startswith(prefix):
                    # First stop the container if it's running
                    if container.status == 'running':
                        logger.debug(f'Stopping container {container.name}')
                        container.stop(timeout=10)
                    
                    # Then remove the container
                    logger.debug(f'Removing container {container.name}')
                    container.remove(force=True)
                    logger.debug(f'Successfully removed container {container.name}')
            except docker.errors.APIError as e:
                logger.debug(f'Docker API error when cleaning up container {container.name}: {e}')
                pass
            except docker.errors.NotFound:
                # Container was already removed or doesn't exist
                pass
            except Exception as e:
                logger.warning(f'Unexpected error when cleaning up container {container.name}: {e}')
    except docker.errors.NotFound:  # yes, this can happen!
        pass
    except Exception as e:
        logger.warning(f'Error while listing containers for cleanup: {e}')
    finally:
        docker_client.close()


def cleanup_orphaned_containers(prefix: str, max_age_hours: int = 24) -> int:
    """Clean up orphaned containers older than the specified age.
    
    This function finds containers that match the prefix and are in 'exited' state
    for longer than max_age_hours, then removes them. This is useful for cleaning
    up containers that may have been left behind by previous runs.
    
    Args:
        prefix: Container name prefix to match (e.g., 'openhands-runtime-')
        max_age_hours: Maximum age in hours for containers to be considered orphaned
        
    Returns:
        Number of containers cleaned up
    """
    import datetime
    
    docker_client = docker.from_env()
    cleaned_count = 0
    
    try:
        containers = docker_client.containers.list(all=True, filters={'status': 'exited'})
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        for container in containers:
            try:
                if not (container.name and container.name.startswith(prefix)):
                    continue
                    
                # Check the container's finish time
                finished_at_str = container.attrs['State'].get('FinishedAt', '')
                if not finished_at_str or finished_at_str == '0001-01-01T00:00:00Z':
                    continue
                    
                # Parse the finish time
                finished_at = datetime.datetime.fromisoformat(
                    finished_at_str.replace('Z', '+00:00')
                )
                
                # Check if the container is old enough to be considered orphaned
                age_hours = (current_time - finished_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    logger.info(f'Removing orphaned container {container.name} (age: {age_hours:.1f} hours)')
                    container.remove(force=True)
                    cleaned_count += 1
                    
            except docker.errors.APIError as e:
                logger.debug(f'Docker API error when cleaning up orphaned container {container.name}: {e}')
            except docker.errors.NotFound:
                # Container was already removed
                pass
            except Exception as e:
                logger.warning(f'Unexpected error when processing container {container.name}: {e}')
                
    except Exception as e:
        logger.warning(f'Error while cleaning up orphaned containers: {e}')
    finally:
        docker_client.close()
        
    if cleaned_count > 0:
        logger.info(f'Cleaned up {cleaned_count} orphaned containers')
        
    return cleaned_count
