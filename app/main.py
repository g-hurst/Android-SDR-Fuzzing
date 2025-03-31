#!/usr/bin/env python3
import time
import sys
from target.target_monitor import Target_Monitor
from transmitter.transmitter import Transmitter
from cli.cli import CLI  # Import your CLI class from the cli directory


def main():
    # Check if we should run in interactive mode
    interactive_mode = "--interactive" in sys.argv or "-i" in sys.argv
    
    # create monitor thread and start it
    monitor = Target_Monitor()
    monitor.start()
    
    transmitter = Transmitter()
    transmitter.start()
    
    # Create CLI instance with reference to the target monitor
    cli = CLI(target_monitor=monitor)
    
    if interactive_mode:
        # Run the interactive CLI
        try:
            print("Starting interactive CLI mode. Use Ctrl+D to exit.")
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt. Shutting down...")
        finally:
            # cleanup threads
            monitor.kill()
            transmitter.kill()
            print('App complete')
            return
    
    # If not in interactive mode, just run the main loop
    print("Running in background mode. Press Ctrl+C to exit.")
    
    # Main loop
    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt. Shutting down...")
            break
        except Exception as e:
            print(f'Error in main loop: {e}')
            break
    
    # cleanup threads
    monitor.kill()
    transmitter.kill()
    print('App complete')


if __name__ == '__main__':
    main()