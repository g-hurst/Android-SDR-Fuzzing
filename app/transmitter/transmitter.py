import threading
import random
import string
from scapy.layers.dot11 import RadioTap, Dot11, LLC, SNAP
from scapy.all import sendp, RandMAC, Raw


class Transmitter(threading.Thread):
    def __init__(self, target_mac='ff:ff:ff:ff:ff:ff', interface='wlp0s20f3'):
        super().__init__()
        self._stay_alive = threading.Event()
        self.interface = interface
        self.target_mac = target_mac
        self._n_packets_sent = 0

    def send_frame(self, payload):
        frame = RadioTap() / Dot11(
            type=2,
            subtype=0,
            addr1=self.target_mac,
            addr2=RandMAC(),
            addr3=self.target_mac
        ) / LLC() / SNAP() / Raw(load=payload)
        sendp(frame, iface=self.interface, verbose=False)

    def get_n_packets_sent(self):
        return self._n_packets_sent

    def set_target_mac(self, mac):
        self.target_mac = mac

    def run(self):
        self._stay_alive.set()
        try:
            while self._stay_alive.is_set():
                data_sz = 50
                data = ''.join(random.choices(string.printable, k=data_sz)).encode()
                self.send_frame(data)
                self._n_packets_sent += 1
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            self.kill()

    def kill(self):
        self._stay_alive.clear()
