import threading
import random
import datetime
from scapy.all import Ether, IP, TCP, UDP, Raw, sendp, hexdump, bytes_hex, raw, RandMAC


class Transmitter(threading.Thread):
    def __init__(self, tracker, target_mac='ff:ff:ff:ff:ff:ff', target_ip='192.168.1.1', interface='eth0', use_tcp=True):
        super().__init__()
        self._stay_alive = threading.Event()
        self.interface = interface
        self.target_mac = target_mac
        self.target_ip = target_ip
        self._n_packets_sent = 0
        self.use_tcp = use_tcp
        self.tracker = tracker

        # Initialize default packet structure
        self.reset_packet()

        # For storing raw packet override
        self.raw_packet = None

    def reset_packet(self, src_ip='192.168.1.100', src_mac=None, src_port=12345, dst_port=80):
        """Reset packet to default values"""
        # Create default Ethernet layer
        self.ether = Ether(
            src=RandMAC() if src_mac is None else src_mac,
            dst=self.target_mac
        )

        # Create default IP layer
        self.ip = IP(
            src=src_ip,
            dst=self.target_ip,
            ttl=64
        )

        # Create default TCP or UDP layer
        if self.use_tcp:
            self.transport = TCP(
                sport=src_port,
                dport=dst_port,
                flags='S'  # SYN flag
            )
        else:
            self.transport = UDP(
                sport=src_port,
                dport=dst_port
            )

        # Default payload
        self.payload = Raw(load=b'')
        self.raw_packet = None

    def build_packet(self):
        """Build the packet from layers or return raw packet if set"""
        if self.raw_packet is not None:
            return self.raw_packet
        return self.ether / self.ip / self.transport / self.payload

    def set_ether_field(self, field, value):
        """Set a specific field in the Ethernet layer"""
        setattr(self.ether, field, value)
        return self

    def set_ip_field(self, field, value):
        """Set a specific field in the IP layer"""
        setattr(self.ip, field, value)
        return self

    def set_transport_field(self, field, value):
        """Set a specific field in the TCP/UDP layer"""
        setattr(self.transport, field, value)
        return self

    def set_payload(self, payload):
        """Set the payload data"""
        if isinstance(payload, str):
            payload = payload.encode()
        self.payload = Raw(load=payload)
        return self

    def modify_raw_bytes(self, offset, new_bytes):
        """
        Modify specific bytes at given offset in the packet
        This allows direct bit/byte manipulation
        """
        # Get current packet as bytes
        packet_bytes = bytearray(raw(self.build_packet()))

        # Modify bytes at specified offset
        for i, b in enumerate(new_bytes):
            if offset + i < len(packet_bytes):
                packet_bytes[offset + i] = b

        # Store as raw packet override
        self.raw_packet = bytes(packet_bytes)
        return self

    def clear_raw_override(self):
        """Clear any raw packet override"""
        self.raw_packet = None
        return self

    def mutate_packet(self, mutation_rate=0.01):
        """
        Randomly mutate bits in the packet for fuzzing
        mutation_rate: percentage of bits to flip (0.01 = 1%)
        """
        packet_bytes = bytearray(raw(self.build_packet()))

        # Calculate how many bits to flip
        num_bits = len(packet_bytes) * 8
        bits_to_flip = max(1, int(num_bits * mutation_rate))

        # Flip random bits
        for _ in range(bits_to_flip):
            byte_idx = random.randint(0, len(packet_bytes) - 1)
            bit_idx = random.randint(0, 7)
            packet_bytes[byte_idx] ^= (1 << bit_idx)

        # Store as raw packet override
        self.raw_packet = bytes(packet_bytes)
        return self

    def get_packet_hex(self):
        """Get hexadecimal representation of current packet"""
        return bytes_hex(raw(self.build_packet())).decode()

    def print_packet(self):
        """Print the current packet in hexdump format"""
        hexdump(self.build_packet())
        return self

    def send_frame(self, payload=None):
        """Send the current packet"""
        temp_packet = self.build_packet()

        # If payload specified, temporarily set it
        if payload is not None:
            if isinstance(payload, str):
                payload = payload.encode()
            temp_packet = temp_packet.copy()
            if Raw in temp_packet:
                temp_packet[Raw].load = payload
            else:
                temp_packet = temp_packet / Raw(load=payload)

        # Send the packet
        sendp(temp_packet, iface=self.interface, verbose=False)
        self._n_packets_sent += 1
        return self

    def get_n_packets_sent(self):
        return self._n_packets_sent

    def set_target_mac(self, mac):
        self.target_mac = mac
        self.ether.dst = mac
        return self

    def set_target_ip(self, ip):
        self.target_ip = ip
        self.ip.dst = ip
        return self

    def track_packet(self):
        """Tracks packets being sent for further analysis"""
        self.tracker.append((datetime.datetime.now(), self.get_n_packets_sent(), self.get_packet_hex()))
        return self

    def run(self):
        self._stay_alive.set()
        try:
            while self._stay_alive.is_set():
                self.reset_packet()
                self.mutate_packet(0.01)
                self.track_packet()
                self.send_frame()
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            self.kill()

    def kill(self):
        self._stay_alive.clear()

