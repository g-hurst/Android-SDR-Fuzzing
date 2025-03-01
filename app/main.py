#!/usr/bin/env python3

import time

from target.target_monitor import Target_Monitor
from transmitter.transmitter import Transmitter


def main():

    # create monitor thread and start it
    monitor = Target_Monitor()
    monitor.start()

    transmitter = Transmitter()
    transmitter.start()

    # just putting this here for now to fill later
    while True:
        try:
            time.sleep(0.1)
        except Exception as e:
            print(f'Error in main loop: {e}')
            break

    # cleanup threads
    monitor.kill()
    transmitter.kill()

    print('App complete')


if __name__ == '__main__':
    main()
