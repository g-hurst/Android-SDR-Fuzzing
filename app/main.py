#!/usr/bin/env python3
import time
import sys
from target.target_monitor import Target_Monitor
from cli.cli import CLI  # Import your CLI class from the cli directory


def main():
    # Check if we should run in interactive mode
    interactive_mode = "--interactive" in sys.argv or "-i" in sys.argv
    skip_transmitter = "--skip-transmitter" in sys.argv

    # Create monitor thread and start it
    try:
        monitor = Target_Monitor()
        monitor.start()
        print("Target monitor started")
    except Exception as e:
        print(f"Warning: Could not start monitor: {e}")
        monitor = None

    # Initialize transmitter if not skipped
    transmitter = None
    if not skip_transmitter:
        try:
            from transmitter.transmitter import Transmitter
            transmitter = Transmitter()
            transmitter.start()
            print("Transmitter started")
        except Exception as e:
            print(f"Warning: Could not start transmitter: {e}")

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
            # Cleanup threads
            if monitor:
                monitor.kill()
            if transmitter:
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

    # Cleanup threads
    if monitor:
        monitor.kill()
    if transmitter:
        transmitter.kill()
    print('App complete')


if __name__ == '__main__':
    main()