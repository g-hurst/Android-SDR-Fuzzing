#!/usr/bin/env python3
import time
import threading
from controller.target_monitor import Target_Monitor
from transmitter.transmitter import Transmitter
from cli.cli import CLI  # Import your CLI class from the cli directory


def main():
    # create monitor thread and start it
    monitor = Target_Monitor()
    monitor.start()

    transmitter = Transmitter()
    transmitter.start()

    # Create CLI instance
    cli = CLI()

    # Create a thread for container status monitoring
    def show_container_status():
        while True:
            print("\n===== Container Status =====")
            cli.print_container_list(filter_prefix="srsran")
            time.sleep(10)  # Update every 10 seconds

    # Start container status monitoring in a separate thread
    status_thread = threading.Thread(target=show_container_status)
    status_thread.daemon = True  # This ensures the thread will exit when main thread exits
    status_thread.start()

    # Main loop
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
    