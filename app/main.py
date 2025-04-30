#!/usr/bin/env python3
import time
import argparse
import configparser
import sys
from collections import deque
from target.target_monitor import Target_Monitor, Correlator
from cli.cli import CLI


def parse_argv():
    '''
    This function is just a wrapper for the argparse setup for our cli tool.
    All of the options for argparse should be added here.
    '''
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
        default='config.ini',
        help="Path to the configuration file"
    )

    return parser.parse_args()


def main():
    args = parse_argv()

    # read the configuration file
    try:
        config = configparser.ConfigParser()
        config.read(args.config)
    except Exception as e:
        print(f'error parsing config: {e}')

    # Initialize trackers
    packet_tracker = deque()
    anomaly_tracker = deque()

    # Initialize thread objects
    monitor = None
    transmitter = None
    correlator = None

    # Create monitor thread and start it
    try:
        monitor = Target_Monitor(tracker=anomaly_tracker)
        monitor.start()
        print("Target monitor started")
    except Exception as e:
        print(f"Warning: Could not start monitor: {e}")
        monitor = None
        cleanup_threads(monitor, transmitter, correlator)
        sys.exit(1)

    # Initialize transmitter if not skipped
    if not args.skip_transmitter:
        try:
            from transmitter.transmitter import Transmitter
            transmitter = Transmitter(tracker=packet_tracker,
                                      interface=config['TRANSMITTER']['NetDevice'])
            transmitter.start()
            print("Transmitter started")
        except Exception as e:
            print(f"Warning: Could not start transmitter: {e}")
            transmitter = None
            cleanup_threads(monitor, transmitter, correlator)
            sys.exit(1)

    # Create correlator thread and start it
    try:
        correlator = Correlator(p_tracker=packet_tracker, a_tracker=anomaly_tracker,
                                logdir=config['LOGGING']['Outdir'])
        correlator.start()
        print("Correlator started")
    except Exception as e:
        print(f"Warning: Could not start correlator: {e}")
        correlator = None
        cleanup_threads(monitor, transmitter, correlator)
        sys.exit(1)

    # Create CLI instance with references to monitor and trackers
    cli = CLI(target_monitor=monitor,
              packet_tracker=packet_tracker,
              anomaly_tracker=anomaly_tracker)

    if args.interactive:
        # Run the interactive CLI
        try:
            print("Starting interactive CLI mode. Use Ctrl+D to exit.")
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt. Shutting down...")
        finally:
            # Cleanup threads
            cleanup_threads(monitor, transmitter, correlator)
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
    cleanup_threads(monitor, transmitter, correlator)
    print('App complete')


def cleanup_threads(monitor, transmitter, correlator):
    """Safely cleanup all threads."""
    # Cleanup the monitor
    if monitor:
        try:
            monitor.kill()
        except AttributeError:
            # Handle the case where device is None
            print("Note: Monitor device was not fully initialized")
        except Exception as e:
            print(f"Warning: Error during monitor cleanup: {e}")

    # Cleanup the transmitter
    if transmitter:
        try:
            transmitter.kill()
        except Exception as e:
            print(f"Warning: Error during transmitter cleanup: {e}")

    # Cleanup the correlator
    if correlator:
        try:
            correlator.kill()
        except Exception as e:
            print(f"Warning: Error during correlator cleanup: {e}")


if __name__ == '__main__':
    main()