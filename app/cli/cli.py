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