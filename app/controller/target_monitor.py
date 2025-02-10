import threading
import os

from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.adb_device import AdbDeviceUsb

class Target_Monitor(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stay_alive  = threading.Event()
        self.adb_key_path = '.android/adbkey' #TODO: this should probably be configurable
        self.device       = None

    def get_adb_signer(self) -> PythonRSASigner:
        # create dir and keys if needed
        key_dir = os.path.dirname(self.adb_key_path)
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
        self.device.connect(rsa_keys=[adb_signer], auth_timeout_s=3.0)

    def adb_exec(self, cmd:str) -> str:
        return self.device.shell(cmd)

    def run(self):
        # connect to the phone
        try:
            self.device = AdbDeviceUsb()
            self.adb_connect()
        except Exception as e:
            print(f'{self.__class__.__name__}: Failed to connect to Android Device')
            print(f'{self.__class__.__name__}: {e}')
            return 

        # run loop for thread
        self._stay_alive.set()
        try:
            while self._stay_alive.is_set():
                pass
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            self.kill()

    def kill(self):
        self._stay_alive.clear()   
