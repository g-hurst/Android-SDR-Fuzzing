#!/usr/bin/env python3
"""
CLI Module
---------
Provides CLI functionality for the baseband fuzzing platform,
with focus on Docker container status monitoring.
"""

import docker
import json


class CLI:
    """Class for CLI operations including Docker container status monitoring."""

    def __init__(self):
        """Initialize the CLI with Docker client connection."""
        try:
            self.client = docker.from_env()
            print("Connected to Docker")
        except docker.errors.DockerException as e:
            print(f"Error connecting to Docker: {e}")
            self.client = None

    def list_containers(self, all_containers=True, filter_prefix=None):
        """
        List Docker containers with optional filtering.

        Args:
            all_containers: Include stopped containers (default: True)
            filter_prefix: Filter containers by name prefix (e.g., "srsran")

        Returns:
            List of container objects
        """
        if not self.client:
            return []

        try:
            containers = self.client.containers.list(all=all_containers)

            if filter_prefix:
                containers = [c for c in containers if c.name.startswith(filter_prefix)]

            return containers
        except Exception as e:
            print(f"Error listing containers: {e}")
            return []

    def get_container_details(self, container_id):
        """
        Get detailed information about a specific container.

        Args:
            container_id: ID or name of the container

        Returns:
            Container attributes dictionary or None if not found
        """
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)
            return container.attrs
        except docker.errors.NotFound:
            print(f"Container '{container_id}' not found")
            return None
        except Exception as e:
            print(f"Error getting container details: {e}")
            return None

    def print_container_list(self, all_containers=True, filter_prefix=None):
        """
        Print a formatted list of Docker containers.

        Args:
            all_containers: Include stopped containers (default: True)
            filter_prefix: Filter containers by name prefix (e.g., "srsran")
        """
        containers = self.list_containers(all_containers, filter_prefix)

        if not containers:
            print("No containers found")
            return

        print(f"\n{'CONTAINER ID':<15}{'NAME':<30}{'STATUS':<15}{'IMAGE':<30}")
        print("-" * 90)

        for container in containers:
            print(f"{container.short_id:<15}{container.name:<30}{container.status:<15}{container.image.tags[0] if container.image.tags else 'unknown':<30}")

    def print_container_details(self, container_id):
        """
        Print detailed information about a specific container.

        Args:
            container_id: ID or name of the container
        """
        details = self.get_container_details(container_id)

        if not details:
            return

        print(f"\nContainer Details: {container_id}")
        print("-" * 50)
        print(f"ID: {details.get('Id', 'Unknown')[:12]}")
        print(f"Name: {details.get('Name', 'Unknown').lstrip('/')}")
        print(f"Image: {details.get('Config', {}).get('Image', 'Unknown')}")
        print(f"Status: {details.get('State', {}).get('Status', 'Unknown')}")
        print(f"Created: {details.get('Created', 'Unknown')}")

        # Network info
        networks = details.get('NetworkSettings', {}).get('Networks', {})
        if networks:
            print("\nNetworks:")
            for net_name, net_info in networks.items():
                print(f"  {net_name}: {net_info.get('IPAddress', 'No IP')}")

    def save_container_status_to_json(self, filename, all_containers=True, filter_prefix=None):
        """
        Save container status information to a JSON file.

        Args:
            filename: Path to save the JSON file
            all_containers: Include stopped containers (default: True)
            filter_prefix: Filter containers by name prefix (e.g., "srsran")
        """
        containers = self.list_containers(all_containers, filter_prefix)

        container_info = []
        for container in containers:
            info = {
                'id': container.short_id,
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown'
            }
            container_info.append(info)

        try:
            with open(filename, 'w') as f:
                json.dump(container_info, f, indent=2)
            print(f"Container status saved to {filename}")
        except Exception as e:
            print(f"Error saving container status: {e}")


# Simple command-line interface for testing
if __name__ == "__main__":
    import sys

    cli = CLI()

    if len(sys.argv) < 2:
        cli.print_container_list()
    elif sys.argv[1] == "list":
        filter_prefix = sys.argv[2] if len(sys.argv) > 2 else None
        cli.print_container_list(filter_prefix=filter_prefix)
    elif sys.argv[1] == "inspect" and len(sys.argv) > 2:
        cli.print_container_details(sys.argv[2])
    elif sys.argv[1] == "srsran":
        cli.print_container_list(filter_prefix="srsran")
    else:
        print("Usage:")
        print("  python3 cli.py                  - List all containers")
        print("  python3 cli.py list [prefix]    - List containers with optional name prefix")
        print("  python3 cli.py inspect <id>     - Show details for a specific container")
        print("  python3 cli.py srsran           - List srsRAN containers")