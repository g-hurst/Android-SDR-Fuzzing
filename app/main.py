#!/usr/bin/env python3
import time
import argparse
import configparser
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
    
    # Flag to prevent multiple shutdowns
    shutdown_initiated = False

    # read the configuration file
    try:
        config = configparser.ConfigParser()
        config.read(args.config)
    except Exception as e:
        print(f'error parsing config: {e}')
        # Create empty config if parsing fails
        config = configparser.ConfigParser()

    # Initialize trackers with size limits
    packet_tracker = deque(maxlen=1000)
    anomaly_tracker = deque(maxlen=500)

    # Initialize components
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

    # Initialize transmitter if not skipped
    if not args.skip_transmitter:
        try:
            from transmitter.transmitter import Transmitter
            # Use safe config access with fallback
            interface = 'eth0'  # Default
            try:
                interface = config['TRANSMITTER']['NetDevice']
            except (KeyError, TypeError):
                print("Warning: Using default interface 'eth0'. Add to config.ini if needed.")
                
            transmitter = Transmitter(tracker=packet_tracker,
                                      interface=interface)
            transmitter.start()
            print("Transmitter started")
        except Exception as e:
            print(f"Warning: Could not start transmitter: {e}")
            transmitter = None

    # Create correlator thread and start it
    try:
        correlator = Correlator(p_tracker=packet_tracker, a_tracker=anomaly_tracker)
        correlator.start()
        print("Correlator started")
    except Exception as e:
        print(f"Warning: Could not start correlator: {e}")
        correlator = None

    # Create CLI instance with references to monitor and trackers
    cli = CLI(target_monitor=monitor,
              packet_tracker=packet_tracker,
              anomaly_tracker=anomaly_tracker)
              
    # Define safe shutdown function
    def shutdown_app():
        nonlocal shutdown_initiated
        if shutdown_initiated:
            print("Shutdown already in progress...")
            return
        
        shutdown_initiated = True
        print("\nInitiating shutdown sequence...")
        cleanup_threads(monitor, transmitter, correlator)
        print('App complete')

    if args.interactive:
        # Run the interactive CLI
        try:
            print("Starting interactive CLI mode. Use Ctrl+D to exit.")
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt. Shutting down...")
        finally:
            # Cleanup threads
            shutdown_app()
            return

    # If not in interactive mode, just run the main loop
    print("Running in background mode. Press Ctrl+C to exit.")

    # Main loop
    try:
        while not shutdown_initiated:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
    except Exception as e:
        print(f'Error in main loop: {e}')
    finally:
        shutdown_app()


def cleanup_threads(monitor, transmitter, correlator):
    """Safely cleanup all threads."""
    # Cleanup the monitor
    if monitor:
        try:
            print("Stopping monitor thread...")
            monitor.kill()
            # Give time for the monitor thread to clean up
            time.sleep(0.5)
        except AttributeError:
            # Handle the case where device is None
            print("Note: Monitor device was not fully initialized")
        except Exception as e:
            print(f"Warning: Error during monitor cleanup: {e}")

    # Cleanup the transmitter
    if transmitter:
        try:
            print("Stopping transmitter thread...")
            transmitter.kill()
            # Give thread time to clean up
            time.sleep(0.2)
        except Exception as e:
            print(f"Warning: Error during transmitter cleanup: {e}")

    # Cleanup the correlator
    if correlator:
        try:
            print("Stopping correlator thread...")
            correlator.kill()
            # Give thread time to clean up
            time.sleep(0.2)
        except Exception as e:
            print(f"Warning: Error during correlator cleanup: {e}")


if __name__ == '__main__':
    main()