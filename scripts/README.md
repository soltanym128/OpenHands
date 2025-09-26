# Container Cleanup Utility

This directory contains utilities for managing Docker containers created by OpenHands.

## scripts/cleanup_containers.py

A utility script to clean up orphaned Docker containers that may be left behind after inference runs.

### Usage

```bash
# Clean up containers older than 24 hours (default)
python scripts/cleanup_containers.py

# Clean up containers older than 6 hours
python scripts/cleanup_containers.py --max-age-hours=6

# See what would be cleaned up without actually doing it
python scripts/cleanup_containers.py --dry-run

# Remove ALL OpenHands containers (use with caution!)
python scripts/cleanup_containers.py --all
```

### When to Use

- When you notice many Docker containers in 'exited' state with names starting with `openhands-runtime-`
- After running evaluation benchmarks that may have left containers behind
- To clean up after interrupted inference sessions
- As part of regular maintenance to free up disk space

### Safety

- The script only affects containers with the `openhands-runtime-` prefix
- By default, it only removes containers that have been in 'exited' state for more than 24 hours
- Use `--dry-run` to see what would be cleaned up before actually doing it
- The `--all` flag requires confirmation before removing ALL OpenHands containers