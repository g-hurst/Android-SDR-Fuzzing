#!/usr/bin/env python3
"""
Target Monitor Module
-------------------
Provides monitoring capabilities for the Android target device.
"""

import threading
import os
import datetime
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.adb_device import AdbDeviceUsb


class Target_Monitor(threading.Thread):
    def __init__(self, tracker):
        super().__init__()
        self._stay_alive = threading.Event()
        self._is_shutting_down = False  # Flag to prevent multiple shutdowns
        self.adb_key_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '.android/adbkey'
        )  # TODO: this should probably be configurable
        self.device = None
        self.executor = None
        self.base_cpu = None
        self.base_ram = None
        self.tracker = tracker

    def get_adb_signer(self) -> PythonRSASigner:
        # create dir and keys if needed
        key_dir = os.path.dirname(self.adb_key_path)
        print(key_dir)
        if not os.path.exists(key_dir):
            os.mkdir(key_dir)
        if not os.path.exists(self.adb_key_path):
            keygen(self.adb_key_path)
        # read the pub and priv key info
        with open(self.adb_key_path, 'r') as f:
            priv = f.read()
        with open(self.adb_key_path + '.pub', 'r') as f:
            pub = f.read()
        # return the rsa signer
        return PythonRSASigner(pub, priv)

    def adb_connect(self):
        adb_signer = self.get_adb_signer()
        print(f'{self.__class__.__name__}: Requesting connection to device')
        # Ensure device is initialized before connecting
        if not self.device:
            # Assuming AdbDeviceUsb() should be initialized if None
            self.device = AdbDeviceUsb()
        self.device.connect(rsa_keys=[adb_signer], auth_timeout_s=15.0)
        print(f'{self.__class__.__name__}: Connected')

    def get_device_ip(self):
        """
        Get the IP address of the connected Android device.

        Returns:
            str: The IP address of the device, or None if not available
        """
        # Skip if shutting down
        if self._is_shutting_down or not self.device or not self.executor:
            return None

        try:
            # Try to get WiFi IP address using ip command
            cmd_ip = ("ip addr show wlan0 | grep 'inet ' |"
                      " cut -d' ' -f6 | cut -d/ -f1")
            wifi_ip = self.executor.adb_exec(cmd_ip, timeout_s=3.0).strip()
            if wifi_ip:
                return wifi_ip

            # If that fails, try using ifconfig command
            cmd_ifconfig = "ifconfig wlan0 | grep 'inet addr'"
            ip_info = self.executor.adb_exec(cmd_ifconfig, timeout_s=3.0).strip()
            if ip_info and "inet addr:" in ip_info:
                # Extract IP from output like "inet addr:192.168.1.100  Bcast:192.168.1.255  Mask:255.255.255.0"
                return ip_info.split(':')[1].split()[0]

            # Try using the dumpsys command
            cmd_dumpsys = ("dumpsys connectivity | grep 'IPv4 address' |"
                           " cut -d' ' -f3")
            dumpsys_ip = self.executor.adb_exec(cmd_dumpsys, timeout_s=3.0).strip()
            if dumpsys_ip:
                return dumpsys_ip

            return None  # If no IP found
        except Exception as e:
            print(f"Error getting device IP: {e}")
            return None

    def track_errors(self):
        """
        Monitors target device for errors involving
        fatal signals or strained resource pressure."""
        if self._is_shutting_down or not self.device or not self.executor:
            return None
        # Parse for error signals - ANR, Native Crashes, SIGSEV, FATAL, WTF
        self._parse_fatals()
        # Monitor resource pressures - CPU, RAM, Memory Leakages,
        self._monitor_resources()
        return self

    def _parse_fatals(self):
        if self._is_shutting_down:
            return None
            
        try:
            cmd_logcat = (r"logcat -d | grep -i -E 'fatal signal|fatal exception|anr in|"
                          "sigsegv|sigabrt|sigbus|java\\.lang\\.(runtime|nullpointer|"
                          "illegalstate)exception' | grep -v 'phenotypemodule' |"
                          " grep -v 'com.google.android.gms' | grep -v 'gms\\.chimera' |"
                          " grep -i -v 'managedchannel'")
            logcat_dump = self.executor.adb_exec(cmd_logcat, timeout_s=3.0).strip()
            if logcat_dump:
                for item in logcat_dump.split('\n'):
                    self.tracker.append((datetime.datetime.now(), "Fatal Error", item))
            return self
        except Exception as e:
            print(f"Parse Fatals error: {e}")
            return None

    def _monitor_resources(self):
        if self._is_shutting_down:
            return None
            
        try:
            cmd_cpu = ("top -n 1 | grep -i 'cpu'")
            cpu_dump = self.executor.adb_exec(cmd_cpu, timeout_s=3.0).strip()
            
            # Parse CPU information safely
            cpu_usage = None
            if cpu_dump:
                try:
                    cpu_usage = float(cpu_dump.split(r'%idle')[0].split()[-1])
                except (IndexError, ValueError):
                    pass  # Failed to parse CPU usage

            cmd_mem = ("dumpsys meminfo | grep -i 'ram'")
            mem_dump = self.executor.adb_exec(cmd_mem, timeout_s=3.0).strip()
            mem_total = None
            mem_used = None
            
            # Parse memory information safely
            if mem_dump:
                for line in mem_dump.splitlines():
                    if "Total RAM" in line:
                        try:
                            clean_line = line.replace(':', '')
                            mem_total = float(clean_line.split()[2].replace(',', '').replace('K', ''))
                        except (IndexError, ValueError):
                            pass
                    if "Used RAM" in line:
                        try:
                            clean_line = line.replace(':', '')
                            mem_used = float(clean_line.split()[2].replace(',', '').replace('K', ''))
                        except (IndexError, ValueError):
                            pass
            
            # Calculate RAM usage percentage safely
            ram_usage_percentage = None
            if mem_total is not None and mem_used is not None and mem_total > 0:
                ram_usage_percentage = (mem_used / mem_total) * 100
            
            # Set baseline values if not already set
            spike_threshold = 1.2
            if self.base_cpu is None and cpu_usage is not None:
                self.base_cpu = cpu_usage
            if self.base_ram is None and ram_usage_percentage is not None:
                self.base_ram = ram_usage_percentage
            
            # Check for resource pressure only if we have valid data
            if (self.base_cpu is not None and cpu_usage is not None and 
                    self.base_ram is not None and ram_usage_percentage is not None):
                if (cpu_usage >= self.base_cpu * spike_threshold or 
                        ram_usage_percentage >= self.base_ram * spike_threshold):
                    self.tracker.append(
                        (datetime.datetime.now(), 
                         "Resource Pressure", 
                         f"CPU: {self.base_cpu:.1f} -> {cpu_usage:.1f}, "
                         f"RAM: {self.base_ram:.1f} -> {ram_usage_percentage:.1f}%")
                    )
            return self
        except Exception as e:
            print(f"Parse Fatals error: {e}")
            return None

    def run(self):
        # connect to the phone
        try:
            self.device = AdbDeviceUsb()
            self.adb_connect()
            # Correctly initialize ADB_Executor after successful connection
            self.executor = ADB_Executor(self.device)
        except Exception as e:
            print(f'{self.__class__.__name__}: Failed to connect to Android Device')
            print(f'{self.__class__.__name__}: {e}')
            # Clean up device if connection failed partially
            if self.device:
                try:
                    self.device.close()
                except Exception as close_e:
                    # Log error during cleanup if necessary
                    print(f"Error closing device during initial connection failure: {close_e}")
            return

        # run loop for thread
        self._stay_alive.set()
        self._is_shutting_down = False  # Reset shutdown flag
        check = datetime.datetime.now()
        try:
            while self._stay_alive.is_set():
                # Skip processing if shutting down
                if self._is_shutting_down:
                    break
                    
                current_time = datetime.datetime.now()

                if (current_time - check).total_seconds() >= 5:
                    self.track_errors()
                    check = current_time
                # Just sleep a short time to prevent CPU spinning
                # Consider adding a check for device availability here
                self._stay_alive.wait(0.1)
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            # self.kill() is called in finally block
        finally:
            # Ensure resources are cleaned up
            self.kill()  # Set flag to stop
            if self.device and not self._is_shutting_down:
                try:
                    print(f'{self.__class__.__name__}: Closing ADB connection.')
                    self.device.close()
                except Exception as e:
                    print(f"Error closing device on exit: {e}")

    def kill(self):
        # Prevent multiple kill attempts
        if self._is_shutting_down:
            print(f'{self.__class__.__name__}: Already shutting down, skipping duplicate cleanup')
            return
            
        print(f'{self.__class__.__name__}: Stopping thread.')  # Added for clarity
        self._is_shutting_down = True  # Mark as shutting down first
        self._stay_alive.clear()
        
        # Only try to close the device if it exists
        if hasattr(self, 'device') and self.device:
            try:
                self.device.close()
            except Exception as e:
                print(f"Error during device closure: {e}")


class ADB_Executor():
    def __init__(self, device):
        self.device = device
        # Removed the call to command_stream() that was blocking execution

    def adb_exec(self, cmd: str, timeout_s=5.0) -> str:
        """Execute an ADB command and return the result as a string."""
        # Add basic error handling and timeout
        try:
            return self.device.shell(cmd, timeout_s=timeout_s)  # Use configurable timeout
        except Exception as e:
            print(f"Error executing ADB command '{cmd}': {e}")
            return ""  # Return empty string on error

    def command_stream(self):
        """
        Interactive command stream for manual ADB command execution.
        This method should be called explicitly when needed, not automatically.
        """
        if not self.device:
            print("Device not available for command stream.")
            return

        print("Starting ADB command stream. Type 'exit' to quit.")
        while True:
            try:
                cmd = input("Enter command: ")
                if cmd.lower() == 'exit':  # Case-insensitive exit
                    break
                if cmd.lower() == 'get status':  # Case-insensitive status
                    self.get_phone_stats()
                elif cmd.strip():  # Only execute if command is not empty
                    print(self.adb_exec(cmd))
                # else: ignore empty input
            except (EOFError, KeyboardInterrupt):  # Handle Ctrl+D and Ctrl+C
                print("\nExiting command stream.")
                break
            except Exception as e:
                print(f"An error occurred in command stream: {e}")
                # Decide if you want to break or continue on other errors
                # break # Uncomment to exit loop on any error

        print("Exiting stream...")

    def get_phone_stats(self):
        """Get basic phone stats like battery information."""
        if not self.device:
            print("Device not available for get_phone_stats.")
            return

        battery_info = self.adb_exec('dumpsys battery', timeout_s=3.0)
        print("Battery info:")
        keywords = ["level", "scale", "status", "health", "present", "powered"]
        found_info = False
        if battery_info:  # Check if command returned anything
            for line in battery_info.splitlines():
                stripped_line = line.strip()
                # Check if line starts with any keyword
                if any(stripped_line.startswith(x) for x in keywords):
                    print(f"  {stripped_line}")
                    found_info = True
        if not found_info:
            print("  Relevant battery info not found or command failed.")
        # return  # Implicit None return is fine


class Correlator(threading.Thread):
    def __init__(self, p_tracker, a_tracker, window=2):
        super().__init__()
        self._stay_alive = threading.Event()
        self._is_shutting_down = False  # Flag to prevent multiple shutdowns
        self.packet_tracker = p_tracker
        self.anomaly_tracker = a_tracker
        self.match_window = window
        self.anomaly_ctr = 0
        self.daemon = True

    def correlate_trackers(self):
        """
        Compares queue of flagged anomalies/errors detected from device
        with log of packets sent in a certain timeframe to which is then
        forwarded to a log file of the error and potential damage-inducing packets"""
        if self._is_shutting_down:
            return
            
        if len(self.anomaly_tracker) > self.anomaly_ctr:
            anomaly_history = list(self.anomaly_tracker)[self.anomaly_ctr:]
            packet_history = list(self.packet_tracker)[-100:] if self.packet_tracker else []
            for idx, anomaly in enumerate(anomaly_history):
                log_idx = self.anomaly_ctr + idx
                try:
                    with open(f"anomaly{log_idx}.log", "w") as outfile:
                        outfile.write(f"Time Detected: {anomaly[0]}\n\n")
                        outfile.write(f"Type: {anomaly[1]}\n\n")
                        outfile.write(f"{anomaly[2]}\n\n\n")
                        
                        # Find packets within timeframe
                        window_start = anomaly[0] - datetime.timedelta(seconds=self.match_window / 2)
                        window_end = anomaly[0] + datetime.timedelta(seconds=self.match_window / 2)
                        
                        # Write packets in timeframe
                        matching_packets = False
                        for packet in packet_history:
                            if window_start <= packet[0] <= window_end:
                                outfile.write(f"{packet[1]} @ {packet[0]} -> {packet[2]}\n")
                                matching_packets = True
                                
                        # Note if no matching packets
                        if not matching_packets:
                            outfile.write("No packets found within the time window of this anomaly.\n")
                except Exception as e:
                    print(f"Error writing anomaly log {log_idx}: {e}")
                    
            self.anomaly_ctr = len(self.anomaly_tracker)
        else:
            pass

    def run(self):
        self._stay_alive.set()
        self._is_shutting_down = False  # Reset shutdown flag
        try:
            while self._stay_alive.is_set():
                if self._is_shutting_down:
                    break
                self.correlate_trackers()
                self._stay_alive.wait(self.match_window)
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            self.kill()

    def kill(self):
        if self._is_shutting_down:
            print(f'{self.__class__.__name__}: Already shutting down, skipping duplicate cleanup')
            return
            
        self._is_shutting_down = True
        print(f'{self.__class__.__name__}: Stopping thread.')
        self._stay_alive.clear()


# Optional: Add main execution block for testing
if __name__ == "__main__":
    print("Starting Target Monitor...")
    monitor = Target_Monitor()
    monitor.start()
    try:
        # Keep the main thread alive so the monitor can run
        # Use join to wait for the monitor thread to complete
        monitor.join()
    except KeyboardInterrupt:
        print("\nShutdown requested. Stopping monitor thread...")
        monitor.kill()
        # Wait for the thread to fully stop and clean up
        monitor.join()
    print("Target Monitor stopped.")