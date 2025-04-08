#!/usr/bin/env python3
"""
Target Monitor Module
-------------------
Provides monitoring capabilities for the Android target device.
"""

import threading
import os
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.adb_device import AdbDeviceUsb


class Target_Monitor(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stay_alive = threading.Event()
        self.adb_key_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '.android/adbkey'
        )  # TODO: this should probably be configurable
        self.device = None
        self.executor = None

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
            wifi_ip = self.executor.adb_exec("ip addr show wlan0 | grep 'inet ' | cut -d' ' -f6 | cut -d/ -f1").strip()
            if wifi_ip:
                return wifi_ip
                
            # If that fails, try using ifconfig command
            ip_info = self.executor.adb_exec("ifconfig wlan0 | grep 'inet addr'").strip()
            if ip_info and "inet addr:" in ip_info:
                # Extract IP from output like "inet addr:192.168.1.100  Bcast:192.168.1.255  Mask:255.255.255.0"
                return ip_info.split(':')[1].split()[0]
                
            # Try using the dumpsys command
            dumpsys_ip = self.executor.adb_exec("dumpsys connectivity | grep 'IPv4 address' | cut -d' ' -f3").strip()
            if dumpsys_ip:
                return dumpsys_ip
                
            return None  # If no IP found
        except Exception as e:
            print(f"Error getting device IP: {e}")
            return None

    def run(self):
        # connect to the phone
        try:
            self.device = AdbDeviceUsb()
            self.adb_connect()
            self.executor = ADB_Executor(self.device)
        except Exception as e:
            print(f'{self.__class__.__name__}: Failed to connect to Android Device')
            print(f'{self.__class__.__name__}: {e}')
            return

        # run loop for thread
        self._stay_alive.set()
        try:
            while self._stay_alive.is_set():
                # Just sleep a short time to prevent CPU spinning
                self._stay_alive.wait(0.1)
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            self.kill()

    def kill(self):
        self._stay_alive.clear()


class ADB_Executor():
    def __init__(self, device):
        self.device = device
        # Removed the call to command_stream() that was blocking execution

    def adb_exec(self, cmd: str) -> str:
        """Execute an ADB command and return the result as a string."""
        return self.device.shell(cmd)

    def command_stream(self):
        """
        Interactive command stream for manual ADB command execution.
        This method should be called explicitly when needed, not automatically.
        """
        print("Starting ADB command stream. Type 'exit' to quit.")
        while True:
            cmd = input("Enter command: ")
            if cmd == 'exit':
                break
            if cmd == 'get status':
                self.get_phone_stats()
            else:
                print(self.adb_exec(cmd))
        print("Exiting stream...")

    def get_phone_stats(self):
        """Get basic phone stats like battery information."""
        battery_info = self.adb_exec('dumpsys battery')
        print("Battery info:")
        for line in battery_info.splitlines():
            if any(x in line for x in ["level", "scale", "status", "health", "present", "powered"]):
                print(f"  {line.strip()}")
        return