#!/usr/bin/env python3
"""
CLI Module
---------
Provides CLI functionality for the WiFi fuzzing platform,
with focus on Android device interaction for WiFi testing.
"""

import cmd


class CLI(cmd.Cmd):
    """Class for CLI operations for WiFi fuzzing and Android interaction."""

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
        Initialize the CLI with target monitor.

        Args:
            target_monitor: Optional reference to Target_Monitor instance
        """
        super().__init__()
        # Store reference to Target_Monitor if provided
        self.target_monitor = target_monitor

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
                # Split the command to handle "adb shell" vs other commands
                args = arg.split()
                # If it's an adb shell command, pass everything after "shell" to executor
                if args[0] == "shell" and len(args) > 1:
                    result = self.target_monitor.executor.adb_exec(" ".join(args[1:]))
                    print(result)
                else:
                    # For non-shell commands, try to execute but might not be supported
                    print("Note: Only 'adb shell' commands are fully supported with the Target Monitor")
                    self._execute_adb_subprocess(arg)
            except Exception as e:
                print(f"Error executing ADB command through Target_Monitor: {e}")
                self._execute_adb_subprocess(arg)
        else:
            # Fall back to subprocess if Target_Monitor is not available
            self._execute_adb_subprocess(arg)

    def _execute_adb_subprocess(self, arg):
        """Execute ADB command using Target Monitor."""
        try:
            if self.target_monitor and hasattr(self.target_monitor, 'executor'):
                stdout = self.target_monitor.executor.adb_exec(arg)
                print(stdout)
            else:
                print("Error: Target Monitor not available")
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

    def do_wifi_info(self, arg):
        """
        Display WiFi information from the connected Android device.
        Usage: wifi_info
        """
        if self.target_monitor and hasattr(self.target_monitor, 'executor') and self.target_monitor.executor:
            try:
                # Get WiFi information
                wifi_info = self.target_monitor.executor.adb_exec("dumpsys wifi")
                # Extract and display key WiFi information
                print("\n===== WiFi Information =====")
                for line in wifi_info.splitlines():
                    if any(x in line for x in ["SSID", "BSSID", "RSSI", "state=", "IP", "Supplicant", "freq", "scan"]):
                        print(line.strip())
            except Exception as e:
                print(f"Error getting WiFi info: {e}")
        else:
            print("Error: Target Monitor not available")

    def do_network_status(self, arg):
        """
        Display network status information from the connected Android device.
        Usage: network_status
        """
        if self.target_monitor and hasattr(self.target_monitor, 'executor') and self.target_monitor.executor:
            try:
                # Get network statistics
                print("\n===== Network Status =====")
                netstats = self.target_monitor.executor.adb_exec("dumpsys netstats | grep -A 5 wifi").strip()
                print(netstats)
                # Get current connectivity
                connectivity = self.target_monitor.executor.adb_exec("dumpsys connectivity | grep -A 5 'NetworkAgentInfo'").strip()
                print("\n----- Current Connectivity -----")
                print(connectivity)
            except Exception as e:
                print(f"Error getting network status: {e}")
        else:
            print("Error: Target Monitor not available")

    # ===== Standard CLI Commands =====
    def do_exit(self, arg):
        """Exit the CLI."""
        print("Exiting CLI...")
        return True

    def do_quit(self, arg):
        """Exit the CLI."""
        return self.do_exit(arg)

    # Make exit work with Ctrl+D (EOF)
    do_EOF = do_exit


# Command-line interface for testing
if __name__ == "__main__":
    # Run in interactive mode
    print("Starting interactive CLI mode. Type 'help' for commands.")
    CLI().cmdloop()