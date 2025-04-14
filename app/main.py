#!/usr/bin/env python3
import time
import sys
import argparse
from target.target_monitor import Target_Monitor
from cli.cli import CLI  # Import your CLI class from the cli directory

def parse_argv():
    parser = argparse.ArgumentParser(description="Run the CLI application with optional modes.")
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run the CLI in interactive mode"
    )
    parser.add_argument(
        "--skip-transmitter",
        action="store_true",
        help="Skip starting the transmitter"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        metavar="FILE",
        help="Path to the configuration file"
    )

    return parser.parse_args()


def main():
    args = parse_argv()

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
    if not args.skip_transmitter:
        try:
            from transmitter.transmitter import Transmitter
            transmitter = Transmitter()
            transmitter.start()
            print("Transmitter started")
        except Exception as e:
            print(f"Warning: Could not start transmitter: {e}")

    # Create CLI instance with reference to the target monitor
    cli = CLI(target_monitor=monitor)

    if args.interactive:
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
