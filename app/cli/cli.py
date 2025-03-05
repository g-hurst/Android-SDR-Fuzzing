#!/usr/bin/env python3
"""
CLI Module
---------
Provides CLI functionality for the WiFi fuzzing platform,
with focus on Docker container status monitoring and Android device interaction.
"""

import docker
import json
import cmd
import sys
import subprocess


class CLI(cmd.Cmd):
    """Class for CLI operations including Docker container status monitoring and Android interaction."""

    intro = """
    ================================================================
    WiFi Fuzzing Platform CLI
    
    Type 'help' or '?' to list commands.
    Type 'quit' or 'exit' to exit the program.
    ================================================================
    """
    prompt = "(fuzzer) > "

    def __init__(self, target_monitor=None):
        """
        Initialize the CLI with Docker client connection and target monitor.
        
        Args:
            target_monitor: Optional reference to Target_Monitor instance
        """
        super().__init__()
        try:
            self.client = docker.from_env()
            print("Connected to Docker")
        except docker.errors.DockerException as e:
            print(f"Error connecting to Docker: {e}")
            self.client = None
        # Store reference to Target_Monitor if provided
        self.target_monitor = target_monitor

    # ===== Docker Container Commands =====
    def do_list(self, arg):
        """
        List Docker containers with optional name prefix filter.
        Usage: list [prefix]
        Example: list wifi
        """
        args = arg.split()
        filter_prefix = args[0] if args else None
        self.print_container_list(filter_prefix=filter_prefix)

    def do_inspect(self, arg):
        """
        Show detailed information about a specific container.
        Usage: inspect <container_id>
        Example: inspect 973b308dd7
        """
        if not arg:
            print("Error: Container ID required")
            return
        self.print_container_details(arg)

    def do_wifi(self, arg):
        """
        Show only WiFi fuzzing containers.
        Usage: wifi
        """
        self.print_container_list(filter_prefix="wifi")

    # ===== Android Device Commands =====
    def do_adb(self, arg):
        """
        Execute an ADB command on the connected Android device.
        Usage: adb <command>
        Examples:
            adb devices
            adb shell ls /sdcard
            adb shell dumpsys battery
        """
        if not arg:
            print("Error: ADB command required")
            return
        # Check if we can use the Target_Monitor (preferred)
        if self.target_monitor and hasattr(self.target_monitor, 'executor') and self.target_monitor.executor:
            try:
                # Execute through Target_Monitor's ADB_Executor
                result = self.target_monitor.executor.adb_exec(arg)
                print(result)
            except Exception as e:
                print(f"Error executing ADB command through Target_Monitor: {e}")
                self._execute_adb_subprocess(arg)
        else:
            # Fall back to subprocess if Target_Monitor is not available
            self._execute_adb_subprocess(arg)

    def _execute_adb_subprocess(self, arg):
        """Execute ADB command using subprocess with timeout."""
        try:
            cmd = ["adb"] + arg.split()
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Add timeout of 5 seconds to prevent hanging
            stdout, stderr = process.communicate(timeout=5)
            if stdout:
                print(stdout.decode())
            if stderr:
                print(f"Error: {stderr.decode()}")
        except subprocess.TimeoutExpired:
            process.kill()
            print("Error: Command timed out. No device may be connected.")
        except Exception as e:
            print(f"Error executing ADB command: {e}")

    def do_logs(self, arg):
        """
        Display Android device logs.
        Usage:
            logs               - Show current logs
            logs clear         - Clear log buffer
            logs filter <tag>  - Filter logs by tag
        """
        args = arg.split()
        command = args[0] if args else "show"
        if command == "show" or not command:
            self._show_logs()
        elif command == "clear":
            self._clear_logs()
        elif command == "filter" and len(args) > 1:
            self._filter_logs(args[1])
        else:
            print("Unknown logs command. Try 'help logs' for usage information.")

    def _show_logs(self):
        """Show current device logs."""
        if self.target_monitor and hasattr(self.target_monitor, 'executor') and self.target_monitor.executor:
            try:
                logs = self.target_monitor.executor.adb_exec("logcat -d")
                print(logs)
            except Exception as e:
                print(f"Error getting logs through Target_Monitor: {e}")
                self._execute_adb_subprocess("logcat -d")
        else:
            self._execute_adb_subprocess("logcat -d")

    def _clear_logs(self):
        """Clear the log buffer."""
        if self.target_monitor and hasattr(self.target_monitor, 'executor') and self.target_monitor.executor:
            try:
                self.target_monitor.executor.adb_exec("logcat -c")
                print("Log buffer cleared")
            except Exception as e:
                print(f"Error clearing logs through Target_Monitor: {e}")
                self._execute_adb_subprocess("logcat -c")
        else:
            self._execute_adb_subprocess("logcat -c")

    def _filter_logs(self, tag):
        """Filter logs by tag."""
        if self.target_monitor and hasattr(self.target_monitor, 'executor') and self.target_monitor.executor:
            try:
                logs = self.target_monitor.executor.adb_exec(f"logcat -d *:{tag}")
                print(logs)
            except Exception as e:
                print(f"Error filtering logs through Target_Monitor: {e}")
                self._execute_adb_subprocess(f"logcat -d *:{tag}")
        else:
            self._execute_adb_subprocess(f"logcat -d *:{tag}")

    def do_device_info(self, arg):
        """
        Display information about the connected Android device.
        Usage: device_info
        """
        if self.target_monitor and hasattr(self.target_monitor, 'executor') and self.target_monitor.executor:
            try:
                # Get basic device information
                manufacturer = self.target_monitor.executor.adb_exec("getprop ro.product.manufacturer").strip()
                model = self.target_monitor.executor.adb_exec("getprop ro.product.model").strip()
                version = self.target_monitor.executor.adb_exec("getprop ro.build.version.release").strip()
                sdk = self.target_monitor.executor.adb_exec("getprop ro.build.version.sdk").strip()
                # Display battery info
                battery = self.target_monitor.executor.adb_exec("dumpsys battery")
                print("\n===== Android Device Information =====")
                print(f"Manufacturer: {manufacturer}")
                print(f"Model: {model}")
                print(f"Android Version: {version} (SDK {sdk})")
                print("\n----- Battery Information -----")
                for line in battery.splitlines():
                    if any(x in line for x in ["level", "scale", "status", "health", "present", "powered"]):
                        print(line.strip())
            except Exception as e:
                print(f"Error getting device info through Target_Monitor: {e}")
                self._execute_adb_subprocess("devices -l")
        else:
            self._execute_adb_subprocess("devices -l")

    # ===== Standard CLI Commands =====
    def do_exit(self, arg):
        """Exit the CLI."""
        print("Exiting CLI...")
        return True

    def do_quit(self, arg):
        """Exit the CLI."""
        return self.do_exit(arg)

    # Alias 'ls' to 'list' for convenience
    do_ls = do_list

    # Make exit work with Ctrl+D (EOF)
    do_EOF = do_exit

    # ===== Docker Container Methods =====
    def list_containers(self, all_containers=True, filter_prefix=None):
        """
        List Docker containers with optional filtering.

        Args:
            all_containers: Include stopped containers (default: True)
            filter_prefix: Filter containers by name prefix (e.g., "wifi")

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
            filter_prefix: Filter containers by name prefix (e.g., "wifi")
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
            filter_prefix: Filter containers by name prefix (e.g., "wifi")
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


# Command-line interface for testing
if __name__ == "__main__":
    # Check if running with arguments or in interactive mode
    if len(sys.argv) > 1:
        # Run in compatibility mode with original CLI
        cli = CLI()
        if sys.argv[1] == "list":
            filter_prefix = sys.argv[2] if len(sys.argv) > 2 else None
            cli.print_container_list(filter_prefix=filter_prefix)
        elif sys.argv[1] == "inspect" and len(sys.argv) > 2:
            cli.print_container_details(sys.argv[2])
        elif sys.argv[1] == "wifi":
            cli.print_container_list(filter_prefix="wifi")
        else:
            print("Usage:")
            print("  python3 cli.py                  - Run interactive CLI")
            print("  python3 cli.py list [prefix]    - List containers with optional name prefix")
            print("  python3 cli.py inspect <id>     - Show details for a specific container")
            print("  python3 cli.py wifi             - List WiFi fuzzing containers")
    else:
        # Run in interactive mode
        print("Starting interactive CLI mode. Type 'help' for commands.")
        CLI().cmdloop()