#!/usr/bin/env python3
"""
Target Monitor Module
-------------------
Provides monitoring capabilities for the Android target device.
"""

import threading
import os
import datetime
import random
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.adb_device import AdbDeviceUsb


class Target_Monitor(threading.Thread):
    def __init__(self, tracker):
        super().__init__()
        self._stay_alive = threading.Event()
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
        if not self.device or not self.executor:
            return None

        try:
            # Try to get WiFi IP address using ip command
            cmd_ip = ("ip addr show wlan0 | grep 'inet ' |"
                      " cut -d' ' -f6 | cut -d/ -f1")
            wifi_ip = self.executor.adb_exec(cmd_ip).strip()
            if wifi_ip:
                return wifi_ip

            # If that fails, try using ifconfig command
            cmd_ifconfig = "ifconfig wlan0 | grep 'inet addr'"
            ip_info = self.executor.adb_exec(cmd_ifconfig).strip()
            if ip_info and "inet addr:" in ip_info:
                # Extract IP from output like "inet addr:192.168.1.100  Bcast:192.168.1.255  Mask:255.255.255.0"
                return ip_info.split(':')[1].split()[0]

            # Try using the dumpsys command
            cmd_dumpsys = ("dumpsys connectivity | grep 'IPv4 address' |"
                           " cut -d' ' -f3")
            dumpsys_ip = self.executor.adb_exec(cmd_dumpsys).strip()
            if dumpsys_ip:
                return dumpsys_ip

            return None  # If no IP found
        except Exception as e:
            print(f"Error getting device IP: {e}")
            return None
    
    def track_errors(self):
        if not self.device or not self.executor:
            return None
        # Parse for error signals - ANR, Native Crashes, SIGSEV, FATAL, WTF
        self._parse_fatals()
        # Monitor resource pressures - CPU, RAM, Memory Leakages,
        self._monitor_resources()
        return self
    
    def _parse_fatals(self):
        try:
            cmd_logcat = ("logcat -d | grep -i -E 'fatal signal|fatal exception|anr in|"
                          "sigsegv|sigabrt|sigbus|java\.lang\.(runtime|nullpointer|"
                          "illegalstate)exception' | grep -v 'phenotypemodule' |"
                          " grep -v 'com.google.android.gms' | grep -v 'gms\.chimera' |"
                          " grep -i -v 'managedchannel'")
            logcat_dump = self.executor.adb_exec(cmd_logcat).strip()
            if logcat_dump:
                for item in logcat_dump.split('\n'):
                    self.tracker.append((datetime.datetime.now(), "Fatal Error", item))
            return self
        except Exception as e:
            print(f"Parse Fatals error: {e}")
            return None
        
    def _monitor_resources(self):
        try:
            cmd_cpu = ("top -n 1 | grep -i 'cpu'")
            cpu_dump = self.executor.adb_exec(cmd_cpu).strip()
            cpu_usage = float(cpu_dump.split(f'%idle')[0].split()[-1])
            
            cmd_mem = ("dumpsys meminfo | grep -i 'ram'")
            mem_dump = self.executor.adb_exec(cmd_mem).strip()
            mem_total = None
            mem_used = None
            for line in mem_dump.splitlines():
                if "Total RAM" in line:
                    clean_line = line.replace(':', '')
                    mem_total = float(clean_line.split()[2].replace(',', '').replace('K', ''))
                if "Used RAM" in line:
                    clean_line = line.replace(':', '')
                    mem_used = float(clean_line.split()[2].replace(',', '').replace('K', ''))
            if mem_total and mem_used:
                ram_usage_percentage = (mem_used / mem_total) * 100
            else:
                ram_usage_percentage = None
                
            spike_threshold = 1.2
            if not self.base_cpu and not self.base_ram:
                self.base_cpu = cpu_usage
                self.base_ram = ram_usage_percentage
            if self.base_cpu and self.base_ram:
                if cpu_usage >= self.base_cpu * spike_threshold or ram_usage_percentage >= self.base_ram * spike_threshold:
                    self.tracker.append((datetime.datetime.now(), "Resource Pressure", f"CPU: {self.base_cpu} -> {cpu_usage}, RAM: {self.base_ram} -> {ram_usage_percentage}"))
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
        check = datetime.datetime.now()
        try:
            while self._stay_alive.is_set():
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
            if self.device:
                try:
                    print(f'{self.__class__.__name__}: Closing ADB connection.')
                    self.device.close()
                except Exception as e:
                    print(f"Error closing device on exit: {e}")

    def kill(self):
        print(f'{self.__class__.__name__}: Stopping thread.')  # Added for clarity
        self.device.close()
        self._stay_alive.clear()


class ADB_Executor():
    def __init__(self, device):
        self.device = device
        # Removed the call to command_stream() that was blocking execution

    def adb_exec(self, cmd: str) -> str:
        """Execute an ADB command and return the result as a string."""
        # Add basic error handling and timeout
        try:
            return self.device.shell(cmd, timeout_s=10.0)  # Added timeout
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

        battery_info = self.adb_exec('dumpsys battery')
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
        self.packet_tracker = p_tracker
        self.anomaly_tracker = a_tracker
        self.match_window = window
        self.anomaly_ctr = 0
        self.daemon = True

    def correlate_trackers(self):
        if len(self.anomaly_tracker) > self.anomaly_ctr:
            anomaly_history = list(self.anomaly_tracker)[self.anomaly_ctr:]
            packet_history = list(self.packet_tracker)[-100:]
            for idx, anomaly in enumerate(anomaly_history):
                log_idx = self.anomaly_ctr + idx
                with open(f"anomaly{log_idx}.log","w") as outfile:
                    print(anomaly)
                    outfile.write(f"Time Detected: {anomaly[0]}\n\n")
                    outfile.write(f"Type: {anomaly[1]}\n\n")
                    outfile.write(f"{anomaly[2]}\n\n\n")
                    for packet in packet_history:
                        if (anomaly[0] - datetime.timedelta(seconds= self.match_window / 2)) <= \
                        packet[0] <= (anomaly[0] + datetime.timedelta(seconds= self.match_window / 2)):
                            outfile.write(f"{packet[1]} @ {packet[0]} -> {packet[2]}\n")
            self.anomaly_ctr = len(self.anomaly_tracker)        
        else:
            pass

    def run(self):
        self._stay_alive.set()
        try:
            while self._stay_alive.is_set():
                self.correlate_trackers()
                self._stay_alive.wait(self.match_window)
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            self.kill()

    def kill(self):
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