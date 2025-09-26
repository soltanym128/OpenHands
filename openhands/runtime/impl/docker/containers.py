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
