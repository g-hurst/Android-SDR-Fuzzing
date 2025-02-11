#!/usr/bin/env python3

import time

from controller.target_monitor import Target_Monitor

def main():

    # create monitor thread and start it
    monitor = Target_Monitor()
    monitor.start()

    # just putting this here for now to fill later
    while True:
        try:
            time.sleep(0.1)
        except:
            print('keyboard interrupt in main')
            break

    # cleanup threads
    monitor.kill()

    print('App complete')

if __name__ == '__main__':
    main()
