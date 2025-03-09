import threading
import time


class Transmitter(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stay_alive = threading.Event()

    def run(self):
        self._stay_alive.set()
        try:
            while self._stay_alive.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            self.kill()

    def kill(self):
        self._stay_alive.clear()
