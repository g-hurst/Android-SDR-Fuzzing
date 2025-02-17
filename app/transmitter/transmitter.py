import threading
import subprocess as sp
import docker
import time

class Transmitter(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stay_alive  = threading.Event()

    def run(self):
        compose_proc = sp.Popen(['cd controller/docker/ && docker compose up'],
                                 shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        
        self._stay_alive.set()
        try:
            while self._stay_alive.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            print(f'Keyboard interrupt in {self.__class__.__name__}'.upper())
            self.kill()

        compose_proc.terminate()

    def get_containers(self):
        try:
            client = docker.from_env()
            return client.containers.list()
        except Exception as e:
            print(e)
            return None 

    def kill(self):
        self._stay_alive.clear()   
