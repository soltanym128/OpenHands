#!/usr/bin/env python3

"""
OpenHands Docker Container Cleanup Utility

This script helps clean up orphaned Docker containers from OpenHands inference runs.
Run this if you have containers in 'exited' state that were not properly cleaned up.

Usage:
    python scripts/cleanup_containers.py [--max-age-hours=24] [--dry-run]

Options:
    --max-age-hours: Only remove containers older than this many hours (default: 24)
    --dry-run: Show what would be removed without actually removing anything
"""

import argparse
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
    from openhands.runtime.impl.docker.containers import cleanup_orphaned_containers, stop_and_remove_all_containers
    from openhands.core.logger import openhands_logger as logger
    import docker
except ImportError as e:
    print(f"Error importing OpenHands modules: {e}")
    print("Make sure you're running this from the OpenHands project directory")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Clean up orphaned OpenHands Docker containers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--max-age-hours',
        type=int,
        default=24,
        help='Only remove containers older than this many hours (default: 24)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be removed without actually removing anything'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Remove ALL OpenHands containers regardless of age (use with caution!)'
    )

    args = parser.parse_args()

    try:
        # Check if Docker is available
        docker_client = docker.from_env()
        docker_client.ping()
        docker_client.close()
        print("✅ Docker is available")
    except Exception as e:
        print(f"❌ Docker is not available: {e}")
        print("Make sure Docker is running and you have permission to access it")
        sys.exit(1)

    container_prefix = 'openhands-runtime-'
    
    if args.dry_run:
        print("🔍 DRY RUN - showing what would be cleaned up:")
        
    if args.all:
        print(f"🚨 Removing ALL containers with prefix '{container_prefix}'")
        if not args.dry_run:
            if input("Are you sure? (y/N): ").lower() != 'y':
                print("Aborted")
                sys.exit(0)
            stop_and_remove_all_containers(container_prefix)
            print("✅ All OpenHands containers removed")
        else:
            # For dry run, list all containers
            docker_client = docker.from_env()
            try:
                containers = docker_client.containers.list(all=True)
                count = 0
                for container in containers:
                    if container.name and container.name.startswith(container_prefix):
                        print(f"  - Would remove: {container.name} (status: {container.status})")
                        count += 1
                print(f"Would remove {count} containers")
            finally:
                docker_client.close()
    else:
        print(f"🧹 Cleaning up containers older than {args.max_age_hours} hours...")
        if not args.dry_run:
            cleaned_count = cleanup_orphaned_containers(container_prefix, args.max_age_hours)
            if cleaned_count == 0:
                print("✅ No orphaned containers found")
            else:
                print(f"✅ Cleaned up {cleaned_count} orphaned containers")
        else:
            # For dry run, show what would be cleaned
            import datetime
            docker_client = docker.from_env()
            try:
                containers = docker_client.containers.list(all=True, filters={'status': 'exited'})
                current_time = datetime.datetime.now(datetime.timezone.utc)
                count = 0
                
                for container in containers:
                    if not (container.name and container.name.startswith(container_prefix)):
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
                    
                    if age_hours > args.max_age_hours:
                        print(f"  - Would remove: {container.name} (age: {age_hours:.1f} hours)")
                        count += 1
                        
                print(f"Would remove {count} containers")
            finally:
                docker_client.close()

    print("🎉 Cleanup complete!")


if __name__ == '__main__':
    main()