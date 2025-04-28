#!/usr/bin/env python3
"""
CLI Module
---------
This provides CLI functionality for the WiFi fuzzing platform,
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

    def __init__(self, target_monitor=None, packet_tracker=None, anomaly_tracker=None):
        """
        Initialize the CLI with target monitor and trackers.

        Args:
            target_monitor: Optional reference to Target_Monitor instance
            packet_tracker: Optional reference to packet tracking deque
            anomaly_tracker: Optional reference to anomaly tracking deque
        """
        super().__init__()
        # Store reference to Target_Monitor if provided
        self.target_monitor = target_monitor
        self.packet_tracker = packet_tracker
        self.anomaly_tracker = anomaly_tracker

    # Override cmdloop to catch KeyboardInterrupt completely
    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        This is overridden to catch KeyboardInterrupt and prevent it from
        propagating up to the main program.
        """
        self.preloop()
        if intro is not None:
            self.intro = intro
        if self.intro:
            self.stdout.write(str(self.intro) + "\n")
        stop = None
        while not stop:
            try:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    line = self.get_input()
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            except KeyboardInterrupt:
                print("\nKeyboard interrupt received. Type 'exit' to quit.")
                continue
        self.postloop()

    def get_input(self):
        """Get input from the user, wrapping standard input in a try/except."""
        try:
            return input(self.prompt)
        except EOFError:
            return 'EOF'

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

    def do_get_ip(self, arg):
        """
        Display the IP address of the connected Android device.
        Usage: get_ip
        """
        if self.target_monitor:
            ip_address = self.target_monitor.get_device_ip()
            if ip_address:
                print(f"Device IP address: {ip_address}")
            else:
                print("Could not retrieve device IP address")
        else:
            print("Error: Target Monitor not available")

    def do_check_network(self, arg):
        """
        Check if the target device and router are on the same network.
        Usage: check_network
        """
        if not self.target_monitor or not hasattr(self.target_monitor, 'executor') or not self.target_monitor.executor:
            print("Error: Target Monitor not available")
            return

        try:
            # Get device IP information
            device_ip = self.target_monitor.get_device_ip()
            if not device_ip:
                print("Error: Could not retrieve device IP address")
                return

            # Get subnet mask
            netmask_cmd = "ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f2"
            subnet_bits = self.target_monitor.executor.adb_exec(netmask_cmd).strip()

            # Get gateway information
            gateway_cmd = "ip route | grep default | awk '{print $3}'"
            gateway = self.target_monitor.executor.adb_exec(gateway_cmd).strip()

            # Display network information
            print("\n===== Network Configuration =====")
            print(f"Device IP Address: {device_ip}")
            if subnet_bits:
                print(f"Subnet Mask: /{subnet_bits}")
            print(f"Default Gateway: {gateway}")

            # Check connectivity to gateway
            ping_cmd = f"ping -c 1 -W 2 {gateway}"
            ping_result = self.target_monitor.executor.adb_exec(ping_cmd)

            if "1 received" in ping_result:
                print("Gateway Connectivity: SUCCESS")
                print("Device and router appear to be on the same network.")
            else:
                print("Gateway Connectivity: FAILED")
                print("Device and router may not be on the same network.")

            # Get network interface status
            interface_cmd = "ip addr show wlan0"
            interface_status = self.target_monitor.executor.adb_exec(interface_cmd)

            print("\n----- Network Interface Status -----")
            for line in interface_status.splitlines():
                line = line.strip()
                if any(x in line for x in ["state UP", "inet ", "link/ether"]):
                    print(line)
        except Exception as e:
            print(f"Error checking network configuration: {e}")

    def do_packet_stats(self, arg):
        """
        Display statistics about packets being sent and received.
        Usage: packet_stats
        """
        if not self.packet_tracker:
            print("Error: Packet tracker not available. Make sure the transmitter is running.")
            return

        packets = list(self.packet_tracker)
        if not packets:
            print("No packets have been sent yet.")
            return

        # Count total packets
        total_packets = len(packets)

        # Analyze packet types
        tcp_count = 0
        udp_count = 0
        other_count = 0

        for _, _, packet_hex in packets:
            if "TCP" in packet_hex:
                tcp_count += 1
            elif "UDP" in packet_hex:
                udp_count += 1
            else:
                other_count += 1

        # Calculate packet rate
        if len(packets) >= 2:
            start_time = packets[0][0]
            end_time = packets[-1][0]
            time_diff = (end_time - start_time).total_seconds()
            rate = len(packets) / time_diff if time_diff > 0 else 0
        else:
            rate = 0

        # Display statistics
        print("\n===== Packet Statistics =====")
        print(f"Total Packets Sent: {total_packets}")
        print(f"Packet Rate: {rate:.2f} packets/second")

        print("\n----- Packet Types -----")
        print(f"TCP Packets: {tcp_count} ({tcp_count / total_packets * 100:.1f}%)")
        print(f"UDP Packets: {udp_count} ({udp_count / total_packets * 100:.1f}%)")
        print(f"Other Packets: {other_count} ({other_count / total_packets * 100:.1f}%)")

        # Display recent packets
        print("\n----- Recent Packets -----")
        for timestamp, packet_num, packet_hex in packets[-5:]:
            print(f"Packet {packet_num} @ {timestamp.strftime('%H:%M:%S.%f')[:-3]}: {packet_hex[:60]}...")

    def do_monitor(self, arg):
        """
        Display status of what monitors can see, including packets and anomalies.
        Usage: monitor [refresh_seconds]
        Example: monitor 5 - Refreshes the display every 5 seconds
        """
        import time
        import os
        import signal

        # Parse refresh interval
        try:
            refresh = int(arg) if arg else 5  # Default to 5 seconds if no value provided
        except ValueError:
            print("Error: Invalid refresh interval. Please enter a number in seconds.")
            return

        # Prepare for continuous monitoring with refresh
        running = True

        def handle_interrupt(sig, frame):
            nonlocal running
            running = False
            print("\nStopping monitor...")

        # Set up signal handler for Ctrl+C
        original_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, handle_interrupt)

        # Cache device IP to prevent repeated lookups that might timeout
        cached_device_ip = None
        if self.target_monitor:
            try:
                cached_device_ip = self.target_monitor.get_device_ip()
            except Exception:
                pass

        try:
            while running:
                try:
                    # Clear screen for each refresh
                    os.system('cls' if os.name == 'nt' else 'clear')

                    # Title
                    print("\n===== WiFi Fuzzing Platform Status Monitor =====")
                    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

                    # Device information - use cached IP when possible
                    if cached_device_ip:
                        print(f"\nDevice IP: {cached_device_ip}")
                    elif self.target_monitor:
                        # Try to get IP but don't cause errors if it fails
                        try:
                            device_ip = self.target_monitor.get_device_ip()
                            if device_ip:
                                cached_device_ip = device_ip  # Update cache if successful
                                print(f"\nDevice IP: {device_ip}")
                            else:
                                print("\nDevice IP: Unknown")
                        except Exception:
                            print("\nDevice IP: Could not retrieve (timeout)")
                    else:
                        print("\nDevice: Not connected")

                    # Packet statistics
                    if self.packet_tracker:
                        packets = list(self.packet_tracker)
                        packet_count = len(packets)
                        # Calculate packet rate from recent packets
                        recent_rate = 0
                        if packet_count >= 2:
                            # Use last 10 packets or all if fewer
                            recent_packets = packets[-min(10, packet_count):]
                            start_time = recent_packets[0][0]
                            end_time = recent_packets[-1][0]
                            time_diff = (end_time - start_time).total_seconds()
                            recent_rate = len(recent_packets) / time_diff if time_diff > 0 else 0
                        print("\n----- Packet Statistics -----")
                        print(f"Total Packets Sent: {packet_count}")
                        print(f"Recent Rate: {recent_rate:.2f} packets/second")
                        # Show most recent packet
                        if packet_count > 0:
                            _, packet_num, packet_hex = packets[-1]
                            print(f"Last Packet: #{packet_num} - {packet_hex[:50]}...")
                    else:
                        print("\n----- Packet Statistics -----")
                        print("Packet tracking not available")

                    # Anomaly information
                    if self.anomaly_tracker:
                        anomalies = list(self.anomaly_tracker)
                        anomaly_count = len(anomalies)
                        print("\n----- Anomalies Detected -----")
                        if anomaly_count > 0:
                            print(f"Total Anomalies: {anomaly_count}")
                            print("\nRecent Anomalies:")
                            for timestamp, anomaly_type, description in anomalies[-min(3, anomaly_count):]:
                                print(f"  {timestamp.strftime('%H:%M:%S')}: {anomaly_type} - {description[:50]}...")
                        else:
                            print("No recent anomalies detected")
                    else:
                        print("\n----- Anomalies Detected -----")
                        print("Anomaly tracking not available")

                    # Skip network connection status check - was causing timeouts
                    # Show helper message
                    print("\nPress Ctrl+C to stop monitoring and return to CLI")
                    
                    # Always sleep for refresh interval
                    time.sleep(refresh)

                except KeyboardInterrupt:
                    running = False
                    print("\nStopping monitor...")
                    break
                except Exception as e:
                    print(f"Error in monitor: {e}")
                    # Don't exit on errors, just continue to next refresh
                    time.sleep(1)

        finally:
            # Restore original signal handler
            signal.signal(signal.SIGINT, original_handler)
            # Print a message to indicate returning to CLI
            print("\nReturning to CLI prompt...")
            return

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